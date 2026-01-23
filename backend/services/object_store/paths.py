"""Object store path helpers for consistent URI generation."""


class ObjectStorePaths:
    """
    Helper class for generating consistent object store paths.
    
    Layout:
        nex-data/
        ├── datasets/{dataset_id}/{version}/
        │   ├── manifest.json
        │   └── raw/...
        ├── runs/{run_id}/
        │   ├── logs.txt
        │   └── outputs/
        │       ├── run_manifest.json
        │       ├── metrics.json
        │       └── {artifacts}
        └── assets/{asset_id}/
            ├── manifest.json
            └── data/...
    """
    
    # ========================================
    # Dataset Paths
    # ========================================
    
    @staticmethod
    def dataset_root(dataset_id: str, version: str) -> str:
        """Root path for a dataset version."""
        return f"datasets/{dataset_id}/{version}"
    
    @staticmethod
    def dataset_manifest(dataset_id: str, version: str) -> str:
        """Path to dataset manifest.json."""
        return f"datasets/{dataset_id}/{version}/manifest.json"
    
    @staticmethod
    def dataset_raw(dataset_id: str, version: str) -> str:
        """Path to raw data folder."""
        return f"datasets/{dataset_id}/{version}/raw"
    
    @staticmethod
    def dataset_raw_file(dataset_id: str, version: str, filename: str) -> str:
        """Path to a specific raw file."""
        return f"datasets/{dataset_id}/{version}/raw/{filename}"
    
    @staticmethod
    def dataset_curated(dataset_id: str, version: str) -> str:
        """Path to curated data folder."""
        return f"datasets/{dataset_id}/{version}/curated"
    
    # ========================================
    # Run Paths
    # ========================================
    
    @staticmethod
    def run_root(run_id: str) -> str:
        """Root path for a model run."""
        return f"runs/{run_id}"
    
    @staticmethod
    def run_logs(run_id: str) -> str:
        """Path to run logs file."""
        return f"runs/{run_id}/logs.txt"
    
    @staticmethod
    def run_outputs(run_id: str) -> str:
        """Path to run outputs folder."""
        return f"runs/{run_id}/outputs"
    
    @staticmethod
    def run_manifest(run_id: str) -> str:
        """Path to run output manifest."""
        return f"runs/{run_id}/outputs/run_manifest.json"
    
    @staticmethod
    def run_metrics(run_id: str) -> str:
        """Path to run metrics file."""
        return f"runs/{run_id}/outputs/metrics.json"
    
    @staticmethod
    def run_artifact(run_id: str, artifact_name: str) -> str:
        """Path to a specific run artifact."""
        return f"runs/{run_id}/outputs/{artifact_name}"
    
    # ========================================
    # Asset Paths
    # ========================================
    
    @staticmethod
    def asset_root(asset_id: str) -> str:
        """Root path for a derived asset."""
        return f"assets/{asset_id}"
    
    @staticmethod
    def asset_manifest(asset_id: str) -> str:
        """Path to asset manifest."""
        return f"assets/{asset_id}/manifest.json"
    
    @staticmethod
    def asset_metadata(asset_id: str) -> str:
        """Path to asset metadata file."""
        return f"assets/{asset_id}/metadata.json"
    
    @staticmethod
    def asset_data(asset_id: str) -> str:
        """Path to asset data folder."""
        return f"assets/{asset_id}/data"
    
    @staticmethod
    def asset_data_file(asset_id: str, filename: str) -> str:
        """Path to a specific asset data file."""
        return f"assets/{asset_id}/data/{filename}"
    
    # ========================================
    # Manifest Schemas
    # ========================================
    
    @staticmethod
    def create_dataset_manifest(
        dataset_id: str,
        version: str,
        files: list[dict],
        schema: dict | None = None,
        description: str | None = None
    ) -> dict:
        """
        Create a dataset manifest structure.
        
        Args:
            dataset_id: Dataset identifier
            version: Version label
            files: List of file info dicts with 'path', 'bytes', 'sha256'
            schema: Optional schema definition
            description: Optional description
            
        Returns:
            Manifest dictionary
        """
        from datetime import datetime
        return {
            "dataset_id": dataset_id,
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "description": description,
            "files": files,
            "schema": schema,
            "total_files": len(files),
            "total_bytes": sum(f.get('bytes', 0) for f in files)
        }
    
    @staticmethod
    def create_run_manifest(
        run_id: str,
        outputs: list[dict],
        metrics: dict | None = None
    ) -> dict:
        """
        Create a run output manifest structure.
        
        Args:
            run_id: Run identifier
            outputs: List of output info dicts with 'name', 'path', 'type'
            metrics: Optional metrics dictionary
            
        Returns:
            Manifest dictionary
        """
        from datetime import datetime
        return {
            "run_id": run_id,
            "completed_at": datetime.utcnow().isoformat(),
            "outputs": outputs,
            "metrics": metrics or {}
        }
    
    @staticmethod
    def create_asset_manifest(
        asset_id: str,
        source_run_id: str,
        asset_type: str,
        artifacts: list[dict]
    ) -> dict:
        """
        Create an asset manifest structure.
        
        Args:
            asset_id: Asset identifier
            source_run_id: Source run identifier
            asset_type: 'temporal' or 'permanent'
            artifacts: List of artifact info dicts
            
        Returns:
            Manifest dictionary
        """
        from datetime import datetime
        return {
            "asset_id": asset_id,
            "source_run_id": source_run_id,
            "type": asset_type,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": artifacts
        }
    
    # ========================================
    # Synthetic Data Paths
    # ========================================
    
    @staticmethod
    def synthetic_root(dataset_id: str) -> str:
        """Root path for a synthetic dataset."""
        return f"synthetic/{dataset_id}"
    
    @staticmethod
    def synthetic_data(dataset_id: str, format: str = "parquet") -> str:
        """Path to synthetic data file."""
        return f"synthetic/{dataset_id}/data.{format}"
    
    @staticmethod
    def synthetic_manifest(dataset_id: str) -> str:
        """Path to synthetic dataset manifest."""
        return f"synthetic/{dataset_id}/manifest.json"
    
    @staticmethod
    def synthetic_quality_report(dataset_id: str) -> str:
        """Path to quality report JSON."""
        return f"synthetic/{dataset_id}/quality_report.json"
    
    @staticmethod
    def synthetic_source_sample(dataset_id: str) -> str:
        """Path to source data sample (for quality comparisons)."""
        return f"synthetic/{dataset_id}/source_sample.parquet"
    
    @staticmethod
    def create_synthetic_manifest(
        dataset_id: str,
        job_id: str,
        num_rows: int,
        num_columns: int,
        columns: list[dict],
        synthesizer_type: str,
        file_size_bytes: int | None = None,
        quality_score: float | None = None,
    ) -> dict:
        """
        Create a synthetic dataset manifest structure.
        
        Args:
            dataset_id: Synthetic dataset ID
            job_id: Generation job ID
            num_rows: Number of rows generated
            num_columns: Number of columns
            columns: Column metadata list
            synthesizer_type: Type of synthesizer used
            file_size_bytes: Optional file size
            quality_score: Optional quality score
            
        Returns:
            Manifest dictionary
        """
        from datetime import datetime
        return {
            "dataset_id": dataset_id,
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat(),
            "synthesizer_type": synthesizer_type,
            "num_rows": num_rows,
            "num_columns": num_columns,
            "columns": columns,
            "file_size_bytes": file_size_bytes,
            "quality_score": quality_score,
        }
