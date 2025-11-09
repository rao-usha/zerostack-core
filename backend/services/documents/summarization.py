"""AI-powered document summarization using OpenAI."""
import os
from typing import Optional
from openai import OpenAI
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """Summarize documents using OpenAI."""
    
    def __init__(self):
        api_key = settings.openai_api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key.startswith('dummy') or api_key.startswith('your-'):
            logger.warning("OpenAI API key not configured or is dummy. Summarization will be disabled.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def summarize(
        self,
        text: str,
        max_length: int = 500,
        style: str = "concise"
    ) -> Optional[str]:
        """
        Summarize text using OpenAI.
        
        Args:
            text: Text to summarize
            max_length: Target length for summary
            style: "concise", "detailed", or "bullet_points"
        
        Returns:
            Summary text or None if summarization fails
        """
        if not self.client:
            return None
        
        if not text or len(text.strip()) < 50:
            return None
        
        # Truncate if too long (limit tokens)
        max_chars = 3000  # ~750 tokens, leaving room for response
        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"
        
        style_prompt = {
            "concise": "Provide a concise summary in 2-3 sentences.",
            "detailed": "Provide a detailed summary covering key points.",
            "bullet_points": "Provide a summary as bullet points."
        }.get(style, "Provide a concise summary.")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes documents clearly and accurately."
                    },
                    {
                        "role": "user",
                        "content": f"{style_prompt}\n\nDocument text:\n\n{text}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            return summary.strip() if summary else None
            
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return None
    
    def summarize_multiple(self, texts: list[str], combine: bool = True) -> Optional[str]:
        """
        Summarize multiple text snippets.
        
        Args:
            texts: List of text snippets to summarize
            combine: If True, combine into one summary; if False, summarize each separately
        
        Returns:
            Combined or individual summaries
        """
        if not self.client or not texts:
            return None
        
        if combine:
            combined = "\n\n---\n\n".join(texts[:5])  # Limit to 5 docs
            return self.summarize(combined, style="detailed")
        else:
            summaries = []
            for text in texts[:5]:
                summary = self.summarize(text, style="concise")
                if summary:
                    summaries.append(f"• {summary}")
            return "\n".join(summaries) if summaries else None

