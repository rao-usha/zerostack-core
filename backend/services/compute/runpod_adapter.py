"""RunPod compute adapter for cloud GPU execution.

Integrates with RunPod API to:
- Create GPU pods on demand
- Submit containerized jobs
- Track job status
- Retrieve logs
- Clean up resources

RunPod API Docs: https://docs.runpod.io/
"""
import os
import asyncio
import logging
import aiohttp
from typing import Optional
from datetime import datetime

from services.compute.adapter import (
    ComputeAdapter, 
    JobSubmission, 
    JobStatus, 
    JobState, 
    ComputeError
)
from core.config import settings

logger = logging.getLogger(__name__)


# RunPod API base URL
RUNPOD_API_URL = "https://api.runpod.io/graphql"
RUNPOD_REST_URL = "https://api.runpod.io/v2"


class RunPodAdapter(ComputeAdapter):
    """
    RunPod GPU compute adapter.
    
    Supports three modes (in priority order):
    1. Serverless: Call a pre-deployed serverless endpoint (RUNPOD_ENDPOINT_ID)
    2. Existing Pod: Use a specific pod (RUNPOD_POD_ID) or auto-detect running pods
    3. New Pod: Create ephemeral pods (requires public Docker images - NOT RECOMMENDED)
    
    If no config is set, will AUTO-DETECT any running pods and use them.
    """
    
    def __init__(self):
        self.api_key = settings.runpod_api_key
        self.default_gpu = getattr(settings, 'runpod_default_gpu', 'NVIDIA RTX A5000')
        self.template_id = getattr(settings, 'runpod_template_id', None)
        
        # Helper to filter out placeholder/invalid values
        def _clean_setting(value):
            if not value:
                return None
            # Filter out common placeholder strings
            placeholders = ['your-endpoint-id', 'your-pod-id', 'placeholder', 'xxx', 'none', '']
            if value.lower().strip() in placeholders:
                return None
            return value
        
        # Serverless endpoint ID (recommended mode)
        self.endpoint_id = _clean_setting(getattr(settings, 'runpod_endpoint_id', None))
        # Existing pod ID (alternative to serverless)
        self.pod_id = _clean_setting(getattr(settings, 'runpod_pod_id', None))
        # Cache for auto-detected pod
        self._auto_detected_pod_id = None
        
        if not self.api_key:
            logger.warning("RUNPOD_API_KEY not configured - RunPod adapter will fail on submit")
        
        # Log which mode we're using
        if self.endpoint_id:
            logger.info(f"RunPod adapter using SERVERLESS mode (endpoint: {self.endpoint_id})")
        elif self.pod_id:
            logger.info(f"RunPod adapter using EXISTING POD mode (pod: {self.pod_id})")
        else:
            logger.info("RunPod adapter will AUTO-DETECT running pods at submit time")
    
    async def list_available_gpus(self) -> list:
        """
        List available GPU types from RunPod with current availability.
        
        Returns:
            List of available GPUs with pricing and availability info
        """
        query = """
        query GpuTypes {
            gpuTypes {
                id
                displayName
                memoryInGb
                secureCloud
                communityCloud
                lowestPrice(input: { gpuCount: 1 }) {
                    minimumBidPrice
                    uninterruptablePrice
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query)
            gpu_types = result.get("gpuTypes", [])
            
            # Filter and format the results
            available = []
            for gpu in gpu_types:
                # Only include GPUs that are available
                if gpu.get("secureCloud") or gpu.get("communityCloud"):
                    lowest_price = gpu.get("lowestPrice") or {}
                    available.append({
                        "id": gpu.get("id"),
                        "name": gpu.get("displayName"),
                        "memory_gb": gpu.get("memoryInGb"),
                        "secure_cloud": gpu.get("secureCloud", False),
                        "community_cloud": gpu.get("communityCloud", False),
                        "hourly_rate_usd": lowest_price.get("uninterruptablePrice"),
                        "spot_rate_usd": lowest_price.get("minimumBidPrice")
                    })
            
            # Sort by price
            available.sort(key=lambda x: x.get("hourly_rate_usd") or 999)
            return available
            
        except Exception as e:
            logger.error(f"Failed to list GPU types: {e}")
            return []
    
    async def get_my_pods(self) -> list:
        """
        Get list of currently running pods for the user.
        
        Returns:
            List of running pods
        """
        query = """
        query Pods {
            myself {
                pods {
                    id
                    name
                    desiredStatus
                    imageName
                    gpuCount
                    machine {
                        gpuDisplayName
                    }
                    runtime {
                        uptimeInSeconds
                    }
                    costPerHr
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query)
            pods = result.get("myself", {}).get("pods", [])
            return [
                {
                    "id": pod.get("id"),
                    "name": pod.get("name"),
                    "status": pod.get("desiredStatus"),
                    "image": pod.get("imageName"),
                    "gpu_count": pod.get("gpuCount"),
                    "gpu_type": pod.get("machine", {}).get("gpuDisplayName") if pod.get("machine") else None,
                    "uptime_seconds": pod.get("runtime", {}).get("uptimeInSeconds") if pod.get("runtime") else 0,
                    "cost_per_hour": pod.get("costPerHr")
                }
                for pod in pods
            ]
        except Exception as e:
            logger.error(f"Failed to get pods: {e}")
            return []
    
    async def get_spending(self) -> dict:
        """
        Get current spending and billing info from RunPod.
        
        Returns:
            Spending summary with costs
        """
        query = """
        query Spending {
            myself {
                id
                currentSpendPerHr
                machineQuota
                referralEarned
                spendLimit
                templateEarned
                notifyPodsStale
                notifyPodsGeneral
                notifyLowBalance
                clientBalance
                hostBalance
                minBalance
                underBalance
            }
        }
        """
        
        try:
            result = await self._graphql_query(query)
            myself = result.get("myself", {})
            return {
                "client_balance": myself.get("clientBalance"),
                "host_balance": myself.get("hostBalance"),
                "min_balance": myself.get("minBalance"),
                "spend_per_hour": myself.get("currentSpendPerHr"),
                "spend_limit": myself.get("spendLimit"),
                "under_balance": myself.get("underBalance"),
                "low_balance_alert": myself.get("notifyLowBalance"),
                "machine_quota": myself.get("machineQuota"),
                "referral_earned": myself.get("referralEarned"),
                "template_earned": myself.get("templateEarned")
            }
        except Exception as e:
            logger.error(f"Failed to get spending: {e}")
            return {}
    
    @property
    def adapter_type(self) -> str:
        return "runpod"
    
    def _get_headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _graphql_query(self, query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query against RunPod API."""
        if not self.api_key:
            raise ComputeError("RUNPOD_API_KEY not configured")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RUNPOD_API_URL,
                headers=self._get_headers(),
                json={"query": query, "variables": variables or {}}
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise ComputeError(f"RunPod API error: {response.status} - {text}")
                
                data = await response.json()
                if "errors" in data:
                    raise ComputeError(f"RunPod GraphQL error: {data['errors']}")
                
                return data.get("data", {})
    
    async def submit(self, job: JobSubmission) -> str:
        """
        Submit a job to RunPod.

        Supports three modes (auto-detects running pods if not configured):
        1. Serverless endpoint (RUNPOD_ENDPOINT_ID set) - recommended
        2. Existing pod (RUNPOD_POD_ID set OR auto-detected running pod)
        3. New pod creation - ONLY if no running pods found (requires public images)

        Args:
            job: Job submission details

        Returns:
            Job/Pod ID for tracking
        """
        logger.info(f"Submitting job {job.run_id} to RunPod")

        # Mode 1: Serverless endpoint (recommended)
        if self.endpoint_id:
            return await self._submit_serverless(job)

        # Mode 2: Existing pod (configured or auto-detected)
        pod_to_use = self.pod_id or self._auto_detected_pod_id
        
        if not pod_to_use:
            # Try to auto-detect a running pod
            pod_to_use = await self._find_running_pod()
            if pod_to_use:
                self._auto_detected_pod_id = pod_to_use
                logger.info(f"Auto-detected running pod: {pod_to_use}")
        
        if pod_to_use:
            return await self._submit_to_existing_pod_by_id(job, pod_to_use)

        # Mode 3: Create new pod (legacy, requires public images) - WARN USER
        logger.warning("No running pods found! Will try to create new pod (requires public Docker image)")
        return await self._submit_new_pod(job)
    
    async def _find_running_pod(self) -> str | None:
        """Find a running pod to use for jobs."""
        try:
            pods = await self.get_my_pods()
            running_pods = [p for p in pods if p.get('status') == 'RUNNING']
            
            if running_pods:
                # Return the first running pod
                pod = running_pods[0]
                logger.info(f"Found running pod: {pod.get('name')} ({pod.get('id')})")
                return pod.get('id')
            
            return None
        except Exception as e:
            logger.error(f"Failed to find running pods: {e}")
            return None
    
    async def _submit_serverless(self, job: JobSubmission) -> str:
        """Submit job to serverless endpoint."""
        logger.info(f"Submitting to serverless endpoint {self.endpoint_id}")
        
        # RunPod serverless API
        url = f"https://api.runpod.ai/v2/{self.endpoint_id}/run"
        
        payload = {
            "input": {
                "run_id": job.run_id,
                "input_uri": job.input_uri,
                "output_uri": job.output_uri,
                "params": job.env.get("PARAMS_JSON", "{}"),
                # Pass all env vars for the job
                **{k.lower(): v for k, v in job.env.items()}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status not in (200, 201):
                    text = await response.text()
                    raise ComputeError(f"Serverless submit failed: {response.status} - {text}")
                
                data = await response.json()
                job_id = data.get("id")
                
                if not job_id:
                    raise ComputeError(f"No job ID returned: {data}")
                
                logger.info(f"Submitted serverless job {job_id} for run {job.run_id}")
                return f"serverless:{self.endpoint_id}:{job_id}"
    
    async def _submit_to_existing_pod(self, job: JobSubmission) -> str:
        """Submit job to the configured existing pod."""
        return await self._submit_to_existing_pod_by_id(job, self.pod_id)
    
    async def _submit_to_existing_pod_by_id(self, job: JobSubmission, pod_id: str) -> str:
        """
        Submit job to a specific existing running pod via SSH.
        
        This method:
        1. Connects to pod via SSH
        2. Creates job directory
        3. Uploads training script from local ml_models
        4. Uploads input data from MinIO via SFTP
        5. Starts training in background with nohup
        """
        import asyncssh
        import os
        
        logger.info(f"Submitting to existing pod {pod_id}")

        # Get pod details including SSH connection info
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                desiredStatus
                machine {
                    gpuDisplayName
                }
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """

        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})

            if not pod:
                raise ComputeError(f"Pod {pod_id} not found")

            if pod.get("desiredStatus") != "RUNNING":
                raise ComputeError(f"Pod {pod_id} is not running (status: {pod.get('desiredStatus')})")

            # Get SSH connection details
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_port = None
            ssh_ip = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:  # SSH port
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                raise ComputeError(f"Pod {pod_id} does not have SSH access configured")
            
            pod_name = pod.get("name", pod_id)
            gpu_type = pod.get("machine", {}).get("gpuDisplayName", "Unknown GPU")
            logger.info(f"✅ Connecting to pod '{pod_name}' ({pod_id}) - {gpu_type}")
            logger.info(f"   SSH: {ssh_ip}:{ssh_port}")
            
            # Get SSH key path
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        logger.info(f"Using SSH key: {ssh_key_path}")
                        break
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            try:
                async with asyncssh.connect(**connect_kwargs) as conn:
                    run_id = job.run_id
                    job_path = f"/root/nex_ml/jobs/{run_id}"
                    
                    # Step 1: Create job directories
                    logger.info(f"Creating job directory: {job_path}")
                    await conn.run(f"mkdir -p {job_path}/input {job_path}/output", check=True)
                    
                    # Step 2: Upload training script from local ml_models
                    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models', 'forecasting', 'train.py')
                    if not os.path.exists(script_path):
                        script_path = '/app/ml_models/forecasting/train.py'
                    
                    if os.path.exists(script_path):
                        logger.info("Uploading training script...")
                        with open(script_path, 'r') as f:
                            train_script = f.read()
                        
                        await conn.run("mkdir -p /root/nex_ml/forecasting", check=True)
                        write_cmd = f"""cat > /root/nex_ml/forecasting/train.py << 'ENDOFSCRIPT'
{train_script}
ENDOFSCRIPT"""
                        await conn.run(write_cmd, check=True)
                    else:
                        logger.warning(f"Training script not found at {script_path}, skipping upload")
                    
                    # Step 3: Upload input data from MinIO via SFTP
                    # Get input data from object store
                    from services.object_store import ObjectStoreClient
                    
                    storage = ObjectStoreClient.get_instance()
                    input_uri = job.input_uri or f"datasets/{job.env.get('RECIPE_ID', 'default')}/latest"
                    
                    logger.info(f"Uploading input data from {input_uri}...")
                    
                    async with conn.start_sftp_client() as sftp:
                        # Try to upload common data files
                        for filename in ['sales.parquet', 'calendar.parquet', 'prices.parquet', 'data.parquet', 'input.parquet']:
                            local_key = f"{input_uri}/{filename}"
                            remote_path = f"{job_path}/input/{filename}"
                            
                            try:
                                data = storage.get_bytes(local_key)
                                async with sftp.open(remote_path, 'wb') as remote_file:
                                    await remote_file.write(data)
                                logger.info(f"  Uploaded {filename} ({len(data):,} bytes)")
                            except Exception as e:
                                # File might not exist, that's OK
                                logger.debug(f"  Could not upload {filename}: {e}")
                    
                    # Step 4: Get parameters
                    params = job.env.get('PARAMS_JSON', '{}')
                    try:
                        import json
                        params_dict = json.loads(params.replace("'", '"')) if isinstance(params, str) else params
                        horizon = params_dict.get('horizon', 28)
                    except:
                        horizon = 28
                    
                    # Step 5: Start training in background with nohup
                    logger.info(f"Starting training (horizon={horizon})...")
                    train_cmd = f"""
cd /root/nex_ml && nohup python forecasting/train.py \\
    --input {job_path}/input \\
    --output {job_path}/output \\
    --horizon {horizon} \\
    > {job_path}/output/training.log 2>&1 &
echo $!
"""
                    result = await conn.run(train_cmd, check=False, timeout=30)
                    
                    if result.exit_status == 0:
                        pid = result.stdout.strip()
                        logger.info(f"✅ Training started with PID: {pid}")
                        logger.info(f"✅ Job {run_id} submitted to pod {pod_id}")
                        
                        # Write PID file for tracking
                        await conn.run(f"echo {pid} > {job_path}/pid", check=False)
                    else:
                        logger.error(f"Failed to start training: {result.stderr}")
                        raise ComputeError(f"Failed to start training: {result.stderr}")
                    
            except asyncssh.Error as ssh_err:
                logger.error(f"SSH connection failed: {ssh_err}")
                raise ComputeError(f"SSH connection to pod {pod_id} failed: {ssh_err}")
            
            return f"pod:{pod_id}:{job.run_id}"

        except ComputeError:
            raise
        except Exception as e:
            logger.error(f"Failed to submit to existing pod {pod_id}: {e}")
            raise ComputeError(f"Failed to submit to pod {pod_id}: {e}")
    
    async def _submit_new_pod(self, job: JobSubmission) -> str:
        """Create a new pod for the job (legacy mode)."""
        logger.warning("Creating new pod - this requires a public Docker image!")
        
        # Map GPU count to RunPod GPU type
        gpu_type = self._map_gpu_type(self.default_gpu)
        
        # Build environment variables string
        env_vars = []
        for key, value in job.env.items():
            env_vars.append({"key": key, "value": value})
        
        # Create pod mutation
        mutation = """
        mutation createPod($input: PodFindAndDeployOnDemandInput!) {
            podFindAndDeployOnDemand(input: $input) {
                id
                name
                desiredStatus
                imageName
            }
        }
        """
        
        variables = {
            "input": {
                "cloudType": "SECURE",  # or "COMMUNITY" for cheaper
                "gpuCount": job.gpu_count,
                "volumeInGb": 20,
                "containerDiskInGb": 20,
                "gpuTypeId": gpu_type,
                "name": f"nex-{job.run_id[:8]}",
                "imageName": job.image,
                "dockerArgs": " ".join(job.command) if job.command else "",
                "env": env_vars,
                "supportPublicIp": False,
            }
        }
        
        # Add template if configured
        if self.template_id:
            variables["input"]["templateId"] = self.template_id
        
        try:
            result = await self._graphql_query(mutation, variables)
            pod_data = result.get("podFindAndDeployOnDemand", {})
            pod_id = pod_data.get("id")
            
            if not pod_id:
                raise ComputeError("No pod ID returned from RunPod")
            
            logger.info(f"Created RunPod pod {pod_id} for job {job.run_id}")
            return pod_id
            
        except Exception as e:
            logger.error(f"Failed to submit job to RunPod: {e}")
            raise ComputeError(f"RunPod submit failed: {e}", job_id=job.run_id, cause=e)
    
    async def get_status(self, remote_job_id: str) -> JobStatus:
        """
        Get the status of a RunPod job.
        
        Handles different job ID formats:
        - serverless:endpoint_id:job_id - serverless job
        - pod:pod_id:run_id - existing pod job
        - pod_id - legacy new pod mode
        
        Args:
            remote_job_id: Job identifier
            
        Returns:
            Current job status
        """
        # Parse job ID format
        if remote_job_id.startswith("serverless:"):
            parts = remote_job_id.split(":", 2)
            if len(parts) == 3:
                return await self._get_serverless_status(parts[1], parts[2])
        
        if remote_job_id.startswith("pod:"):
            parts = remote_job_id.split(":", 2)
            if len(parts) == 3:
                return await self._get_existing_pod_status(parts[1], parts[2])
        
        # Legacy: direct pod ID
        return await self._get_pod_status(remote_job_id)
    
    async def _get_serverless_status(self, endpoint_id: str, job_id: str) -> JobStatus:
        """Get status of a serverless job."""
        url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        return JobStatus(state=JobState.UNKNOWN, reason="Status check failed")
                    
                    data = await response.json()
                    status = data.get("status", "").upper()
                    
                    # Map RunPod serverless status
                    if status == "COMPLETED":
                        return JobStatus(state=JobState.SUCCEEDED)
                    elif status == "FAILED":
                        return JobStatus(state=JobState.FAILED, reason=data.get("error"))
                    elif status in ("IN_PROGRESS", "IN_QUEUE"):
                        return JobStatus(state=JobState.RUNNING)
                    elif status == "CANCELLED":
                        return JobStatus(state=JobState.CANCELLED)
                    else:
                        return JobStatus(state=JobState.PENDING, reason=f"Status: {status}")
                        
        except Exception as e:
            logger.error(f"Failed to get serverless status: {e}")
            return JobStatus(state=JobState.UNKNOWN, reason=str(e))
    
    async def _get_existing_pod_status(self, pod_id: str, run_id: str) -> JobStatus:
        """
        Get status of a job on existing pod.
        
        Actually checks if the job exists and is running on the pod,
        not just whether the pod itself is running.
        """
        import asyncssh
        import os
        
        try:
            # First check if pod is even running
            pod_status = await self._get_pod_status(pod_id)
            if pod_status.state != JobState.RUNNING:
                return pod_status
            
            # Get pod SSH details to check actual job status
            query = """
            query Pod($podId: String!) {
                pod(input: { podId: $podId }) {
                    id
                    runtime {
                        ports { ip privatePort publicPort }
                    }
                }
            }
            """
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod:
                return JobStatus(state=JobState.UNKNOWN, reason="Pod not found")
            
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                # Can't SSH to verify, assume running if pod is running
                return JobStatus(state=JobState.RUNNING, reason="Pod active (SSH unavailable for verification)")
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 10,
            }
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            try:
                async with asyncssh.connect(**connect_kwargs) as conn:
                    # Check if job directory exists
                    job_path = f"/root/nex_ml/jobs/{run_id}"
                    check_result = await conn.run(f"test -d {job_path} && echo 'exists'", check=False)
                    
                    if "exists" not in check_result.stdout:
                        # Job directory doesn't exist - job never started
                        return JobStatus(
                            state=JobState.FAILED, 
                            reason="Job directory not found on pod - job never started"
                        )
                    
                    # Check if metrics.json exists (job completed)
                    metrics_check = await conn.run(
                        f"test -f {job_path}/output/metrics.json && echo 'completed'", 
                        check=False
                    )
                    
                    if "completed" in metrics_check.stdout:
                        return JobStatus(state=JobState.SUCCEEDED, reason="Job completed (metrics.json found)")
                    
                    # Check if there's an active Python process for this job
                    process_check = await conn.run(
                        f"pgrep -f 'python.*{run_id}' || pgrep -f 'train.py' | head -1", 
                        check=False
                    )
                    
                    if process_check.stdout.strip():
                        return JobStatus(state=JobState.RUNNING, reason="Training process active on pod")
                    
                    # Job directory exists but no process running and no metrics
                    # Could be starting up, or could be stalled
                    # Check if job was created recently (within last 5 minutes)
                    age_check = await conn.run(
                        f"find {job_path} -maxdepth 0 -mmin -5 2>/dev/null | head -1",
                        check=False
                    )
                    
                    if age_check.stdout.strip():
                        return JobStatus(state=JobState.RUNNING, reason="Job starting (directory recently created)")
                    
                    # Job directory is old but no process or output - likely failed
                    return JobStatus(
                        state=JobState.FAILED, 
                        reason="Job directory exists but no active process or output - job may have crashed"
                    )
                    
            except asyncssh.Error as ssh_err:
                logger.warning(f"SSH check failed for job {run_id}: {ssh_err}")
                # Fall back to pod-level check
                return JobStatus(state=JobState.RUNNING, reason="Pod active (SSH verification failed)")
            
        except Exception as e:
            logger.error(f"Failed to get existing pod status: {e}")
            return JobStatus(state=JobState.UNKNOWN, reason=str(e))
    
    async def _get_pod_status(self, pod_id: str) -> JobStatus:
        """Get status of a pod directly."""
        query = """
        query getPod($podId: String!) {
            pod(input: {podId: $podId}) {
                id
                name
                desiredStatus
                lastStatusChange
                runtime {
                    uptimeInSeconds
                    gpus {
                        id
                        gpuUtilPercent
                    }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod")
            
            if not pod:
                return JobStatus(
                    state=JobState.UNKNOWN,
                    reason="Pod not found"
                )
            
            # Map RunPod status to our JobState
            runpod_status = pod.get("desiredStatus", "").upper()
            state = self._map_status(runpod_status)
            
            # Get runtime info
            runtime = pod.get("runtime", {})
            uptime = runtime.get("uptimeInSeconds", 0) if runtime else 0
            
            return JobStatus(
                state=state,
                started_at=None,  # Would need to track separately
                progress=None,
                reason=f"RunPod status: {runpod_status}"
            )
            
        except Exception as e:
            logger.error(f"Failed to get RunPod pod status: {e}")
            return JobStatus(state=JobState.UNKNOWN, reason=str(e))
    
    async def get_logs(self, remote_job_id: str, tail: Optional[int] = None) -> str:
        """
        Get logs from a RunPod pod.
        
        Note: RunPod logs API is limited. For full logs, the container
        should write to S3/MinIO which we already do.
        """
        # RunPod doesn't have a great logs API via GraphQL
        # Best practice is to have the container stream logs to object storage
        # For now, return a placeholder pointing to S3
        return f"Logs for RunPod pod {remote_job_id} are stored in object storage.\nCheck s3://nex-data/runs/*/logs.txt"
    
    async def cancel(self, remote_job_id: str) -> bool:
        """
        Terminate a RunPod pod.
        
        Args:
            remote_job_id: Pod ID
            
        Returns:
            True if terminated successfully
        """
        mutation = """
        mutation terminatePod($podId: String!) {
            podTerminate(input: {podId: $podId})
        }
        """
        
        try:
            await self._graphql_query(mutation, {"podId": remote_job_id})
            logger.info(f"Terminated RunPod pod {remote_job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to terminate RunPod pod: {e}")
            return False
    
    async def is_healthy(self) -> bool:
        """Check if RunPod API is accessible."""
        if not self.api_key:
            return False
        
        query = """
        query {
            myself {
                id
            }
        }
        """
        
        try:
            result = await self._graphql_query(query)
            return "myself" in result
        except Exception:
            return False
    
    def _map_gpu_type(self, gpu_name: str) -> str:
        """
        Map GPU name to RunPod GPU type ID.
        
        See: https://docs.runpod.io/references/gpu-types
        """
        gpu_mapping = {
            "NVIDIA RTX A4000": "NVIDIA RTX A4000",
            "NVIDIA RTX A5000": "NVIDIA RTX A5000",
            "NVIDIA RTX 3090": "NVIDIA GeForce RTX 3090",
            "NVIDIA RTX 4090": "NVIDIA GeForce RTX 4090",
            "NVIDIA A40": "NVIDIA A40",
            "NVIDIA A100 40GB": "NVIDIA A100-SXM4-40GB",
            "NVIDIA A100 80GB": "NVIDIA A100-SXM4-80GB",
            "NVIDIA H100 80GB": "NVIDIA H100 80GB HBM3",
        }
        return gpu_mapping.get(gpu_name, gpu_name)
    
    def _map_status(self, runpod_status: str) -> JobState:
        """Map RunPod status to JobState."""
        status_mapping = {
            "CREATED": JobState.PENDING,
            "RUNNING": JobState.RUNNING,
            "EXITED": JobState.SUCCEEDED,  # Need to check exit code
            "TERMINATED": JobState.CANCELLED,
            "PAUSED": JobState.PENDING,
        }
        return status_mapping.get(runpod_status, JobState.UNKNOWN)
    
    async def run_gpu_test(self) -> dict:
        """
        Run GPU test script on the configured pod.
        
        This syncs the ml_models code to the pod and runs the GPU test.
        Auto-detects running pods if the configured one isn't available.
        
        Returns:
            Test results dictionary
        """
        import asyncssh
        import os
        
        # Find pod to use - prefer configured, but auto-detect if not running
        pod_id = self.pod_id or self._auto_detected_pod_id
        
        # Check if configured pod is actually running
        if pod_id:
            check_query = """
            query Pod($podId: String!) {
                pod(input: { podId: $podId }) {
                    desiredStatus
                }
            }
            """
            try:
                result = await self._graphql_query(check_query, {"podId": pod_id})
                pod_info = result.get("pod", {})
                if not pod_info or pod_info.get("desiredStatus") != "RUNNING":
                    logger.info(f"Configured pod {pod_id} not running, auto-detecting...")
                    pod_id = None
            except:
                pod_id = None
        
        # Auto-detect if needed
        if not pod_id:
            pod_id = await self._find_running_pod()
            if pod_id:
                self._auto_detected_pod_id = pod_id
                logger.info(f"Auto-detected running pod: {pod_id}")
        
        if not pod_id:
            return {"status": "error", "error": "No running pod found"}
        
        # Get pod SSH details
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                desiredStatus
                machine {
                    gpuDisplayName
                }
                runtime {
                    ports {
                        ip
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod or pod.get("desiredStatus") != "RUNNING":
                return {"status": "error", "error": f"Pod {pod_id} is not running"}
            
            # Get SSH connection details
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                return {"status": "error", "error": "Pod does not have SSH access"}
            
            pod_name = pod.get("name", pod_id)
            gpu_type = pod.get("machine", {}).get("gpuDisplayName", "Unknown")
            
            logger.info(f"Running GPU test on pod '{pod_name}' ({gpu_type})")
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            # Read the GPU test script
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models', 'tests', 'gpu_test.py')
            if not os.path.exists(script_path):
                # Try alternate path (when running from /app)
                script_path = '/app/ml_models/tests/gpu_test.py'
            
            if not os.path.exists(script_path):
                return {"status": "error", "error": f"GPU test script not found at {script_path}"}
            
            with open(script_path, 'r') as f:
                gpu_test_script = f.read()
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Create directory and write script
                logger.info("Syncing GPU test script to pod...")
                await conn.run("mkdir -p /root/nex_ml/tests", check=True)
                
                # Write script using cat with heredoc
                write_cmd = f"""cat > /root/nex_ml/tests/gpu_test.py << 'ENDOFSCRIPT'
{gpu_test_script}
ENDOFSCRIPT"""
                await conn.run(write_cmd, check=True)
                
                # Run the test
                logger.info("Executing GPU test...")
                result = await conn.run(
                    "cd /root/nex_ml/tests && python gpu_test.py 2>&1",
                    check=False,
                    timeout=120
                )
                
                output = result.stdout if result.stdout else ""
                
                # Parse JSON from output
                import json
                json_start = output.find("--- JSON OUTPUT ---")
                if json_start != -1:
                    json_str = output[json_start + 20:].strip()
                    try:
                        test_results = json.loads(json_str)
                        test_results["pod_id"] = pod_id
                        test_results["pod_name"] = pod_name
                        test_results["gpu_type"] = gpu_type
                        return test_results
                    except json.JSONDecodeError:
                        pass
                
                return {
                    "status": "completed",
                    "pod_id": pod_id,
                    "pod_name": pod_name,
                    "gpu_type": gpu_type,
                    "output": output,
                    "exit_code": result.exit_status
                }
                
        except asyncssh.Error as e:
            logger.error(f"SSH error during GPU test: {e}")
            return {"status": "error", "error": f"SSH error: {str(e)}"}
        except Exception as e:
            logger.error(f"GPU test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def setup_pod(self) -> dict:
        """
        Install ML dependencies on the pod.
        
        This syncs the setup script and runs it to install:
        - LightGBM
        - scikit-learn
        - pandas, numpy, pyarrow
        - boto3 (S3 access)
        
        Returns:
            Setup results dictionary
        """
        import asyncssh
        import os
        
        # Find pod to use (same logic as run_gpu_test)
        pod_id = self.pod_id or self._auto_detected_pod_id
        
        if pod_id:
            check_query = """
            query Pod($podId: String!) {
                pod(input: { podId: $podId }) {
                    desiredStatus
                }
            }
            """
            try:
                result = await self._graphql_query(check_query, {"podId": pod_id})
                pod_info = result.get("pod", {})
                if not pod_info or pod_info.get("desiredStatus") != "RUNNING":
                    pod_id = None
            except:
                pod_id = None
        
        if not pod_id:
            pod_id = await self._find_running_pod()
            if pod_id:
                self._auto_detected_pod_id = pod_id
        
        if not pod_id:
            return {"status": "error", "error": "No running pod found"}
        
        # Get pod details
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                desiredStatus
                machine {
                    gpuDisplayName
                }
                runtime {
                    ports {
                        ip
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod or pod.get("desiredStatus") != "RUNNING":
                return {"status": "error", "error": f"Pod {pod_id} is not running"}
            
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                return {"status": "error", "error": "Pod does not have SSH access"}
            
            pod_name = pod.get("name", pod_id)
            gpu_type = pod.get("machine", {}).get("gpuDisplayName", "Unknown")
            
            logger.info(f"Setting up pod '{pod_name}' ({gpu_type})")
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            # Read the setup script
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models', 'setup_pod.py')
            if not os.path.exists(script_path):
                script_path = '/app/ml_models/setup_pod.py'
            
            if not os.path.exists(script_path):
                return {"status": "error", "error": f"Setup script not found at {script_path}"}
            
            with open(script_path, 'r') as f:
                setup_script = f.read()
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Create directory and write setup script
                logger.info("Syncing setup script to pod...")
                await conn.run("mkdir -p /root/nex_ml", check=True)
                
                write_cmd = f"""cat > /root/nex_ml/setup_pod.py << 'ENDOFSCRIPT'
{setup_script}
ENDOFSCRIPT"""
                await conn.run(write_cmd, check=True)
                
                # Run setup (this may take a few minutes)
                logger.info("Installing dependencies (this may take 2-3 minutes)...")
                result = await conn.run(
                    "cd /root/nex_ml && python setup_pod.py 2>&1",
                    check=False,
                    timeout=300  # 5 minute timeout
                )
                
                output = result.stdout if result.stdout else ""
                success = result.exit_status == 0
                
                return {
                    "status": "success" if success else "failed",
                    "pod_id": pod_id,
                    "pod_name": pod_name,
                    "gpu_type": gpu_type,
                    "output": output,
                    "exit_code": result.exit_status
                }
                
        except asyncssh.Error as e:
            logger.error(f"SSH error during setup: {e}")
            return {"status": "error", "error": f"SSH error: {str(e)}"}
        except Exception as e:
            logger.error(f"Pod setup failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_forecast(self, job_id: str, input_prefix: str, horizon: int = 28) -> dict:
        """
        Run M5 forecasting on the pod.
        
        Args:
            job_id: Unique job identifier
            input_prefix: S3 prefix where input data is stored
            horizon: Forecast horizon in days
            
        Returns:
            Forecast results
        """
        import asyncssh
        import os
        
        # Find pod
        pod_id = self.pod_id or self._auto_detected_pod_id
        
        if pod_id:
            check_query = """
            query Pod($podId: String!) {
                pod(input: { podId: $podId }) {
                    desiredStatus
                }
            }
            """
            try:
                result = await self._graphql_query(check_query, {"podId": pod_id})
                pod_info = result.get("pod", {})
                if not pod_info or pod_info.get("desiredStatus") != "RUNNING":
                    pod_id = None
            except:
                pod_id = None
        
        if not pod_id:
            pod_id = await self._find_running_pod()
            if pod_id:
                self._auto_detected_pod_id = pod_id
        
        if not pod_id:
            return {"status": "error", "error": "No running pod found"}
        
        # Get pod details
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                desiredStatus
                machine {
                    gpuDisplayName
                }
                runtime {
                    ports {
                        ip
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod or pod.get("desiredStatus") != "RUNNING":
                return {"status": "error", "error": f"Pod {pod_id} is not running"}
            
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                return {"status": "error", "error": "Pod does not have SSH access"}
            
            pod_name = pod.get("name", pod_id)
            gpu_type = pod.get("machine", {}).get("gpuDisplayName", "Unknown")
            
            logger.info(f"Running forecast job {job_id} on pod '{pod_name}'")
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            # Read the training script
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models', 'forecasting', 'train.py')
            if not os.path.exists(script_path):
                script_path = '/app/ml_models/forecasting/train.py'
            
            if not os.path.exists(script_path):
                return {"status": "error", "error": f"Training script not found at {script_path}"}
            
            with open(script_path, 'r') as f:
                train_script = f.read()
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            # Database settings for pod to download data directly
            db_host = settings.explorer_db_host
            if db_host == 'host.docker.internal':
                # Pod is external, use public-accessible host
                # For now, assume the pod can reach the database via host.docker.internal
                # (this works if RunPod has network access to your machine)
                pass
            
            db_port = settings.explorer_db_port
            db_user = settings.explorer_db_user
            db_password = settings.explorer_db_password
            db_name = settings.explorer_db_name
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Create directories
                await conn.run("mkdir -p /root/nex_ml/forecasting /root/nex_ml/jobs", check=True)
                
                # Write training script
                logger.info("Syncing training script...")
                write_cmd = f"""cat > /root/nex_ml/forecasting/train.py << 'ENDOFSCRIPT'
{train_script}
ENDOFSCRIPT"""
                await conn.run(write_cmd, check=True)
                
                # Upload data directly via SFTP (pod can't access local DB/MinIO)
                logger.info("Uploading data to pod via SFTP...")
                
                # Download data from MinIO to backend first
                from services.object_store import ObjectStoreClient
                import tempfile
                
                storage = ObjectStoreClient.get_instance()
                remote_input_dir = f"/root/nex_ml/jobs/{job_id}/input"
                
                # Create remote directory
                await conn.run(f"mkdir -p {remote_input_dir}", check=True)
                
                # Get SFTP client
                async with conn.start_sftp_client() as sftp:
                    for filename in ['sales.parquet', 'calendar.parquet', 'prices.parquet']:
                        local_key = f"{input_prefix}/{filename}"
                        remote_path = f"{remote_input_dir}/{filename}"
                        
                        logger.info(f"  Uploading {filename}...")
                        try:
                            # Download from MinIO to temp file
                            data = storage.get_bytes(local_key)
                            
                            # Upload to pod via SFTP
                            async with sftp.open(remote_path, 'wb') as remote_file:
                                await remote_file.write(data)
                            
                            logger.info(f"    Uploaded {len(data):,} bytes")
                        except Exception as e:
                            logger.error(f"Failed to upload {filename}: {e}")
                            return {"status": "error", "error": f"Failed to upload {filename}: {e}"}
                
                logger.info("Data upload complete!")
                
                # Run training
                logger.info(f"Running LightGBM training (horizon={horizon})...")
                train_cmd = f"""
cd /root/nex_ml && python forecasting/train.py \
    --input /root/nex_ml/jobs/{job_id}/input \
    --output /root/nex_ml/jobs/{job_id}/output \
    --horizon {horizon} 2>&1
"""
                result = await conn.run(train_cmd, check=False, timeout=600)  # 10 minute timeout
                
                output = result.stdout if result.stdout else ""
                success = result.exit_status == 0
                
                # Results remain on pod at /root/nex_ml/jobs/{job_id}/output
                # (MinIO not accessible from external pod)
                
                # Parse metrics from output
                metrics = {}
                if "--- METRICS JSON ---" in output:
                    import json
                    json_start = output.find("--- METRICS JSON ---")
                    json_str = output[json_start + 20:].strip()
                    try:
                        metrics = json.loads(json_str)
                    except:
                        pass
                
                return {
                    "status": "success" if success else "failed",
                    "job_id": job_id,
                    "pod_id": pod_id,
                    "pod_name": pod_name,
                    "gpu_type": gpu_type,
                    "horizon": horizon,
                    "metrics": metrics,
                    "output_prefix": f"jobs/{job_id}/output",
                    "output": output[-2000:] if len(output) > 2000 else output,  # Last 2000 chars
                    "exit_code": result.exit_status
                }
                
        except asyncssh.Error as e:
            logger.error(f"SSH error during forecast: {e}")
            return {"status": "error", "error": f"SSH error: {str(e)}"}
        except Exception as e:
            logger.error(f"Forecast failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_jobs(self) -> dict:
        """
        List all forecast jobs on the pod.
        
        Returns:
            Dict with jobs list and metadata
        """
        import asyncssh
        import os
        import json
        
        # Find running pod
        pod_id = self.pod_id or self._auto_detected_pod_id
        
        if not pod_id:
            pod_id = await self._find_running_pod()
            if pod_id:
                self._auto_detected_pod_id = pod_id
        
        if not pod_id:
            return {"jobs": [], "error": "No running pod found"}
        
        # Get pod SSH details
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                machine { gpuDisplayName }
                runtime {
                    ports { ip privatePort publicPort }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod:
                return {"jobs": [], "error": f"Pod {pod_id} not found"}
            
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                return {"jobs": [], "error": "Pod does not have SSH access"}
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                # List job directories
                list_result = await conn.run(
                    "ls -1 /root/nex_ml/jobs/ 2>/dev/null || echo ''",
                    check=False
                )
                
                job_dirs = [d.strip() for d in list_result.stdout.split('\n') if d.strip()]
                
                jobs = []
                for job_id in job_dirs:
                    job_info = {"job_id": job_id}
                    
                    # Check for metrics.json
                    metrics_result = await conn.run(
                        f"cat /root/nex_ml/jobs/{job_id}/output/metrics.json 2>/dev/null || echo '{{}}'",
                        check=False
                    )
                    try:
                        metrics = json.loads(metrics_result.stdout.strip())
                        job_info["metrics"] = metrics
                        job_info["status"] = "completed" if metrics else "unknown"
                        job_info["timestamp"] = metrics.get("timestamp", "")
                        job_info["mae"] = metrics.get("mae")
                        job_info["rmse"] = metrics.get("rmse")
                        job_info["training_time"] = metrics.get("training_time_seconds")
                    except:
                        job_info["status"] = "unknown"
                        job_info["metrics"] = {}
                    
                    # Check for output files
                    files_result = await conn.run(
                        f"ls -1 /root/nex_ml/jobs/{job_id}/output/ 2>/dev/null || echo ''",
                        check=False
                    )
                    job_info["output_files"] = [f.strip() for f in files_result.stdout.split('\n') if f.strip()]
                    
                    jobs.append(job_info)
                
                # Sort by timestamp (newest first)
                jobs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                return {
                    "jobs": jobs,
                    "pod_id": pod_id,
                    "pod_name": pod.get("name", pod_id),
                    "gpu_type": pod.get("machine", {}).get("gpuDisplayName", "Unknown"),
                    "count": len(jobs)
                }
                
        except asyncssh.Error as e:
            logger.error(f"SSH error listing jobs: {e}")
            return {"jobs": [], "error": f"SSH error: {str(e)}"}
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return {"jobs": [], "error": str(e)}
    
    async def get_job_details(self, job_id: str) -> dict:
        """
        Get detailed information about a specific job including logs.
        
        Args:
            job_id: The job ID (e.g., "forecast_64aa0d58")
            
        Returns:
            Dict with job details, logs, and output files
        """
        import asyncssh
        import os
        import json
        
        # Find running pod
        pod_id = self.pod_id or self._auto_detected_pod_id
        
        if not pod_id:
            pod_id = await self._find_running_pod()
            if pod_id:
                self._auto_detected_pod_id = pod_id
        
        if not pod_id:
            return {"error": "No running pod found"}
        
        # Get pod SSH details
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                machine { gpuDisplayName }
                runtime {
                    ports { ip privatePort publicPort }
                }
            }
        }
        """
        
        try:
            result = await self._graphql_query(query, {"podId": pod_id})
            pod = result.get("pod", {})
            
            if not pod:
                return {"error": f"Pod {pod_id} not found"}
            
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            
            ssh_ip = None
            ssh_port = None
            for port_info in ports:
                if port_info.get("privatePort") == 22:
                    ssh_ip = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break
            
            if not ssh_ip or not ssh_port:
                return {"error": "Pod does not have SSH access"}
            
            # Get SSH key
            ssh_key_path = getattr(settings, 'runpod_ssh_key_path', None)
            if not ssh_key_path:
                common_paths = [
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_rsa'),
                    '/root/.ssh/id_ed25519',
                    '/root/.ssh/id_rsa',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        ssh_key_path = path
                        break
            
            connect_kwargs = {
                'host': ssh_ip,
                'port': ssh_port,
                'username': 'root',
                'known_hosts': None,
                'connect_timeout': 30,
            }
            
            if ssh_key_path:
                connect_kwargs['client_keys'] = [ssh_key_path]
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                job_path = f"/root/nex_ml/jobs/{job_id}"
                
                # Check if job exists
                check_result = await conn.run(f"test -d {job_path} && echo 'exists'", check=False)
                if "exists" not in check_result.stdout:
                    return {"error": f"Job {job_id} not found on pod"}
                
                job_details = {
                    "job_id": job_id,
                    "pod_id": pod_id,
                    "pod_name": pod.get("name", pod_id),
                    "gpu_type": pod.get("machine", {}).get("gpuDisplayName", "Unknown")
                }
                
                # Get metrics
                metrics_result = await conn.run(
                    f"cat {job_path}/output/metrics.json 2>/dev/null || echo '{{}}'",
                    check=False
                )
                try:
                    job_details["metrics"] = json.loads(metrics_result.stdout.strip())
                except:
                    job_details["metrics"] = {}
                
                # Get feature importance
                fi_result = await conn.run(
                    f"cat {job_path}/output/feature_importance.csv 2>/dev/null || echo ''",
                    check=False
                )
                job_details["feature_importance"] = fi_result.stdout.strip()
                
                # Get forecasts (first 20 rows)
                forecasts_result = await conn.run(
                    f"head -21 {job_path}/output/forecasts.csv 2>/dev/null || echo ''",
                    check=False
                )
                job_details["forecasts_preview"] = forecasts_result.stdout.strip()
                
                # List all output files with sizes
                files_result = await conn.run(
                    f"ls -lh {job_path}/output/ 2>/dev/null | tail -n +2",
                    check=False
                )
                
                output_files = []
                for line in files_result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            output_files.append({
                                "name": parts[-1],
                                "size": parts[4],
                                "modified": f"{parts[5]} {parts[6]} {parts[7]}"
                            })
                
                job_details["output_files"] = output_files
                
                # List input files
                input_result = await conn.run(
                    f"ls -lh {job_path}/input/ 2>/dev/null | tail -n +2",
                    check=False
                )
                
                input_files = []
                for line in input_result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            input_files.append({
                                "name": parts[-1],
                                "size": parts[4]
                            })
                
                job_details["input_files"] = input_files
                
                return job_details
                
        except asyncssh.Error as e:
            logger.error(f"SSH error getting job details: {e}")
            return {"error": f"SSH error: {str(e)}"}
        except Exception as e:
            logger.error(f"Failed to get job details: {e}")
            return {"error": str(e)}


# Factory function to create adapter
def create_runpod_adapter() -> RunPodAdapter:
    """Create a RunPod adapter instance."""
    return RunPodAdapter()
