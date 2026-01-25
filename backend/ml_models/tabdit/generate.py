#!/usr/bin/env python3
"""Batch generation script for TabDiT models.

This script generates synthetic data using a trained TabDiT model.
Can run on GPU for fast generation or CPU for smaller batches.

Usage:
    python generate.py \
        --vae-checkpoint s3://bucket/models/tabdit/model_id/vae/best.pt \
        --diffusion-checkpoint s3://bucket/models/tabdit/model_id/diffusion/best.pt \
        --tokenizer s3://bucket/models/tabdit/model_id/vae/tokenizer.json \
        --output-uri s3://bucket/synthetic/model_id/output.parquet \
        --num-rows 10000
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
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domains.synthetic.synthesizers.tabdit import (
    TabularTokenizer,
    load_vae_from_checkpoint,
    load_diffusion_from_checkpoint,
    DDIMScheduler,
    DiffusionConfig,
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

    path = uri[5:]
    bucket, key = path.split("/", 1)
    return bucket, key


def download_file(s3_uri: str, local_path: Path) -> None:
    """Download file from S3."""
    s3 = get_s3_client()
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Downloading {s3_uri} to {local_path}")
    s3.download_file(bucket, key, str(local_path))


def upload_file(local_path: Path, s3_uri: str) -> None:
    """Upload file to S3."""
    s3 = get_s3_client()
    bucket, key = parse_s3_uri(s3_uri)

    logger.info(f"Uploading {local_path} to {s3_uri}")
    s3.upload_file(str(local_path), bucket, key)


def generate_batch(
    diffusion: "DiffusionTransformer",
    vae: "TabularVAE",
    scheduler: DDIMScheduler,
    batch_size: int,
    device: torch.device,
) -> np.ndarray:
    """Generate a batch of synthetic samples.

    Args:
        diffusion: Diffusion model
        vae: VAE model (for decoding)
        scheduler: Noise scheduler
        batch_size: Number of samples
        device: Compute device

    Returns:
        Decoded samples as numpy array
    """
    latent_dim = vae.latent_dim

    # Sample random noise
    latents = torch.randn(batch_size, latent_dim, device=device)

    # Iterative denoising
    for t in scheduler.timesteps:
        t_batch = torch.full(
            (batch_size,),
            t.item(),
            device=device,
            dtype=torch.float,
        )

        # Predict noise
        with torch.no_grad():
            noise_pred = diffusion(latents, t_batch)

        # Denoise step
        latents, _ = scheduler.step(
            noise_pred,
            t.item(),
            latents,
            eta=0.0,  # DDIM deterministic
        )

    # Decode latents to tabular features
    with torch.no_grad():
        decoded = vae.decode(latents)

    return decoded.cpu().numpy()


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data with TabDiT")
    parser.add_argument(
        "--vae-checkpoint",
        required=True,
        help="S3 URI or local path to VAE checkpoint",
    )
    parser.add_argument(
        "--diffusion-checkpoint",
        required=True,
        help="S3 URI or local path to diffusion checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        required=True,
        help="S3 URI or local path to tokenizer JSON",
    )
    parser.add_argument(
        "--output-uri",
        required=True,
        help="S3 URI or local path for output (parquet)",
    )
    parser.add_argument(
        "--num-rows",
        type=int,
        default=1000,
        help="Number of rows to generate",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Batch size for generation",
    )
    parser.add_argument(
        "--inference-steps",
        type=int,
        default=50,
        help="Number of denoising steps",
    )
    parser.add_argument(
        "--local-dir",
        default="/tmp/tabdit_generate",
        help="Local working directory",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device: auto, cuda, or cpu",
    )

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed is not None:
        torch.manual_seed(args.seed)
        np.random.seed(args.seed)

    # Setup local directory
    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    # Download checkpoints if from S3
    vae_path = local_dir / "vae_checkpoint.pt"
    diffusion_path = local_dir / "diffusion_checkpoint.pt"
    tokenizer_path = local_dir / "tokenizer.json"

    if args.vae_checkpoint.startswith("s3://"):
        download_file(args.vae_checkpoint, vae_path)
    else:
        vae_path = Path(args.vae_checkpoint)

    if args.diffusion_checkpoint.startswith("s3://"):
        download_file(args.diffusion_checkpoint, diffusion_path)
    else:
        diffusion_path = Path(args.diffusion_checkpoint)

    if args.tokenizer.startswith("s3://"):
        download_file(args.tokenizer, tokenizer_path)
    else:
        tokenizer_path = Path(args.tokenizer)

    # Setup device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    logger.info(f"Using device: {device}")

    # Load models
    logger.info("Loading models...")
    tokenizer = TabularTokenizer.load(tokenizer_path)
    vae = load_vae_from_checkpoint(vae_path, device=str(device))
    diffusion = load_diffusion_from_checkpoint(diffusion_path, device=str(device), use_ema=True)

    vae.eval()
    diffusion.eval()

    logger.info(f"VAE latent_dim: {vae.latent_dim}")
    logger.info(f"Tokenizer input_dim: {tokenizer.input_dim}")

    # Setup scheduler
    scheduler = DDIMScheduler(
        num_train_timesteps=1000,
        num_inference_steps=args.inference_steps,
        beta_schedule="cosine",
    )
    scheduler.set_timesteps(args.inference_steps)

    # Generate in batches
    logger.info(f"Generating {args.num_rows} rows in batches of {args.batch_size}...")
    all_samples = []

    num_batches = (args.num_rows + args.batch_size - 1) // args.batch_size

    with torch.no_grad():
        for i in tqdm(range(num_batches), desc="Generating"):
            batch_num = min(args.batch_size, args.num_rows - i * args.batch_size)

            samples = generate_batch(
                diffusion=diffusion,
                vae=vae,
                scheduler=scheduler,
                batch_size=batch_num,
                device=device,
            )

            all_samples.append(samples)

    # Concatenate all batches
    all_samples = np.concatenate(all_samples, axis=0)
    logger.info(f"Generated {len(all_samples)} samples")

    # Inverse transform to DataFrame
    logger.info("Converting to DataFrame...")
    synthetic_df = tokenizer.inverse_transform(all_samples)

    # Save output
    output_path = local_dir / "output.parquet"
    synthetic_df.to_parquet(output_path, index=False)
    logger.info(f"Saved to {output_path}")

    # Upload if S3 URI
    if args.output_uri.startswith("s3://"):
        upload_file(output_path, args.output_uri)
    else:
        # Copy to local output path
        import shutil
        shutil.copy(output_path, args.output_uri)

    # Print summary
    logger.info("=" * 50)
    logger.info("Generation Summary:")
    logger.info(f"  Rows generated: {len(synthetic_df)}")
    logger.info(f"  Columns: {len(synthetic_df.columns)}")
    logger.info(f"  Inference steps: {args.inference_steps}")
    logger.info(f"  Output: {args.output_uri}")
    logger.info("=" * 50)

    logger.info("Generation complete!")


if __name__ == "__main__":
    main()
