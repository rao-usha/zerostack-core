"""SSH-based compute adapter for remote GPU execution."""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from core.config import settings
from .adapter import ComputeAdapter, JobSubmission, JobStatus, JobState, ComputeError

logger = logging.getLogger(__name__)


class SSHComputeAdapter(ComputeAdapter):
    """
    Execute jobs on remote GPU VM via SSH and Docker.
    
    Requirements on remote host:
    - Docker installed with nvidia-container-toolkit
    - SSH access with key-based auth
    - Network access to MinIO/S3 for data transfer
    """
    
    def __init__(self):
        """Initialize SSH adapter with settings."""
        self.host = settings.ssh_host
        self.port = settings.ssh_port
        self.user = settings.ssh_user
        self.key_path = settings.ssh_key_path
        self.docker_runtime = settings.ssh_docker_runtime
        
        if not self.host:
            logger.warning("SSH_HOST not configured - SSH adapter will fail")
    
    @property
    def adapter_type(self) -> str:
        return "ssh"
    
    def _build_ssh_cmd(self, remote_cmd: str) -> list[str]:
        """Build SSH command with proper options."""
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
        if self.key_path:
            cmd.extend(["-i", self.key_path])
        if self.port != 22:
            cmd.extend(["-p", str(self.port)])
        cmd.append(f"{self.user}@{self.host}")
        cmd.append(remote_cmd)
        return cmd
    
    async def _run_ssh(self, remote_cmd: str) -> tuple[int, str, str]:
        """Execute command on remote host via SSH."""
        cmd = self._build_ssh_cmd(remote_cmd)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    
    async def submit(self, job: JobSubmission) -> str:
        """
        Submit job by running Docker container on remote GPU host.
        
        Args:
            job: Job submission details
            
        Returns:
            Container ID as remote job ID
        """
        if not self.host:
            raise ComputeError("SSH_HOST not configured", job_id=job.run_id)
        
        # Build environment arguments
        env_args = " ".join(f"-e {k}='{v}'" for k, v in job.env.items())
        
        # Build GPU arguments
        gpu_args = ""
        if job.gpu_count > 0:
            gpu_args = f"--gpus {job.gpu_count}"
            if self.docker_runtime:
                gpu_args += f" --runtime={self.docker_runtime}"
        
        # Build resource limits
        resource_args = ""
        if job.memory_limit:
            resource_args += f" --memory {job.memory_limit}"
        if job.cpu_limit:
            resource_args += f" --cpus {job.cpu_limit}"
        
        # Build labels
        label_args = " ".join(f"--label {k}={v}" for k, v in job.labels.items())
        
        # Build command string
        command_str = " ".join(f"'{c}'" for c in job.command) if job.command else ""
        
        # Full docker run command
        docker_cmd = f"""
            docker run -d \
                --name {job.run_id} \
                {gpu_args} \
                {resource_args} \
                {env_args} \
                {label_args} \
                {job.image} \
                {command_str}
        """.strip()
        
        try:
            logger.info(f"Submitting SSH job: {job.run_id} to {self.host}")
            logger.debug(f"Docker command: {docker_cmd}")
            
            returncode, stdout, stderr = await self._run_ssh(docker_cmd)
            
            if returncode != 0:
                raise ComputeError(f"Failed to start container: {stderr}", job_id=job.run_id)
            
            container_id = stdout.strip()[:12]
            logger.info(f"Started container {container_id} on {self.host} for run {job.run_id}")
            return container_id
            
        except Exception as e:
            if isinstance(e, ComputeError):
                raise
            raise ComputeError(f"Failed to submit job: {e}", job_id=job.run_id, cause=e)
    
    async def get_status(self, remote_job_id: str) -> JobStatus:
        """
        Get container status via SSH.
        
        Args:
            remote_job_id: Container ID or name
            
        Returns:
            Current job status
        """
        if not self.host:
            return JobStatus(state=JobState.UNKNOWN, reason="SSH not configured")
        
        try:
            cmd = f"docker inspect --format='{{{{.State.Status}}}} {{{{.State.ExitCode}}}} {{{{.State.StartedAt}}}} {{{{.State.FinishedAt}}}}' {remote_job_id}"
            returncode, stdout, stderr = await self._run_ssh(cmd)
            
            if returncode != 0:
                return JobStatus(state=JobState.UNKNOWN, reason="Container not found")
            
            parts = stdout.strip().split()
            if len(parts) < 2:
                return JobStatus(state=JobState.UNKNOWN)
            
            status = parts[0]
            exit_code = int(parts[1]) if len(parts) > 1 else None
            
            # Parse timestamps
            started_at = None
            ended_at = None
            if len(parts) > 2 and "0001-01-01" not in parts[2]:
                try:
                    started_at = datetime.fromisoformat(parts[2].replace("Z", "+00:00"))
                except:
                    pass
            if len(parts) > 3 and "0001-01-01" not in parts[3]:
                try:
                    ended_at = datetime.fromisoformat(parts[3].replace("Z", "+00:00"))
                except:
                    pass
            
            # Map Docker status to JobState
            state_map = {
                "running": JobState.RUNNING,
                "exited": JobState.SUCCEEDED if exit_code == 0 else JobState.FAILED,
                "created": JobState.PENDING,
                "restarting": JobState.RUNNING,
                "paused": JobState.RUNNING,
                "removing": JobState.CANCELLED,
                "dead": JobState.FAILED,
            }
            
            return JobStatus(
                state=state_map.get(status, JobState.UNKNOWN),
                started_at=started_at,
                ended_at=ended_at,
                exit_code=exit_code if status == "exited" else None,
                reason=f"Exit code: {exit_code}" if status == "exited" and exit_code != 0 else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get status for {remote_job_id}: {e}")
            return JobStatus(state=JobState.UNKNOWN, reason=str(e))
    
    async def get_logs(self, remote_job_id: str, tail: Optional[int] = None) -> str:
        """
        Fetch container logs via SSH.
        
        Args:
            remote_job_id: Container ID or name
            tail: Optional number of lines from end
            
        Returns:
            Log content
        """
        if not self.host:
            return "SSH not configured"
        
        try:
            tail_arg = f"--tail {tail}" if tail else ""
            cmd = f"docker logs {tail_arg} {remote_job_id} 2>&1"
            
            returncode, stdout, stderr = await self._run_ssh(cmd)
            return stdout if returncode == 0 else f"Error: {stderr}"
            
        except Exception as e:
            logger.error(f"Failed to get logs for {remote_job_id}: {e}")
            return f"Error fetching logs: {e}"
    
    async def cancel(self, remote_job_id: str) -> bool:
        """
        Stop and remove container on remote host.
        
        Args:
            remote_job_id: Container ID or name
            
        Returns:
            True if cancelled successfully
        """
        if not self.host:
            return False
        
        try:
            # Stop container
            await self._run_ssh(f"docker stop -t 10 {remote_job_id}")
            # Remove container
            await self._run_ssh(f"docker rm -f {remote_job_id}")
            
            logger.info(f"Cancelled job {remote_job_id} on {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel {remote_job_id}: {e}")
            return False
    
    async def is_healthy(self) -> bool:
        """Check if SSH connection and Docker are available."""
        if not self.host:
            return False
        
        try:
            returncode, _, _ = await self._run_ssh("docker info")
            return returncode == 0
        except:
            return False
