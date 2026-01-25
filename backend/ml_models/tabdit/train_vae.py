#!/usr/bin/env python3
"""Standalone VAE training script for GPU execution.

This script is designed to run on a GPU pod (e.g., RunPod) for training
the VAE phase of TabDiT models.

Usage:
    python train_vae.py \
        --data-uri s3://bucket/datasets/model_id/source.parquet \
        --output-dir s3://bucket/models/tabdit/model_id/vae \
        --config config.json

Environment variables:
    AWS_ACCESS_KEY_ID: S3 access key
    AWS_SECRET_ACCESS_KEY: S3 secret key
    S3_ENDPOINT_URL: S3 endpoint (for MinIO)
    WANDB_API_KEY: WandB API key (optional)
"""

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

import boto3
import numpy as np
import pandas as pd
import torch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domains.synthetic.synthesizers.tabdit import (
    TabularTokenizer,
    TabularVAE,
    VAETrainer,
    VAEConfig,
    TokenizerConfig,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_s3_client():
    """Get S3 client with optional custom endpoint."""
    endpoint_url = os.environ.get("S3_ENDPOINT_URL")

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def parse_s3_uri(uri: str) -> tuple:
    """Parse S3 URI into bucket and key."""
    if not uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {uri}")

    path = uri[5:]  # Remove s3://
    bucket, key = path.split("/", 1)
    return bucket, key


def download_data(s3_uri: str, local_path: Path) -> None:
    """Download data from S3."""
    s3 = get_s3_client()
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Downloading {s3_uri} to {local_path}")
    s3.download_file(bucket, key, str(local_path))


def upload_directory(local_dir: Path, s3_uri: str) -> None:
    """Upload directory to S3."""
    s3 = get_s3_client()
    bucket, prefix = parse_s3_uri(s3_uri)

    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            key = f"{prefix}/{file_path.relative_to(local_dir)}"
            logger.info(f"Uploading {file_path} to s3://{bucket}/{key}")
            s3.upload_file(str(file_path), bucket, key)


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file or S3."""
    if config_path.startswith("s3://"):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            download_data(config_path, Path(f.name))
            with open(f.name, "r") as cf:
                return json.load(cf)
    else:
        with open(config_path, "r") as f:
            return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Train TabDiT VAE")
    parser.add_argument(
        "--data-uri",
        required=True,
        help="S3 URI to training data (parquet)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="S3 URI for output checkpoints",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config JSON (local or S3)",
    )
    parser.add_argument(
        "--resume-from",
        default=None,
        help="S3 URI to checkpoint to resume from",
    )
    parser.add_argument(
        "--local-dir",
        default="/tmp/tabdit_vae",
        help="Local working directory",
    )
    parser.add_argument(
        "--wandb-project",
        default=None,
        help="WandB project name for tracking",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Model ID for tracking",
    )

    args = parser.parse_args()

    # Setup local directories
    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    data_path = local_dir / "data.parquet"
    checkpoint_dir = local_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)

    # Load config
    config = {}
    if args.config:
        config = load_config(args.config)
        logger.info(f"Loaded config: {config}")

    vae_config = VAEConfig.from_dict(config.get("vae", {}))
    tokenizer_config = TokenizerConfig.from_dict(config.get("tokenizer", {}))

    # Download training data
    download_data(args.data_uri, data_path)
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")

    # Setup WandB
    if args.wandb_project:
        try:
            import wandb
            wandb.init(
                project=args.wandb_project,
                name=f"vae-{args.model_id}" if args.model_id else "vae-training",
                config={
                    "model_id": args.model_id,
                    "phase": "vae",
                    "vae_config": vae_config.to_dict(),
                    "tokenizer_config": tokenizer_config.to_dict(),
                    "num_rows": len(df),
                    "num_columns": len(df.columns),
                },
            )
        except ImportError:
            logger.warning("WandB not installed, skipping tracking")

    # Fit tokenizer
    logger.info("Fitting tokenizer...")
    tokenizer = TabularTokenizer(tokenizer_config)
    tokenizer.fit(df)
    tokenizer.save(checkpoint_dir / "tokenizer.json")
    logger.info(f"Tokenizer input_dim: {tokenizer.input_dim}")

    # Transform data
    logger.info("Transforming data...")
    train_data = tokenizer.transform(df)

    # Split for validation
    val_split = 0.1
    n_val = int(len(train_data) * val_split)
    indices = np.random.permutation(len(train_data))
    val_data = train_data[indices[:n_val]]
    train_data = train_data[indices[n_val:]]

    logger.info(f"Train samples: {len(train_data)}, Val samples: {len(val_data)}")

    # Initialize VAE
    logger.info("Initializing VAE...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    vae = TabularVAE(input_dim=tokenizer.input_dim, config=vae_config)
    trainer = VAETrainer(model=vae, config=vae_config, device=device)

    # Resume if checkpoint provided
    if args.resume_from:
        resume_path = checkpoint_dir / "resume.pt"
        download_data(args.resume_from, resume_path)
        trainer.load_checkpoint(resume_path)
        logger.info(f"Resumed from {args.resume_from}")

    # Define progress callback
    def progress_callback(epoch, total_epochs, train_loss, val_loss):
        progress = (epoch + 1) / total_epochs * 100
        logger.info(
            f"Epoch {epoch+1}/{total_epochs} ({progress:.1f}%) - "
            f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f if val_loss else 'N/A'}"
        )

        # Log to WandB if available
        if args.wandb_project:
            try:
                import wandb
                wandb.log({
                    "epoch": epoch + 1,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "progress": progress,
                })
            except Exception:
                pass

    # Train
    logger.info(f"Starting VAE training for {vae_config.epochs} epochs...")
    result = trainer.train(
        train_data=train_data,
        val_data=val_data,
        checkpoint_dir=str(checkpoint_dir),
        progress_callback=progress_callback,
    )

    # Save final metrics
    metrics = {
        "final_loss": result["history"]["train_loss"][-1],
        "best_loss": result["best_loss"],
        "epochs_completed": result["final_epoch"],
        "recon_loss": result["history"]["recon_loss"][-1],
        "kl_loss": result["history"]["kl_loss"][-1],
        "input_dim": tokenizer.input_dim,
        "latent_dim": vae_config.latent_dim,
    }

    with open(checkpoint_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Training completed: {metrics}")

    # Upload results to S3
    logger.info(f"Uploading results to {args.output_dir}...")
    upload_directory(checkpoint_dir, args.output_dir)

    # Finish WandB
    if args.wandb_project:
        try:
            import wandb
            wandb.finish()
        except Exception:
            pass

    logger.info("VAE training complete!")


if __name__ == "__main__":
    main()
