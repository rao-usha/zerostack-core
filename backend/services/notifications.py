"""Notification service for alerts and schedule notifications.

Supports:
- Email (SMTP)
- Slack (webhook)
- Generic webhooks
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)

# Try to import aiohttp for async HTTP calls
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not installed, webhook notifications will fail")

# Try to import email libraries
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    HAS_EMAIL = True
except ImportError:
    HAS_EMAIL = False
    logger.warning("email libraries not available")


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    channel: str
    success: bool
    message: str
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'channel': self.channel,
            'success': self.success,
            'message': self.message,
            'error': self.error
        }


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        self._settings_cache: Dict[str, dict] = {}
    
    async def send(
        self,
        channel: NotificationChannel,
        subject: str,
        body: str,
        metadata: dict = None
    ) -> NotificationResult:
        """
        Send a notification via the specified channel.
        
        Args:
            channel: The notification channel
            subject: Notification subject/title
            body: Notification body
            metadata: Additional data (e.g., recipient email, slack channel)
        """
        config = self._get_channel_config(channel.value)
        
        if not config or not config.get('is_enabled', False):
            return NotificationResult(
                channel=channel.value,
                success=False,
                message="Channel not configured or disabled"
            )
        
        try:
            if channel == NotificationChannel.EMAIL:
                return await self._send_email(config, subject, body, metadata)
            elif channel == NotificationChannel.SLACK:
                return await self._send_slack(config, subject, body, metadata)
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(config, subject, body, metadata)
            else:
                return NotificationResult(
                    channel=channel.value,
                    success=False,
                    message=f"Unknown channel: {channel}"
                )
        except Exception as e:
            logger.error(f"Failed to send {channel.value} notification: {e}")
            return NotificationResult(
                channel=channel.value,
                success=False,
                message="Failed to send notification",
                error=str(e)
            )
    
    async def send_drift_alert(
        self,
        check_name: str,
        metric: str,
        baseline: float,
        current: float,
        change_percent: float,
        severity: str,
        channels: List[str] = None
    ) -> List[NotificationResult]:
        """Send a drift alert notification to all configured channels."""
        subject = f"🚨 Drift Alert: {check_name}"
        
        body = f"""
Drift detected in metric '{metric}'

**Check:** {check_name}
**Severity:** {severity.upper()}

**Values:**
- Baseline: {baseline:.4f}
- Current: {current:.4f}
- Change: {change_percent:+.2f}%

Please review and acknowledge this alert.
"""
        
        # Use provided channels or all enabled channels
        if channels is None:
            channels = self._get_enabled_channels()
        
        results = []
        for channel_name in channels:
            try:
                channel = NotificationChannel(channel_name)
                result = await self.send(channel, subject, body)
                results.append(result)
            except ValueError:
                logger.warning(f"Unknown notification channel: {channel_name}")
        
        return results
    
    async def send_schedule_notification(
        self,
        schedule_name: str,
        status: str,  # 'success', 'failure', 'reused'
        run_id: str = None,
        error_message: str = None,
        channels: List[str] = None
    ) -> List[NotificationResult]:
        """Send a schedule execution notification."""
        emoji = {
            'success': '✅',
            'failure': '❌',
            'reused': '♻️'
        }.get(status, '📋')
        
        subject = f"{emoji} Schedule '{schedule_name}': {status.upper()}"
        
        if status == 'success':
            body = f"Schedule '{schedule_name}' completed successfully.\nRun ID: {run_id}"
        elif status == 'failure':
            body = f"Schedule '{schedule_name}' failed.\nError: {error_message or 'Unknown error'}"
        elif status == 'reused':
            body = f"Schedule '{schedule_name}' reused existing run.\nReused Run ID: {run_id}"
        else:
            body = f"Schedule '{schedule_name}' status: {status}"
        
        if channels is None:
            channels = self._get_enabled_channels()
        
        results = []
        for channel_name in channels:
            try:
                channel = NotificationChannel(channel_name)
                result = await self.send(channel, subject, body)
                results.append(result)
            except ValueError:
                pass
        
        return results
    
    async def _send_email(
        self,
        config: dict,
        subject: str,
        body: str,
        metadata: dict = None
    ) -> NotificationResult:
        """Send email notification."""
        if not HAS_EMAIL:
            return NotificationResult(
                channel='email',
                success=False,
                message="Email libraries not installed"
            )
        
        smtp_config = config.get('config', {})
        smtp_host = smtp_config.get('smtp_host', 'localhost')
        smtp_port = smtp_config.get('smtp_port', 587)
        smtp_user = smtp_config.get('smtp_user')
        smtp_password = smtp_config.get('smtp_password')
        from_email = smtp_config.get('from_email', 'nex@localhost')
        to_emails = smtp_config.get('to_emails', [])
        
        if metadata and 'to' in metadata:
            to_emails = [metadata['to']] if isinstance(metadata['to'], str) else metadata['to']
        
        if not to_emails:
            return NotificationResult(
                channel='email',
                success=False,
                message="No recipients configured"
            )
        
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._send_smtp(
                smtp_host, smtp_port, smtp_user, smtp_password, from_email, to_emails, msg
            ))
            
            return NotificationResult(
                channel='email',
                success=True,
                message=f"Email sent to {len(to_emails)} recipient(s)"
            )
        except Exception as e:
            return NotificationResult(
                channel='email',
                success=False,
                message="Failed to send email",
                error=str(e)
            )
    
    def _send_smtp(self, host, port, user, password, from_email, to_emails, msg):
        """Synchronous SMTP send."""
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_email, to_emails, msg.as_string())
    
    async def _send_slack(
        self,
        config: dict,
        subject: str,
        body: str,
        metadata: dict = None
    ) -> NotificationResult:
        """Send Slack notification via webhook."""
        if not HAS_AIOHTTP:
            return NotificationResult(
                channel='slack',
                success=False,
                message="aiohttp not installed"
            )
        
        slack_config = config.get('config', {})
        webhook_url = slack_config.get('webhook_url')
        channel = slack_config.get('channel', '#alerts')
        
        if not webhook_url:
            return NotificationResult(
                channel='slack',
                success=False,
                message="Slack webhook URL not configured"
            )
        
        payload = {
            'channel': channel,
            'username': 'NEX Bot',
            'icon_emoji': ':robot_face:',
            'attachments': [
                {
                    'title': subject,
                    'text': body,
                    'color': '#ff0000' if 'alert' in subject.lower() else '#36a64f'
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return NotificationResult(
                            channel='slack',
                            success=True,
                            message="Slack message sent"
                        )
                    else:
                        text = await response.text()
                        return NotificationResult(
                            channel='slack',
                            success=False,
                            message="Slack API error",
                            error=text
                        )
        except Exception as e:
            return NotificationResult(
                channel='slack',
                success=False,
                message="Failed to send Slack message",
                error=str(e)
            )
    
    async def _send_webhook(
        self,
        config: dict,
        subject: str,
        body: str,
        metadata: dict = None
    ) -> NotificationResult:
        """Send generic webhook notification."""
        if not HAS_AIOHTTP:
            return NotificationResult(
                channel='webhook',
                success=False,
                message="aiohttp not installed"
            )
        
        webhook_config = config.get('config', {})
        webhook_url = webhook_config.get('url')
        headers = webhook_config.get('headers', {})
        
        if not webhook_url:
            return NotificationResult(
                channel='webhook',
                success=False,
                message="Webhook URL not configured"
            )
        
        payload = {
            'subject': subject,
            'body': body,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status in [200, 201, 202]:
                        return NotificationResult(
                            channel='webhook',
                            success=True,
                            message=f"Webhook delivered (status {response.status})"
                        )
                    else:
                        text = await response.text()
                        return NotificationResult(
                            channel='webhook',
                            success=False,
                            message=f"Webhook failed (status {response.status})",
                            error=text
                        )
        except Exception as e:
            return NotificationResult(
                channel='webhook',
                success=False,
                message="Failed to send webhook",
                error=str(e)
            )
    
    def _get_channel_config(self, channel: str) -> Optional[dict]:
        """Get configuration for a notification channel."""
        if channel in self._settings_cache:
            return self._settings_cache[channel]
        
        query = "SELECT * FROM notification_settings WHERE channel = :channel"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'channel': channel}).fetchone()
            if result:
                config = dict(result._mapping)
                self._settings_cache[channel] = config
                return config
        
        return None
    
    def _get_enabled_channels(self) -> List[str]:
        """Get all enabled notification channels."""
        query = "SELECT channel FROM notification_settings WHERE is_enabled = true"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return [row[0] for row in result]
    
    def configure_channel(
        self,
        channel: NotificationChannel,
        is_enabled: bool,
        config: dict
    ):
        """Configure a notification channel."""
        query = """
            INSERT INTO notification_settings (channel, is_enabled, config)
            VALUES (:channel, :enabled, :config)
            ON CONFLICT (channel) DO UPDATE SET
                is_enabled = :enabled,
                config = :config,
                updated_at = NOW()
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'channel': channel.value,
                'enabled': is_enabled,
                'config': json.dumps(config)
            })
        
        # Clear cache
        if channel.value in self._settings_cache:
            del self._settings_cache[channel.value]
        
        logger.info(f"Configured {channel.value} notifications: enabled={is_enabled}")


# Import datetime for webhook payload
from datetime import datetime


# Singleton instance
_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get singleton notification service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = NotificationService()
    return _service_instance
