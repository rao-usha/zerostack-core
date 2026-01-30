"""Tests for TabDiT (Tabular Diffusion Transformer) synthesizer.

Note: Uses direct module imports to avoid loading database dependencies.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import sys
import importlib.util
from pathlib import Path
from unittest import mock

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent
TABDIT_DIR = BACKEND_DIR / "domains" / "synthetic" / "synthesizers" / "tabdit"


def load_module_with_package(name: str, filepath: Path, package_name: str = None):
    """Load a module directly from a file path, handling relative imports."""
    spec = importlib.util.spec_from_file_location(
        name,
        filepath,
        submodule_search_locations=[str(filepath.parent)] if package_name else None
    )
    module = importlib.util.module_from_spec(spec)
    if package_name:
        module.__package__ = package_name
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# First, load config (no relative imports)
config_module = load_module_with_package(
    "domains.synthetic.synthesizers.tabdit.config",
    TABDIT_DIR / "config.py",
    "domains.synthetic.synthesizers.tabdit"
)
sys.modules[".config"] = config_module  # For relative imports

TabDiTConfig = config_module.TabDiTConfig
VAEConfig = config_module.VAEConfig
DiffusionConfig = config_module.DiffusionConfig
TokenizerConfig = config_module.TokenizerConfig

# Now load tokenizer with config available
tokenizer_module = load_module_with_package(
    "domains.synthetic.synthesizers.tabdit.tokenizer",
    TABDIT_DIR / "tokenizer.py",
    "domains.synthetic.synthesizers.tabdit"
)
TabularTokenizer = tokenizer_module.TabularTokenizer
ColumnInfo = tokenizer_module.ColumnInfo

# Check if PyTorch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

# Conditionally load PyTorch-dependent modules
if TORCH_AVAILABLE:
    vae_module = load_module_with_package(
        "domains.synthetic.synthesizers.tabdit.vae",
        TABDIT_DIR / "vae.py",
        "domains.synthetic.synthesizers.tabdit"
    )
    diffusion_module = load_module_with_package(
        "domains.synthetic.synthesizers.tabdit.diffusion",
        TABDIT_DIR / "diffusion.py",
        "domains.synthetic.synthesizers.tabdit"
    )
    scheduler_module = load_module_with_package(
        "domains.synthetic.synthesizers.tabdit.scheduler",
        TABDIT_DIR / "scheduler.py",
        "domains.synthetic.synthesizers.tabdit"
    )

    TabularVAE = vae_module.TabularVAE
    VAETrainer = vae_module.VAETrainer
    VAELoss = vae_module.VAELoss
    load_vae_from_checkpoint = vae_module.load_vae_from_checkpoint

    DiffusionTransformer = diffusion_module.DiffusionTransformer
    DiffusionTrainer = diffusion_module.DiffusionTrainer
    load_diffusion_from_checkpoint = diffusion_module.load_diffusion_from_checkpoint

    NoiseScheduler = scheduler_module.NoiseScheduler
    DDIMScheduler = scheduler_module.DDIMScheduler
    create_scheduler = scheduler_module.create_scheduler


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Create sample mixed-type data for testing."""
    np.random.seed(42)
    n = 200

    return pd.DataFrame({
        'age': np.random.randint(18, 80, n),
        'income': np.random.normal(50000, 15000, n).clip(20000, 150000),
        'category': np.random.choice(['A', 'B', 'C'], n, p=[0.5, 0.3, 0.2]),
        'score': np.random.uniform(0, 100, n),
    })


@pytest.fixture
def small_data():
    """Small dataset for quick tests."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame({
        'x': np.random.normal(0, 1, n),
        'y': np.random.normal(5, 2, n),
        'label': np.random.choice(['yes', 'no'], n),
    })


@pytest.fixture
def data_with_missing():
    """Dataset with missing values."""
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        'numeric': np.random.normal(0, 1, n),
        'category': np.random.choice(['A', 'B', 'C'], n),
    })

    # Add some missing values
    df.loc[np.random.choice(n, 10, replace=False), 'numeric'] = np.nan
    df.loc[np.random.choice(n, 5, replace=False), 'category'] = None

    return df


# ============================================================================
# Configuration Tests
# ============================================================================

class TestTabDiTConfig:
    """Tests for configuration dataclasses."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TabDiTConfig()

        assert config.vae.latent_dim == 128
        assert config.vae.epochs == 100
        assert config.diffusion.num_layers == 6
        assert config.diffusion.num_train_timesteps == 1000
        assert config.device == "auto"

    def test_small_config(self):
        """Test small preset configuration."""
        config = TabDiTConfig.small()

        assert config.vae.latent_dim == 64
        assert config.vae.epochs == 50
        assert config.diffusion.num_layers == 4
        assert config.diffusion.num_inference_steps == 25

    def test_large_config(self):
        """Test large preset configuration."""
        config = TabDiTConfig.large()

        assert config.vae.latent_dim == 256
        assert config.diffusion.num_layers == 8
        assert config.diffusion.num_inference_steps == 100

    def test_config_serialization(self):
        """Test config to_dict and from_dict."""
        config = TabDiTConfig()
        config_dict = config.to_dict()

        assert 'vae' in config_dict
        assert 'diffusion' in config_dict
        assert 'tokenizer' in config_dict

        restored = TabDiTConfig.from_dict(config_dict)

        assert restored.vae.latent_dim == config.vae.latent_dim
        assert restored.diffusion.num_layers == config.diffusion.num_layers

    def test_vae_config(self):
        """Test VAE-specific configuration."""
        config = VAEConfig(
            latent_dim=64,
            encoder_layers=[256, 128],
            kl_weight=0.2,
        )

        assert config.latent_dim == 64
        assert config.encoder_layers == [256, 128]
        assert config.kl_weight == 0.2
        assert config.kl_annealing is True  # Default

    def test_diffusion_config(self):
        """Test Diffusion-specific configuration."""
        config = DiffusionConfig(
            num_layers=4,
            hidden_dim=128,
            beta_schedule="linear",
        )

        assert config.num_layers == 4
        assert config.hidden_dim == 128
        assert config.beta_schedule == "linear"


# ============================================================================
# Tokenizer Tests
# ============================================================================

class TestTabularTokenizer:
    """Tests for tabular data tokenizer."""

    def test_fit(self, small_data):
        """Test tokenizer fitting."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        assert tokenizer.is_fitted
        assert tokenizer.input_dim > 0
        assert len(tokenizer.column_info) == 3

    def test_transform(self, small_data):
        """Test data transformation."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        transformed = tokenizer.transform(small_data)

        assert isinstance(transformed, np.ndarray)
        assert transformed.shape[0] == len(small_data)
        assert transformed.shape[1] == tokenizer.input_dim
        assert transformed.dtype == np.float32

    def test_inverse_transform(self, small_data):
        """Test inverse transformation."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        transformed = tokenizer.transform(small_data)
        reconstructed = tokenizer.inverse_transform(transformed)

        assert isinstance(reconstructed, pd.DataFrame)
        assert len(reconstructed) == len(small_data)
        assert list(reconstructed.columns) == list(small_data.columns)

        # Check numeric columns are close
        np.testing.assert_allclose(
            reconstructed['x'].values,
            small_data['x'].values,
            rtol=0.01,
            atol=0.01,
        )

    def test_numeric_column_analysis(self, small_data):
        """Test numeric column handling."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        col_info = tokenizer.column_info['x']

        assert col_info.dtype == "numeric"
        assert col_info.mean is not None
        assert col_info.std is not None
        assert col_info.min_val is not None
        assert col_info.max_val is not None

    def test_categorical_column_analysis(self, small_data):
        """Test categorical column handling."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        col_info = tokenizer.column_info['label']

        assert col_info.dtype == "categorical"
        assert col_info.n_categories == 2
        assert 'yes' in col_info.categories
        assert 'no' in col_info.categories

    def test_missing_value_handling(self, data_with_missing):
        """Test handling of missing values."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(data_with_missing)

        col_info = tokenizer.column_info['numeric']
        assert col_info.has_missing is True

        transformed = tokenizer.transform(data_with_missing)
        assert not np.any(np.isnan(transformed))

    def test_save_and_load(self, small_data):
        """Test tokenizer serialization."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tokenizer.json"
            tokenizer.save(path)

            loaded = TabularTokenizer.load(path)

            assert loaded.is_fitted
            assert loaded.input_dim == tokenizer.input_dim

            # Transform should produce same results
            orig_transformed = tokenizer.transform(small_data)
            loaded_transformed = loaded.transform(small_data)

            np.testing.assert_array_almost_equal(
                orig_transformed,
                loaded_transformed,
            )

    def test_high_cardinality_truncation(self):
        """Test truncation of high-cardinality categorical columns."""
        np.random.seed(42)
        config = TokenizerConfig(max_cardinality=5)
        tokenizer = TabularTokenizer(config)

        # Create data with many categories
        df = pd.DataFrame({
            'category': [f"cat_{i % 20}" for i in range(100)]
        })

        tokenizer.fit(df)

        col_info = tokenizer.column_info['category']
        assert col_info.n_categories == 5


# ============================================================================
# PyTorch-Dependent Tests
# ============================================================================

@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestTabularVAE:
    """Tests for VAE model."""

    def test_forward_pass(self, small_data):
        """Test VAE forward pass."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        vae = TabularVAE(
            input_dim=tokenizer.input_dim,
            config=VAEConfig(latent_dim=32),
        )

        x = torch.FloatTensor(tokenizer.transform(small_data))
        recon, mu, logvar = vae(x)

        assert recon.shape == x.shape
        assert mu.shape == (len(small_data), 32)
        assert logvar.shape == (len(small_data), 32)

    def test_encode_decode(self, small_data):
        """Test VAE encoding and decoding."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        vae = TabularVAE(
            input_dim=tokenizer.input_dim,
            config=VAEConfig(latent_dim=32),
        )

        x = torch.FloatTensor(tokenizer.transform(small_data))

        # Encode
        z = vae.encode_to_latent(x, use_mean=True)
        assert z.shape == (len(small_data), 32)

        # Decode
        recon = vae.decode(z)
        assert recon.shape == x.shape

    def test_sample(self, small_data):
        """Test VAE sampling from prior."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        vae = TabularVAE(
            input_dim=tokenizer.input_dim,
            config=VAEConfig(latent_dim=32),
        )

        samples = vae.sample(50)
        assert samples.shape == (50, tokenizer.input_dim)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestVAETraining:
    """Tests for VAE training."""

    def test_train_epoch(self, small_data):
        """Test single training epoch."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        config = VAEConfig(
            latent_dim=16,
            encoder_layers=[32],
            decoder_layers=[32],
            batch_size=32,
        )
        vae = TabularVAE(input_dim=tokenizer.input_dim, config=config)
        trainer = VAETrainer(vae, config=config, device="cpu")

        train_data = tokenizer.transform(small_data)

        # Create dataloader manually for single epoch test
        train_tensor = torch.FloatTensor(train_data)
        train_dataset = torch.utils.data.TensorDataset(train_tensor)
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=32, shuffle=True, drop_last=True
        )

        metrics = trainer.train_epoch(train_loader)

        assert 'total_loss' in metrics
        assert 'recon_loss' in metrics
        assert 'kl_loss' in metrics
        assert metrics['total_loss'] > 0

    @pytest.mark.slow
    def test_full_training(self, small_data):
        """Test full VAE training loop (slow)."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        config = VAEConfig(
            latent_dim=16,
            encoder_layers=[32],
            decoder_layers=[32],
            epochs=5,
            batch_size=32,
            early_stopping_patience=10,
        )
        vae = TabularVAE(input_dim=tokenizer.input_dim, config=config)
        trainer = VAETrainer(vae, config=config, device="cpu")

        train_data = tokenizer.transform(small_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = trainer.train(
                train_data=train_data,
                checkpoint_dir=tmpdir,
            )

            assert 'history' in result
            assert len(result['history']['train_loss']) > 0
            assert result['final_epoch'] > 0

            # Check checkpoint was saved
            assert (Path(tmpdir) / "best.pt").exists()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestVAELoss:
    """Tests for VAE loss function."""

    def test_loss_computation(self):
        """Test VAE loss computation."""
        loss_fn = VAELoss(
            reconstruction_weight=1.0,
            kl_weight=0.1,
            kl_annealing=False,
        )

        batch_size = 32
        dim = 64
        latent_dim = 16

        recon = torch.randn(batch_size, dim)
        target = torch.randn(batch_size, dim)
        mu = torch.randn(batch_size, latent_dim)
        logvar = torch.randn(batch_size, latent_dim)

        total_loss, metrics = loss_fn(recon, target, mu, logvar)

        assert total_loss.item() > 0
        assert metrics['recon_loss'] > 0
        assert metrics['kl_loss'] >= 0

    def test_kl_annealing(self):
        """Test KL weight annealing."""
        loss_fn = VAELoss(
            kl_weight=0.1,
            kl_annealing=True,
            kl_anneal_epochs=10,
        )

        # At epoch 0, KL weight should be 0
        loss_fn.set_epoch(0)
        assert loss_fn.get_kl_weight() == 0.0

        # At epoch 5, should be halfway
        loss_fn.set_epoch(5)
        assert abs(loss_fn.get_kl_weight() - 0.05) < 0.01

        # At epoch 10+, should be full weight
        loss_fn.set_epoch(10)
        assert abs(loss_fn.get_kl_weight() - 0.1) < 0.01


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestDiffusionTransformer:
    """Tests for Diffusion Transformer model."""

    def test_forward_pass(self):
        """Test diffusion transformer forward pass."""
        config = DiffusionConfig(
            num_layers=2,
            hidden_dim=64,
            num_heads=4,
        )

        model = DiffusionTransformer(latent_dim=32, config=config)

        batch_size = 16
        latents = torch.randn(batch_size, 32)
        timesteps = torch.randint(0, 1000, (batch_size,)).float()

        output = model(latents, timesteps)

        assert output.shape == latents.shape

    def test_with_class_conditioning(self):
        """Test diffusion with class conditioning."""
        config = DiffusionConfig(
            num_layers=2,
            hidden_dim=64,
            num_heads=4,
            use_class_conditioning=True,
            num_classes=3,
        )

        model = DiffusionTransformer(latent_dim=32, config=config)

        batch_size = 16
        latents = torch.randn(batch_size, 32)
        timesteps = torch.randint(0, 1000, (batch_size,)).float()
        class_labels = torch.randint(0, 3, (batch_size,))

        output = model(latents, timesteps, class_labels)

        assert output.shape == latents.shape


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestNoiseScheduler:
    """Tests for noise scheduler."""

    def test_add_noise(self):
        """Test noise addition (forward diffusion)."""
        scheduler = DDIMScheduler(
            num_train_timesteps=1000,
            beta_schedule="cosine",
        )

        batch_size = 16
        dim = 32

        original = torch.randn(batch_size, dim)
        noise = torch.randn(batch_size, dim)
        timesteps = torch.randint(0, 1000, (batch_size,))

        noisy = scheduler.add_noise(original, noise, timesteps)

        assert noisy.shape == original.shape

    def test_step(self):
        """Test denoising step."""
        scheduler = DDIMScheduler(
            num_train_timesteps=1000,
            num_inference_steps=50,
            beta_schedule="cosine",
        )
        scheduler.set_timesteps(50)

        batch_size = 16
        dim = 32

        sample = torch.randn(batch_size, dim)
        model_output = torch.randn(batch_size, dim)

        prev_sample, pred_original = scheduler.step(
            model_output=model_output,
            timestep=500,
            sample=sample,
            eta=0.0,
        )

        assert prev_sample.shape == sample.shape
        assert pred_original.shape == sample.shape

    def test_timesteps(self):
        """Test timestep generation."""
        scheduler = DDIMScheduler(
            num_train_timesteps=1000,
            num_inference_steps=50,
        )
        scheduler.set_timesteps(50)

        timesteps = scheduler.timesteps

        assert len(timesteps) == 50
        assert timesteps[0].item() > timesteps[-1].item()  # Descending

    def test_beta_schedules(self):
        """Test different beta schedules."""
        for schedule in ["linear", "cosine", "squaredcos_cap_v2"]:
            scheduler = DDIMScheduler(
                num_train_timesteps=1000,
                beta_schedule=schedule,
            )

            assert len(scheduler.betas) == 1000
            assert (scheduler.betas > 0).all()
            assert (scheduler.betas < 1).all()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestDiffusionTraining:
    """Tests for diffusion training."""

    def test_train_epoch(self):
        """Test single diffusion training epoch."""
        config = DiffusionConfig(
            num_layers=2,
            hidden_dim=32,
            num_heads=2,
            batch_size=16,
        )

        model = DiffusionTransformer(latent_dim=16, config=config)
        scheduler = create_scheduler(config)
        trainer = DiffusionTrainer(model, scheduler, config=config, device="cpu")

        # Create dummy latent data
        train_data = np.random.randn(100, 16).astype(np.float32)
        train_tensor = torch.FloatTensor(train_data)
        train_dataset = torch.utils.data.TensorDataset(train_tensor)
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=16, shuffle=True, drop_last=True
        )

        metrics = trainer.train_epoch(train_loader)

        assert 'loss' in metrics
        assert 'lr' in metrics
        assert metrics['loss'] > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestCheckpointLoading:
    """Tests for checkpoint save/load functionality."""

    def test_vae_checkpoint(self, small_data):
        """Test VAE checkpoint save and load."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)

        config = VAEConfig(latent_dim=16, encoder_layers=[32], decoder_layers=[32])
        vae = TabularVAE(input_dim=tokenizer.input_dim, config=config)
        trainer = VAETrainer(vae, config=config, device="cpu")

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "vae.pt"
            trainer.save_checkpoint(checkpoint_path)

            # Load into new model
            loaded_vae = load_vae_from_checkpoint(checkpoint_path, device="cpu")

            assert loaded_vae.latent_dim == 16
            assert loaded_vae.input_dim == tokenizer.input_dim

    def test_diffusion_checkpoint(self):
        """Test diffusion checkpoint save and load."""
        config = DiffusionConfig(num_layers=2, hidden_dim=32, num_heads=2)
        model = DiffusionTransformer(latent_dim=16, config=config)
        scheduler = create_scheduler(config)
        trainer = DiffusionTrainer(model, scheduler, config=config, device="cpu")

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "diffusion.pt"
            trainer.save_checkpoint(checkpoint_path)

            # Load into new model
            loaded = load_diffusion_from_checkpoint(checkpoint_path, device="cpu")

            assert loaded.latent_dim == 16


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestTabDiTIntegration:
    """Integration tests for TabDiT pipeline."""

    def test_tokenizer_vae_pipeline(self, small_data):
        """Test tokenizer -> VAE pipeline."""
        # Tokenize
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)
        tokens = tokenizer.transform(small_data)

        # VAE encode/decode
        config = VAEConfig(latent_dim=16, encoder_layers=[32], decoder_layers=[32])
        vae = TabularVAE(input_dim=tokenizer.input_dim, config=config)

        x = torch.FloatTensor(tokens)
        recon, mu, logvar = vae(x)

        # Inverse transform
        reconstructed = tokenizer.inverse_transform(recon.detach().numpy())

        assert len(reconstructed) == len(small_data)
        assert list(reconstructed.columns) == list(small_data.columns)

    @pytest.mark.slow
    def test_minimal_training_pipeline(self, small_data):
        """Test minimal training pipeline (slow)."""
        tokenizer = TabularTokenizer()
        tokenizer.fit(small_data)
        tokens = tokenizer.transform(small_data)

        # Train VAE for a few epochs
        vae_config = VAEConfig(
            latent_dim=16,
            encoder_layers=[32],
            decoder_layers=[32],
            epochs=3,
            batch_size=32,
        )
        vae = TabularVAE(input_dim=tokenizer.input_dim, config=vae_config)
        vae_trainer = VAETrainer(vae, config=vae_config, device="cpu")

        vae_result = vae_trainer.train(tokens)
        assert vae_result['final_epoch'] > 0

        # Encode to latents
        vae.eval()
        with torch.no_grad():
            latents = vae.encode_to_latent(torch.FloatTensor(tokens), use_mean=False)
            latents = latents.numpy()

        # Train diffusion for a few epochs
        diff_config = DiffusionConfig(
            num_layers=2,
            hidden_dim=32,
            num_heads=2,
            epochs=3,
            batch_size=32,
        )
        diffusion = DiffusionTransformer(latent_dim=16, config=diff_config)
        scheduler = create_scheduler(diff_config)
        diff_trainer = DiffusionTrainer(diffusion, scheduler, config=diff_config, device="cpu")

        diff_result = diff_trainer.train(latents)
        assert diff_result['final_epoch'] > 0

        # Generate samples
        diffusion.eval()
        scheduler.set_timesteps(10)  # Few steps for testing

        with torch.no_grad():
            # Start from noise
            z = torch.randn(10, 16)

            for t in scheduler.timesteps:
                t_batch = torch.full((10,), t.item(), dtype=torch.float)
                noise_pred = diffusion(z, t_batch)
                z, _ = scheduler.step(noise_pred, t.item(), z, eta=0.0)

            # Decode
            decoded = vae.decode(z)

            # Inverse transform
            synthetic = tokenizer.inverse_transform(decoded.numpy())

        assert len(synthetic) == 10
        assert list(synthetic.columns) == list(small_data.columns)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_transform_before_fit(self, small_data):
        """Test that transform before fit raises error."""
        tokenizer = TabularTokenizer()

        with pytest.raises(RuntimeError, match="must be fitted"):
            tokenizer.transform(small_data)

    def test_inverse_transform_before_fit(self, small_data):
        """Test that inverse_transform before fit raises error."""
        tokenizer = TabularTokenizer()

        with pytest.raises(RuntimeError, match="must be fitted"):
            tokenizer.inverse_transform(np.random.randn(10, 5))
