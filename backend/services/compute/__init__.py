"""Compute service for remote job execution."""
from .adapter import ComputeAdapter, JobSubmission, JobStatus, JobState
from .local_adapter import LocalComputeAdapter
from .ssh_adapter import SSHComputeAdapter
from .runpod_adapter import RunPodAdapter

__all__ = [
    "ComputeAdapter",
    "JobSubmission", 
    "JobStatus",
    "JobState",
    "LocalComputeAdapter",
    "SSHComputeAdapter",
    "RunPodAdapter",
    "get_compute_adapter"
]


def get_compute_adapter() -> ComputeAdapter:
    """
    Get the configured compute adapter based on settings.
    
    Supported adapters:
    - local: Run containers on local Docker
    - ssh: Run containers on remote GPU VM via SSH
    - runpod: Run containers on RunPod cloud GPUs
    - k8s_gateway: Submit jobs to Kubernetes cluster
    
    Returns:
        Configured ComputeAdapter instance
    """
    from core.config import settings
    
    adapter_type = settings.compute_adapter.lower()
    
    if adapter_type == "local":
        return LocalComputeAdapter()
    elif adapter_type == "ssh":
        return SSHComputeAdapter()
    elif adapter_type == "runpod":
        return RunPodAdapter()
    elif adapter_type == "k8s_gateway":
        from .k8s_gateway_adapter import K8sGatewayAdapter
        return K8sGatewayAdapter()
    else:
        raise ValueError(f"Unknown compute adapter: {adapter_type}. Valid options: local, ssh, runpod, k8s_gateway")
