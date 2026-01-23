"""Local Docker compute adapter for development."""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .adapter import ComputeAdapter, JobSubmission, JobStatus, JobState, ComputeError

logger = logging.getLogger(__name__)


class LocalComputeAdapter(ComputeAdapter):
    """
    Execute jobs locally using Docker.
    
    Useful for development and testing without remote GPU infrastructure.
    Jobs run as Docker containers on the local machine.
    """
    
    @property
    def adapter_type(self) -> str:
        return "local"
    
    async def submit(self, job: JobSubmission) -> str:
        """
        Submit job by running Docker container locally.
        
        Args:
            job: Job submission details
            
        Returns:
            Container ID as remote job ID
        """
        # Build environment arguments
        env_args = []
        for key, value in job.env.items():
            env_args.extend(["-e", f"{key}={value}"])
        
        # Build docker run command
        cmd_parts = [
            "docker", "run", "-d",
            "--name", job.run_id,
        ]
        
        # Add environment variables
        cmd_parts.extend(env_args)
        
        # Add resource limits if specified (no GPU for local)
        if job.memory_limit:
            cmd_parts.extend(["--memory", job.memory_limit])
        
        # Add labels
        for key, value in job.labels.items():
            cmd_parts.extend(["--label", f"{key}={value}"])
        
        # Add image and command
        cmd_parts.append(job.image)
        cmd_parts.extend(job.command)
        
        try:
            logger.info(f"Submitting local job: {job.run_id}")
            logger.debug(f"Docker command: {' '.join(cmd_parts)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise ComputeError(f"Failed to start container: {error_msg}", job_id=job.run_id)
            
            container_id = stdout.decode().strip()[:12]  # Short container ID
            logger.info(f"Started container {container_id} for run {job.run_id}")
            return container_id
            
        except Exception as e:
            if isinstance(e, ComputeError):
                raise
            raise ComputeError(f"Failed to submit job: {e}", job_id=job.run_id, cause=e)
    
    async def get_status(self, remote_job_id: str) -> JobStatus:
        """
        Get container status via docker inspect.
        
        Args:
            remote_job_id: Container ID or name
            
        Returns:
            Current job status
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "inspect",
                "--format", "{{.State.Status}} {{.State.ExitCode}} {{.State.StartedAt}} {{.State.FinishedAt}}",
                remote_job_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return JobStatus(state=JobState.UNKNOWN, reason="Container not found")
            
            parts = stdout.decode().strip().split()
            if len(parts) < 2:
                return JobStatus(state=JobState.UNKNOWN)
            
            status = parts[0]
            exit_code = int(parts[1]) if len(parts) > 1 else None
            
            # Parse timestamps
            started_at = None
            ended_at = None
            if len(parts) > 2 and parts[2] != "0001-01-01T00:00:00Z":
                try:
                    started_at = datetime.fromisoformat(parts[2].replace("Z", "+00:00"))
                except:
                    pass
            if len(parts) > 3 and parts[3] != "0001-01-01T00:00:00Z":
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
        Fetch container logs.
        
        Args:
            remote_job_id: Container ID or name
            tail: Optional number of lines from end
            
        Returns:
            Log content
        """
        try:
            cmd = ["docker", "logs"]
            if tail:
                cmd.extend(["--tail", str(tail)])
            cmd.append(remote_job_id)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await process.communicate()
            return stdout.decode()
            
        except Exception as e:
            logger.error(f"Failed to get logs for {remote_job_id}: {e}")
            return f"Error fetching logs: {e}"
    
    async def cancel(self, remote_job_id: str) -> bool:
        """
        Stop and remove container.
        
        Args:
            remote_job_id: Container ID or name
            
        Returns:
            True if cancelled successfully
        """
        try:
            # Stop container
            process = await asyncio.create_subprocess_exec(
                "docker", "stop", "-t", "10", remote_job_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Remove container
            process = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", remote_job_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            logger.info(f"Cancelled job {remote_job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel {remote_job_id}: {e}")
            return False
    
    async def is_healthy(self) -> bool:
        """Check if Docker is available."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
