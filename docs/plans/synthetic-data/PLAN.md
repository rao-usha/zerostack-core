# Synthetic Data Generation - Comprehensive Planning Document

## Executive Summary

Synthetic data generation is a critical capability for modern data platforms, enabling organizations to:
- Share data without privacy concerns
- Augment limited datasets for ML training
- Create realistic test environments
- Comply with data protection regulations (GDPR, CCPA, HIPAA)
- Accelerate development with production-like data

This document explores the landscape of synthetic data generation techniques, evaluates approaches for the NEX platform, and provides a detailed implementation roadmap.

---

## Table of Contents

1. [What is Synthetic Data?](#1-what-is-synthetic-data)
2. [Use Cases & Business Value](#2-use-cases--business-value)
3. [Technical Approaches](#3-technical-approaches)
4. [Privacy Considerations](#4-privacy-considerations)
5. [Quality Metrics & Validation](#5-quality-metrics--validation)
6. [Industry Tools & Libraries](#6-industry-tools--libraries)
7. [NEX Platform Requirements](#7-nex-platform-requirements)
8. [Architecture Design](#8-architecture-design)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Risk Assessment](#10-risk-assessment)
11. [Appendix](#11-appendix)

---

## 1. What is Synthetic Data?

### 1.1 Definition

Synthetic data is artificially generated data that mimics the statistical properties, patterns, and structure of real data without containing actual records from the source dataset. Unlike anonymized or masked data, synthetic data is created from scratch using mathematical models learned from the original data.

### 1.2 Types of Synthetic Data

| Type | Description | Privacy Level | Use Cases |
|------|-------------|---------------|-----------|
| **Fully Synthetic** | 100% artificially generated, no real records | Highest | Public sharing, external partners |
| **Partially Synthetic** | Some records real, sensitive values replaced | Medium | Internal testing, development |
| **Hybrid Synthetic** | Real structure with synthetic sensitive fields | Medium-Low | Analytics, reporting |

### 1.3 Synthetic Data vs. Other Privacy Techniques

| Technique | Description | Reversibility Risk | Utility Preservation |
|-----------|-------------|-------------------|---------------------|
| **Anonymization** | Remove identifying fields | Medium (linkage attacks) | High |
| **Pseudonymization** | Replace identifiers with tokens | High (with key) | High |
| **Data Masking** | Obfuscate sensitive values | Low-Medium | Medium |
| **Differential Privacy** | Add statistical noise | Very Low | Medium-Low |
| **Synthetic Data** | Generate new data from learned distribution | Very Low | High |

**Key Insight:** Synthetic data offers the best balance of privacy protection and data utility when done correctly.

---

## 2. Use Cases & Business Value

### 2.1 Primary Use Cases

#### 2.1.1 Software Development & Testing
- Create realistic test datasets without exposing production data
- Generate edge cases and boundary conditions
- Populate development environments with production-like data
- Enable parallel development with isolated datasets

**Value:** Reduces data breach risk, accelerates development cycles

#### 2.1.2 Machine Learning & AI
- Augment small datasets to improve model performance
- Balance imbalanced datasets (oversample minority classes)
- Create training data for rare events
- Enable transfer learning scenarios
- Generate labeled data when labeling is expensive

**Value:** Improves model accuracy, reduces data collection costs

#### 2.1.3 Data Sharing & Collaboration
- Share data with external partners without privacy concerns
- Enable cross-organization analytics
- Publish research datasets
- Support open data initiatives

**Value:** Unlocks collaboration, enables innovation

#### 2.1.4 Regulatory Compliance
- GDPR: Right to erasure compliance without breaking ML models
- HIPAA: Share medical data for research
- CCPA: Consumer data protection
- PCI-DSS: Payment data handling

**Value:** Reduces compliance risk, enables data monetization

#### 2.1.5 Data Marketplace
- Sell synthetic versions of proprietary datasets
- Create "demo" versions of premium data products
- Enable try-before-you-buy for data consumers

**Value:** New revenue streams, market expansion

### 2.2 Business Value Quantification

| Benefit | Typical Impact |
|---------|----------------|
| Reduced data breach risk | 60-80% reduction in exposure |
| Faster development cycles | 30-50% acceleration |
| Compliance cost savings | 40-60% reduction |
| ML model improvement | 10-30% accuracy gains (data augmentation) |
| New revenue opportunities | Varies (data products) |

---

## 3. Technical Approaches

### 3.1 Overview of Approaches

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SYNTHETIC DATA APPROACHES                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   STATISTICAL   │  │  MACHINE        │  │  DEEP           │     │
│  │   METHODS       │  │  LEARNING       │  │  LEARNING       │     │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤     │
│  │ • Random        │  │ • Decision      │  │ • GANs          │     │
│  │   Sampling      │  │   Trees         │  │ • VAEs          │     │
│  │ • Gaussian      │  │ • Bayesian      │  │ • Transformers  │     │
│  │   Copulas       │  │   Networks      │  │ • Diffusion     │     │
│  │ • KDE           │  │ • CART          │  │   Models        │     │
│  │ • Bootstrapping │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│         ▲                    ▲                    ▲                 │
│         │                    │                    │                 │
│    Fast, Simple         Balanced            Best Quality           │
│    Lower Quality        Good Privacy        Slow, Complex          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Statistical Methods

#### 3.2.1 Independent Column Sampling (Current NEX Implementation)

**How it works:**
- Analyze each column independently
- Fit statistical distribution (Gaussian for numeric, categorical for discrete)
- Sample from fitted distributions

**Pros:**
- Very fast
- Simple to implement
- Works with any data type

**Cons:**
- **Destroys correlations** between columns
- May produce invalid combinations (e.g., "Male" + "Pregnant")
- Limited privacy guarantees

**Code Example (Current):**
```python
# Current NEX approach
for column in df.columns:
    if is_numeric(column):
        synthetic[column] = np.random.normal(mean, std, n)
    else:
        synthetic[column] = np.random.choice(values, n, p=probs)
```

**Verdict:** ❌ Not suitable for production use due to correlation destruction

#### 3.2.2 Gaussian Copulas

**How it works:**
1. Transform each column to uniform distribution (using CDF)
2. Fit multivariate Gaussian to capture correlations
3. Sample from multivariate Gaussian
4. Inverse transform back to original distributions

**Mathematical Foundation:**
```
Given data X with marginal distributions F₁, F₂, ..., Fₙ:
1. U = (F₁(X₁), F₂(X₂), ..., Fₙ(Xₙ))  # Transform to uniform
2. Fit Gaussian copula C to U
3. Sample U' ~ C
4. X' = (F₁⁻¹(U'₁), F₂⁻¹(U'₂), ..., Fₙ⁻¹(U'ₙ))  # Inverse transform
```

**Pros:**
- Preserves pairwise correlations
- Fast training and sampling
- Works well for numeric data
- Mature, well-understood technique

**Cons:**
- Assumes linear correlations (may miss complex patterns)
- Struggles with highly categorical data
- May not capture multimodal distributions well

**Verdict:** ✅ Good default choice for most tabular data

#### 3.2.3 Kernel Density Estimation (KDE)

**How it works:**
- Place kernel (usually Gaussian) at each data point
- Sum kernels to estimate probability density
- Sample from estimated density

**Pros:**
- Non-parametric (makes no distribution assumptions)
- Can capture multimodal distributions

**Cons:**
- Computationally expensive for large datasets
- Curse of dimensionality (struggles with many columns)
- Bandwidth selection is tricky

**Verdict:** ⚠️ Limited use cases (small, low-dimensional data)

### 3.3 Machine Learning Methods

#### 3.3.1 Bayesian Networks

**How it works:**
- Learn directed acyclic graph (DAG) of variable dependencies
- Estimate conditional probability distributions
- Sample by traversing graph in topological order

**Pros:**
- Captures complex conditional dependencies
- Interpretable structure
- Efficient sampling once learned

**Cons:**
- Structure learning is NP-hard (approximations used)
- Struggles with continuous variables
- May miss some dependencies

**Verdict:** ✅ Good for data with known causal structure

#### 3.3.2 Classification and Regression Trees (CART)

**How it works:**
- Build decision tree to predict each variable given others
- Sample by recursively predicting values

**Pros:**
- Handles mixed data types well
- Captures non-linear relationships
- Fast inference

**Cons:**
- May overfit to training data
- Struggles with high-cardinality categorical variables

**Verdict:** ✅ Good for mixed-type data

### 3.4 Deep Learning Methods

#### 3.4.1 Generative Adversarial Networks (GANs)

**How it works:**
```
┌─────────────┐         ┌───────────────┐
│  Generator  │ ──────> │ Discriminator │
│     G(z)    │  fake   │     D(x)      │
└─────────────┘         └───────────────┘
       ▲                        │
       │    adversarial         │ real/fake?
       │    training            ▼
       │                 ┌─────────────┐
       └──────────────── │    Loss     │
                         └─────────────┘
```

- Generator creates synthetic data from random noise
- Discriminator tries to distinguish real from fake
- Both networks improve through adversarial training

**Variants for Tabular Data:**

| Variant | Description | Best For |
|---------|-------------|----------|
| **CTGAN** | Conditional GAN with mode-specific normalization | Mixed numeric/categorical |
| **TableGAN** | CNN-based for tabular data | Large datasets |
| **CopulaGAN** | GAN + Copula for correlations | Complex correlations |

**Pros:**
- Can capture complex, non-linear relationships
- Produces high-quality synthetic data
- State-of-the-art for many benchmarks

**Cons:**
- Training instability (mode collapse, vanishing gradients)
- Requires hyperparameter tuning
- Computationally expensive (benefits from GPU)
- May memorize training data (privacy risk)

**Verdict:** ✅ Best quality, but requires expertise and compute

#### 3.4.2 Variational Autoencoders (VAEs)

**How it works:**
```
Input ──> Encoder ──> Latent Space (z) ──> Decoder ──> Reconstruction
                          │
                    Sample z ~ N(μ, σ)
```

- Encoder maps data to latent distribution
- Decoder reconstructs data from latent samples
- Training optimizes reconstruction + KL divergence

**Tabular Variant: TVAE (Tabular VAE)**

**Pros:**
- More stable training than GANs
- Provides latent representation (useful for other tasks)
- Can incorporate domain constraints

**Cons:**
- May produce blurry/averaged outputs
- Less sharp than GAN outputs
- Still computationally expensive

**Verdict:** ✅ Good alternative to GANs, more stable

#### 3.4.3 Transformers & Large Language Models

**How it works:**
- Treat tabular data as sequences
- Train transformer to predict next token/value
- Sample autoregressively

**Examples:**
- **GReaT (Generation of Realistic Tabular data)** - Fine-tune GPT-2 on tabular data
- **TabuLa** - BERT-based tabular synthesis

**Pros:**
- Can leverage pre-trained models
- Handles complex sequential patterns
- State-of-the-art on some benchmarks

**Cons:**
- Very computationally expensive
- May not respect constraints
- Newer, less mature

**Verdict:** ⚠️ Promising but experimental for tabular data

#### 3.4.4 Diffusion Models

**How it works:**
- Forward process: gradually add noise to data
- Reverse process: learn to denoise
- Generate by starting from noise and denoising

**Pros:**
- Currently state-of-the-art for image generation
- More stable training than GANs
- Strong theoretical foundation

**Cons:**
- Slow sampling (many denoising steps)
- Newer for tabular data
- Computationally intensive

**Verdict:** ⚠️ Emerging approach, watch this space

### 3.5 Approach Comparison Matrix

| Approach | Quality | Speed | Privacy | Complexity | GPU Needed |
|----------|---------|-------|---------|------------|------------|
| Independent Sampling | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | No |
| Gaussian Copula | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | No |
| Bayesian Networks | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | No |
| CART | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | No |
| CTGAN | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Yes |
| TVAE | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Yes |
| Transformers | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | Yes |
| Diffusion | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Yes |

### 3.6 Recommendation for NEX

**Tiered Approach:**

1. **Default (Fast):** Gaussian Copula
   - Good quality, fast, no GPU needed
   - Suitable for most use cases
   
2. **High Quality:** CTGAN/TVAE
   - Best quality for complex data
   - Use with existing RunPod GPU infrastructure
   
3. **Specialized:** Bayesian Networks
   - When causal structure is known
   - For regulatory/explainability requirements

---

## 4. Privacy Considerations

### 4.1 Privacy Risks in Synthetic Data

Even synthetic data can leak information about the training data:

#### 4.1.1 Membership Inference
**Risk:** Attacker determines if specific individual was in training data
**Mitigation:** Differential privacy, larger datasets

#### 4.1.2 Attribute Inference  
**Risk:** Attacker infers sensitive attributes from non-sensitive ones
**Mitigation:** Remove highly predictive features, add noise

#### 4.1.3 Model Memorization
**Risk:** Deep learning models memorize and reproduce training records
**Mitigation:** Regularization, early stopping, differential privacy

#### 4.1.4 Linkage Attacks
**Risk:** Synthetic records linked to real individuals via external data
**Mitigation:** k-anonymity constraints, remove quasi-identifiers

### 4.2 Privacy-Preserving Techniques

#### 4.2.1 Differential Privacy (DP)

**Definition:** A mechanism M satisfies ε-differential privacy if for all datasets D₁, D₂ differing by one record:

```
P[M(D₁) ∈ S] ≤ e^ε × P[M(D₂) ∈ S]
```

**Implementation:**
- Add calibrated noise during training (DP-SGD)
- Add noise to statistics used for generation
- Post-processing (adding noise to synthetic data)

**Trade-off:** Privacy (ε) vs. Utility
- ε < 1: Strong privacy, lower utility
- ε = 1-10: Moderate privacy, good utility
- ε > 10: Weak privacy, high utility

#### 4.2.2 k-Anonymity

**Definition:** Each record is indistinguishable from at least k-1 other records on quasi-identifiers

**Implementation:**
- Generalize values (age 25 → age 20-30)
- Suppress rare combinations
- Ensure minimum group sizes

#### 4.2.3 PII Detection and Handling

**Categories of PII:**

| Category | Examples | Treatment |
|----------|----------|-----------|
| Direct Identifiers | SSN, Email, Phone | Replace with Faker-generated |
| Quasi-Identifiers | Age, ZIP, Gender | Generalize or add noise |
| Sensitive Attributes | Health, Finance | Generate from learned distribution |

**Implementation Strategy:**
1. Auto-detect PII columns (regex, NER, heuristics)
2. Flag for user confirmation
3. Apply appropriate treatment per category

### 4.3 Privacy Metrics

| Metric | What it Measures | Good Value |
|--------|------------------|------------|
| **Membership Inference AUC** | Can attacker detect training members? | < 0.55 |
| **Attribute Inference Accuracy** | Can attacker infer sensitive attributes? | Close to random |
| **Nearest Neighbor Distance** | Are synthetic records too close to real? | > threshold |
| **DCR (Distance to Closest Record)** | Minimum distance to training data | > threshold |

### 4.4 Privacy Levels for NEX

| Level | ε (if DP) | Use Case | Techniques |
|-------|-----------|----------|------------|
| **Standard** | N/A | Internal dev/test | Basic synthesis |
| **Enhanced** | 10 | Partner sharing | Quasi-identifier treatment |
| **Strict** | 1-5 | Regulated data | Full DP, PII replacement |
| **Maximum** | < 1 | Highly sensitive | DP + k-anonymity |

---

## 5. Quality Metrics & Validation

### 5.1 Statistical Fidelity Metrics

#### 5.1.1 Univariate Distribution Similarity

**Numeric Columns:**
- **Kolmogorov-Smirnov (KS) Test:** Max difference between CDFs
  - KS statistic < 0.1: Excellent
  - KS statistic 0.1-0.2: Good
  - KS statistic > 0.2: Poor

- **Wasserstein Distance:** "Earth mover's distance" between distributions
  
- **Jensen-Shannon Divergence:** Symmetric measure of distribution similarity

**Categorical Columns:**
- **Chi-Squared Test:** Compare observed vs expected frequencies
- **Total Variation Distance:** Sum of absolute frequency differences

#### 5.1.2 Multivariate Similarity

**Correlation Preservation:**
```python
correlation_score = 1 - |corr_real - corr_synthetic|.mean()
```
- Score > 0.9: Excellent
- Score 0.8-0.9: Good
- Score < 0.8: Needs improvement

**Contingency Tables (Categorical Pairs):**
- Compare joint distributions of categorical variable pairs

#### 5.1.3 Aggregate Statistics

| Statistic | Comparison |
|-----------|------------|
| Mean | |real_mean - synth_mean| / real_std |
| Std Dev | |real_std - synth_std| / real_std |
| Quantiles | Compare percentiles (25th, 50th, 75th, 99th) |
| Skewness | |real_skew - synth_skew| |
| Kurtosis | |real_kurt - synth_kurt| |

### 5.2 Machine Learning Utility Metrics

**"Train on Synthetic, Test on Real" (TSTR):**
1. Train ML model on synthetic data
2. Evaluate on held-out real data
3. Compare to model trained on real data

```
Utility Score = Accuracy(TSTR) / Accuracy(TRTR)
```

- Score > 0.95: Excellent synthetic data
- Score 0.85-0.95: Good
- Score < 0.85: May not be suitable for ML

**"Train on Real, Test on Synthetic" (TRTS):**
- Tests if synthetic captures patterns in real data

### 5.3 Detection Metrics

**Discriminator Accuracy:**
- Train classifier to distinguish real vs synthetic
- Random performance (50%) = indistinguishable = good
- High accuracy (>70%) = synthetic is detectable = bad

### 5.4 Constraint Satisfaction

**Domain Constraints:**
- Valid ranges (age > 0, price > 0)
- Referential integrity (foreign keys valid)
- Business rules (if pregnant, then female)

**Satisfaction Rate:**
```
Constraint Score = Valid Records / Total Records
```

### 5.5 Quality Report Structure

```json
{
  "overall_quality_score": 0.87,
  "statistical_fidelity": {
    "univariate_similarity": 0.92,
    "correlation_preservation": 0.85,
    "distribution_scores": {
      "column_name": {"ks_stat": 0.08, "p_value": 0.34}
    }
  },
  "ml_utility": {
    "tstr_score": 0.91,
    "model_type": "random_forest",
    "target_column": "target"
  },
  "privacy_metrics": {
    "membership_inference_auc": 0.52,
    "dcr_min": 0.15,
    "dcr_mean": 0.45
  },
  "constraint_satisfaction": {
    "valid_ranges": 1.0,
    "business_rules": 0.98
  },
  "recommendations": [
    "Consider increasing sample size for column X",
    "High correlation between A and B not fully captured"
  ]
}
```

---

## 6. Industry Tools & Libraries

### 6.1 Open Source Libraries

#### 6.1.1 SDV (Synthetic Data Vault) ⭐ Recommended

**Overview:**
- Most comprehensive open-source synthetic data library
- Developed by MIT Data to AI Lab
- Active development, large community

**Features:**
- Multiple synthesizers (Gaussian Copula, CTGAN, TVAE, CopulaGAN)
- Single table, multi-table, and time-series support
- Built-in quality metrics
- Constraint handling
- Privacy controls

**Synthesizers:**
| Synthesizer | Best For | Speed | Quality |
|-------------|----------|-------|---------|
| GaussianCopulaSynthesizer | Most tabular data | Fast | Good |
| CTGANSynthesizer | Complex distributions | Slow | Excellent |
| TVAESynthesizer | Mixed types | Medium | Very Good |
| CopulaGANSynthesizer | Complex correlations | Slow | Excellent |

**Installation:**
```bash
pip install sdv
```

**Basic Usage:**
```python
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata

# Define metadata
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(real_data)

# Create and fit synthesizer
synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_data)

# Generate synthetic data
synthetic_data = synthesizer.sample(num_rows=1000)

# Evaluate quality
from sdv.evaluation.single_table import run_diagnostic, evaluate_quality
diagnostic = run_diagnostic(real_data, synthetic_data, metadata)
quality_report = evaluate_quality(real_data, synthetic_data, metadata)
```

**Pros:**
- Comprehensive feature set
- Active development
- Good documentation
- Built-in evaluation

**Cons:**
- Can be slow for large datasets
- Some advanced features require care

#### 6.1.2 Faker

**Overview:**
- Generate fake data for specific data types
- Great for PII replacement

**Usage:**
```python
from faker import Faker
fake = Faker()

fake.name()           # 'John Smith'
fake.email()          # 'john.smith@example.com'
fake.address()        # '123 Main St, City, State 12345'
fake.ssn()            # '123-45-6789'
fake.credit_card()    # '4111111111111111'
```

**Best For:** Replacing PII columns with realistic fake values

#### 6.1.3 Gretel.ai (Open Source Components)

**Overview:**
- Enterprise synthetic data platform with OSS components
- Includes gretel-synthetics library

**Features:**
- LSTM-based synthesis
- Differential privacy support
- Quality evaluation

#### 6.1.4 DataSynthesizer

**Overview:**
- Privacy-aware synthetic data generation
- Supports differential privacy

**Features:**
- Random mode, independent attribute mode, correlated attribute mode
- Differential privacy built-in
- Good for privacy-focused use cases

#### 6.1.5 ydata-synthetic

**Overview:**
- Focus on time-series synthetic data
- GAN-based approaches

**Features:**
- TimeGAN for temporal data
- WGAN, DRAGAN variants

### 6.2 Commercial Platforms

| Platform | Key Features | Pricing Model |
|----------|--------------|---------------|
| **Gretel.ai** | Full platform, privacy guarantees, API | Per-record/subscription |
| **Tonic.ai** | Database subsetting, referential integrity | Enterprise |
| **Mostly AI** | Enterprise focus, GDPR compliance | Enterprise |
| **Hazy** | Enterprise, financial services focus | Enterprise |
| **Synthesized** | Open-core model, SDK | Freemium |

### 6.3 Recommendation for NEX

**Primary:** SDV
- Comprehensive, well-maintained
- Multiple synthesizer options
- Built-in evaluation
- Fits NEX architecture well

**Secondary:** Faker
- PII generation for column replacement
- Fast and reliable

**Optional:** Gretel or ydata-synthetic
- For advanced time-series use cases
- If specific deep learning approaches needed

---

## 7. NEX Platform Requirements

### 7.1 Functional Requirements

#### 7.1.1 Core Generation
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Generate synthetic data from uploaded datasets | P0 |
| FR-2 | Generate synthetic data from database tables | P0 |
| FR-3 | Support multiple synthesizer algorithms | P1 |
| FR-4 | Allow user to specify number of rows | P0 |
| FR-5 | Support all common data types (numeric, categorical, datetime, text) | P0 |
| FR-6 | Preserve statistical distributions | P0 |
| FR-7 | Preserve correlations between columns | P0 |

#### 7.1.2 Privacy & Security
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8 | Auto-detect PII columns | P1 |
| FR-9 | Replace PII with realistic fake data | P1 |
| FR-10 | Support differential privacy | P2 |
| FR-11 | Provide privacy risk assessment | P1 |
| FR-12 | Support column-level privacy settings | P1 |

#### 7.1.3 Quality & Validation
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-13 | Generate quality report after synthesis | P0 |
| FR-14 | Show distribution comparison visualizations | P1 |
| FR-15 | Provide ML utility metrics | P2 |
| FR-16 | Allow constraint specification | P1 |
| FR-17 | Validate constraints on generated data | P1 |

#### 7.1.4 Integration
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-18 | Save synthetic datasets to platform storage | P0 |
| FR-19 | Track lineage (synthetic → source) | P1 |
| FR-20 | Export to multiple formats (CSV, Parquet) | P1 |
| FR-21 | API for programmatic generation | P0 |
| FR-22 | Generate in notebooks | P2 |

### 7.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Generation time for 10K rows | < 60 seconds (Copula), < 5 min (GAN) |
| NFR-2 | Generation time for 100K rows | < 5 min (Copula), < 30 min (GAN) |
| NFR-3 | Memory usage | < 4GB for 100K rows |
| NFR-4 | API response time | < 200ms (job submission) |
| NFR-5 | Concurrent generation jobs | 10+ |
| NFR-6 | Uptime | 99.9% |

### 7.3 User Stories

```
As a data analyst,
I want to generate synthetic versions of production data,
So that I can share datasets with vendors without privacy concerns.

As a ML engineer,
I want to augment my training data with synthetic samples,
So that I can improve model performance on rare events.

As a developer,
I want to populate my test database with realistic data,
So that I can test edge cases without using production data.

As a compliance officer,
I want to verify synthetic data doesn't leak real information,
So that we can meet regulatory requirements.
```

---

## 8. Architecture Design

### 8.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Synthetic Data  │  │ Quality Report  │  │ Configuration   │         │
│  │ Generation UI   │  │ Dashboard       │  │ Wizard          │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼─────────────────────┼─────────────────────┼─────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    /api/v1/synthetic/*                           │   │
│  │  POST /generate   GET /jobs/{id}   GET /quality/{id}            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYNTHETIC DATA DOMAIN                            │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Router     │  │   Service    │  │   Models     │  │  DB Models │  │
│  │              │─▶│              │─▶│              │  │            │  │
│  │ - endpoints  │  │ - generation │  │ - requests   │  │ - jobs     │  │
│  │ - validation │  │ - evaluation │  │ - responses  │  │ - configs  │  │
│  │              │  │ - privacy    │  │ - configs    │  │ - reports  │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └────────────┘  │
│                           │                                             │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  SYNTHESIZERS    │ │  EVALUATORS  │ │  PRIVACY ENGINE  │
│                  │ │              │ │                  │
│ ┌──────────────┐ │ │ - Statistical│ │ - PII Detection │
│ │GaussianCopula│ │ │ - ML Utility │ │ - Faker         │
│ └──────────────┘ │ │ - Detection  │ │ - DP Mechanism  │
│ ┌──────────────┐ │ │ - Privacy    │ │ - Risk Scoring  │
│ │    CTGAN     │ │ │              │ │                 │
│ └──────────────┘ │ └──────────────┘ └──────────────────┘
│ ┌──────────────┐ │
│ │    TVAE      │ │
│ └──────────────┘ │
└──────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPUTE LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Local Executor │  │  RunPod GPU     │  │  Background     │         │
│  │  (CPU tasks)    │  │  (GAN training) │  │  Workers        │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   PostgreSQL    │  │     MinIO       │  │     Redis       │         │
│  │   (metadata)    │  │   (datasets)    │  │   (job queue)   │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Domain Structure

```
backend/domains/synthetic/
├── __init__.py
├── router.py           # API endpoints
├── service.py          # Core business logic
├── models.py           # Pydantic models (request/response)
├── db_models.py        # SQLAlchemy models
├── synthesizers/
│   ├── __init__.py
│   ├── base.py         # Abstract synthesizer interface
│   ├── copula.py       # Gaussian Copula implementation
│   ├── ctgan.py        # CTGAN wrapper
│   └── tvae.py         # TVAE wrapper
├── evaluators/
│   ├── __init__.py
│   ├── statistical.py  # Distribution similarity metrics
│   ├── ml_utility.py   # TSTR/TRTS metrics
│   ├── privacy.py      # Privacy risk metrics
│   └── report.py       # Quality report generation
├── privacy/
│   ├── __init__.py
│   ├── pii_detector.py # Auto-detect PII
│   ├── faker_gen.py    # Generate fake PII
│   └── dp.py           # Differential privacy
└── constraints/
    ├── __init__.py
    └── validator.py    # Constraint validation
```

### 8.3 Database Schema

```sql
-- Synthetic generation job tracking
CREATE TABLE synthetic_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_dataset_id UUID REFERENCES datasets(id),
    source_table_ref VARCHAR(255),  -- For DB table sources
    synthesizer_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    privacy_config JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    num_rows_requested INTEGER NOT NULL,
    num_rows_generated INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);

-- Generated synthetic datasets
CREATE TABLE synthetic_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES synthetic_jobs(id),
    name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500),
    num_rows INTEGER NOT NULL,
    num_columns INTEGER NOT NULL,
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quality evaluation reports
CREATE TABLE synthetic_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    synthetic_dataset_id UUID REFERENCES synthetic_datasets(id),
    overall_score DECIMAL(4,3),
    statistical_fidelity JSONB,
    ml_utility JSONB,
    privacy_metrics JSONB,
    constraint_satisfaction JSONB,
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Column-level configuration
CREATE TABLE synthetic_column_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES synthetic_jobs(id),
    column_name VARCHAR(255) NOT NULL,
    column_type VARCHAR(50),
    is_pii BOOLEAN DEFAULT FALSE,
    pii_type VARCHAR(50),  -- 'email', 'name', 'ssn', etc.
    faker_provider VARCHAR(100),
    constraints JSONB DEFAULT '{}',
    UNIQUE(job_id, column_name)
);
```

### 8.4 API Design

#### 8.4.1 Generate Synthetic Data

```
POST /api/v1/synthetic/generate
```

**Request:**
```json
{
  "source": {
    "type": "dataset",
    "dataset_id": "uuid"
  },
  "config": {
    "synthesizer": "gaussian_copula",
    "num_rows": 5000,
    "random_seed": 42
  },
  "privacy": {
    "level": "enhanced",
    "pii_handling": "auto_detect",
    "differential_privacy": {
      "enabled": false,
      "epsilon": 1.0
    }
  },
  "columns": {
    "email": {
      "is_pii": true,
      "faker": "email"
    },
    "age": {
      "constraints": {
        "min": 18,
        "max": 100
      }
    }
  },
  "constraints": [
    {
      "type": "inequality",
      "columns": ["start_date", "end_date"],
      "condition": "start_date < end_date"
    }
  ]
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "estimated_time_seconds": 120,
  "message": "Synthetic data generation job queued"
}
```

#### 8.4.2 Get Job Status

```
GET /api/v1/synthetic/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "synthetic_dataset_id": "uuid",
  "num_rows_generated": 5000,
  "duration_seconds": 45,
  "quality_summary": {
    "overall_score": 0.89,
    "recommendation": "Good quality synthetic data"
  }
}
```

#### 8.4.3 Get Quality Report

```
GET /api/v1/synthetic/quality/{synthetic_dataset_id}
```

**Response:**
```json
{
  "synthetic_dataset_id": "uuid",
  "source_dataset_id": "uuid",
  "overall_score": 0.89,
  "statistical_fidelity": {
    "univariate_similarity": 0.92,
    "correlation_preservation": 0.87,
    "column_scores": {
      "age": {"ks_stat": 0.05, "rating": "excellent"},
      "income": {"ks_stat": 0.12, "rating": "good"}
    }
  },
  "privacy_metrics": {
    "membership_inference_risk": "low",
    "nearest_neighbor_distance": 0.23
  },
  "visualizations": {
    "distribution_comparisons": "/api/v1/synthetic/viz/distributions/{id}",
    "correlation_heatmaps": "/api/v1/synthetic/viz/correlations/{id}"
  },
  "recommendations": [
    "Consider using CTGAN for better capture of 'income' distribution"
  ]
}
```

#### 8.4.4 List Synthesizers

```
GET /api/v1/synthetic/synthesizers
```

**Response:**
```json
{
  "synthesizers": [
    {
      "id": "gaussian_copula",
      "name": "Gaussian Copula",
      "description": "Fast statistical synthesizer using Gaussian copulas",
      "speed": "fast",
      "quality": "good",
      "gpu_required": false,
      "best_for": ["Most tabular data", "Quick generation"]
    },
    {
      "id": "ctgan",
      "name": "CTGAN",
      "description": "Deep learning synthesizer using Conditional GANs",
      "speed": "slow",
      "quality": "excellent",
      "gpu_required": true,
      "best_for": ["Complex distributions", "High-quality requirements"]
    }
  ]
}
```

### 8.5 Service Layer Design

```python
# backend/domains/synthetic/service.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
from uuid import UUID

class BaseSynthesizer(ABC):
    """Abstract base class for all synthesizers."""
    
    @abstractmethod
    def fit(self, data: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        """Fit the synthesizer to the data."""
        pass
    
    @abstractmethod
    def sample(self, num_rows: int) -> pd.DataFrame:
        """Generate synthetic samples."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get synthesizer information."""
        pass


class SyntheticDataService:
    """Main service for synthetic data generation."""
    
    def __init__(
        self,
        db: Database,
        storage: ObjectStorage,
        compute: ComputeAdapter,
    ):
        self.db = db
        self.storage = storage
        self.compute = compute
        self.synthesizers = {
            "gaussian_copula": GaussianCopulaSynthesizer,
            "ctgan": CTGANSynthesizer,
            "tvae": TVAESynthesizer,
        }
    
    async def create_generation_job(
        self,
        request: SyntheticGenerationRequest,
    ) -> SyntheticJob:
        """Create a new synthetic data generation job."""
        # 1. Validate request
        # 2. Load source data metadata
        # 3. Create job record
        # 4. Queue for processing
        # 5. Return job info
        pass
    
    async def process_generation_job(self, job_id: UUID) -> None:
        """Process a synthetic data generation job."""
        # 1. Load job config
        # 2. Load source data
        # 3. Detect/apply PII handling
        # 4. Initialize synthesizer
        # 5. Fit and generate
        # 6. Validate constraints
        # 7. Save synthetic data
        # 8. Generate quality report
        # 9. Update job status
        pass
    
    async def evaluate_quality(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        metadata: Dict[str, Any],
    ) -> QualityReport:
        """Evaluate synthetic data quality."""
        pass
```

---

## 9. Implementation Roadmap

### 9.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1        Phase 2         Phase 3         Phase 4        Phase 5  │
│  Foundation     Privacy         Quality         UI             Platform │
│  ─────────     ───────         ───────         ──             ────────  │
│  ████████      ██████          ██████          ████           ████      │
│                                                                          │
│  2-3 days      1-2 days        1-2 days        1-2 days       1-2 days  │
│                                                                          │
│  Core engine   PII handling    Metrics         Generation     Lineage   │
│  SDV setup     Faker           Reports         wizard         Notebooks │
│  Basic API     DP (optional)   Viz             Quality UI     Export    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Phase 1: Foundation (Days 1-3)

**Goal:** Replace basic synthesizer with SDV-based engine

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Add SDV, Faker to requirements.txt | 0.5h |
| 1.2 | Create domain structure (synthetic/) | 1h |
| 1.3 | Implement DB models and migrations | 2h |
| 1.4 | Create base synthesizer interface | 1h |
| 1.5 | Implement GaussianCopulaSynthesizer | 3h |
| 1.6 | Implement CTGANSynthesizer | 2h |
| 1.7 | Implement TVAESynthesizer | 1h |
| 1.8 | Create SyntheticDataService | 4h |
| 1.9 | Implement API endpoints | 3h |
| 1.10 | Background job processing | 2h |
| 1.11 | Basic tests | 2h |

**Deliverables:**
- Working `/api/v1/synthetic/generate` endpoint
- Three synthesizer options
- Job tracking in database
- Synthetic datasets saved to MinIO

**Success Criteria:**
- Can generate 10K synthetic rows in < 60 seconds (Copula)
- Correlations preserved (score > 0.8)

### 9.3 Phase 2: Privacy & PII (Days 4-5)

**Goal:** Auto-detect and handle sensitive data

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Implement PII detection service | 3h |
| 2.2 | Create Faker-based PII generator | 2h |
| 2.3 | Column-level privacy config | 2h |
| 2.4 | Privacy risk scoring | 2h |
| 2.5 | (Optional) Differential privacy wrapper | 4h |
| 2.6 | Update API for privacy config | 1h |
| 2.7 | Tests for privacy features | 2h |

**Deliverables:**
- Auto-detection of email, phone, SSN, name columns
- Faker replacement for PII
- Privacy level configuration
- Basic privacy risk report

**Success Criteria:**
- 90%+ accuracy on PII detection
- All detected PII replaced with fake data
- Privacy risk score in quality report

### 9.4 Phase 3: Quality Metrics (Days 6-7)

**Goal:** Comprehensive quality evaluation

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Statistical fidelity metrics | 3h |
| 3.2 | Correlation preservation scoring | 2h |
| 3.3 | ML utility metrics (TSTR) | 3h |
| 3.4 | Privacy metrics (membership inference) | 2h |
| 3.5 | Quality report generation | 2h |
| 3.6 | Visualization endpoints | 2h |
| 3.7 | Tests for metrics | 2h |

**Deliverables:**
- Comprehensive quality report
- KS test scores per column
- Correlation preservation score
- ML utility score (optional)
- Distribution comparison visualizations

**Success Criteria:**
- Quality report generated for every synthesis
- Overall score correlates with actual quality
- Actionable recommendations provided

### 9.5 Phase 4: UI Enhancements (Days 8-9)

**Goal:** Intuitive generation and quality visualization

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Redesign SyntheticData.tsx | 4h |
| 4.2 | Synthesizer selection UI | 2h |
| 4.3 | Column configuration panel | 3h |
| 4.4 | Privacy settings panel | 2h |
| 4.5 | Quality report dashboard | 4h |
| 4.6 | Distribution comparison charts | 3h |
| 4.7 | Job progress tracking | 2h |

**Deliverables:**
- Step-by-step generation wizard
- Real-time job progress
- Interactive quality dashboard
- Distribution comparison charts
- Synthetic dataset catalog

**Success Criteria:**
- User can configure and generate in < 5 clicks
- Quality metrics clearly visualized
- Progress visible for long-running jobs

### 9.6 Phase 5: Platform Integration (Days 10-11)

**Goal:** Deep integration with NEX platform

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | Data lineage integration | 3h |
| 5.2 | Generate from DB tables | 3h |
| 5.3 | Notebook integration | 2h |
| 5.4 | Export formats (CSV, Parquet) | 2h |
| 5.5 | GPU execution (RunPod) for CTGAN | 3h |
| 5.6 | Documentation | 2h |
| 5.7 | End-to-end tests | 2h |

**Deliverables:**
- Synthetic → Source lineage tracking
- Generate from connected databases
- Use in Python notebooks
- Multiple export formats
- GPU acceleration for deep learning synthesizers

**Success Criteria:**
- Lineage visible in lineage graph
- CTGAN runs on RunPod GPU
- Full workflow documented

### 9.7 Milestone Summary

| Milestone | Target | Key Metrics |
|-----------|--------|-------------|
| M1: Foundation | Day 3 | 3 synthesizers working |
| M2: Privacy | Day 5 | PII auto-detection + replacement |
| M3: Quality | Day 7 | Quality reports generated |
| M4: UI | Day 9 | Generation wizard complete |
| M5: Integration | Day 11 | Full platform integration |

---

## 10. Risk Assessment

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SDV library instability | Low | High | Pin version, have fallback |
| GAN training instability | Medium | Medium | Default to Copula, tune hyperparams |
| Memory issues with large data | Medium | Medium | Streaming, chunked processing |
| Slow generation times | Medium | Low | Background jobs, progress tracking |
| Poor quality for some data types | Medium | Medium | Multiple synthesizers, guidance |

### 10.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users don't understand output | Medium | Medium | Clear quality reports, education |
| Privacy concerns | Low | High | Privacy metrics, PII handling |
| Compliance issues | Low | High | Audit logging, documentation |

### 10.3 Dependency Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| SDV | Version changes | Pin version, abstract interface |
| Faker | Limited | Can add custom providers |
| NumPy/Pandas | Stable | Standard data science stack |

---

## 11. Appendix

### 11.1 Glossary

| Term | Definition |
|------|------------|
| **Copula** | Function that couples marginal distributions to joint distribution |
| **GAN** | Generative Adversarial Network |
| **VAE** | Variational Autoencoder |
| **Differential Privacy** | Mathematical framework for privacy guarantees |
| **PII** | Personally Identifiable Information |
| **TSTR** | Train on Synthetic, Test on Real |
| **KS Test** | Kolmogorov-Smirnov statistical test |
| **Mode Collapse** | GAN failure where generator produces limited variety |

### 11.2 References

**Papers:**
- Xu et al. (2019) "Modeling Tabular Data using Conditional GAN" (CTGAN)
- Patki et al. (2016) "The Synthetic Data Vault"
- Jordon et al. (2018) "PATE-GAN: Generating Synthetic Data with Differential Privacy"

**Libraries:**
- SDV: https://sdv.dev/
- Faker: https://faker.readthedocs.io/
- Gretel: https://gretel.ai/

### 11.3 Sample Code Snippets

**Basic SDV Usage:**
```python
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata

# Create metadata
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(df)

# Mark PII columns
metadata.update_column(column_name='email', sdtype='email')
metadata.update_column(column_name='name', sdtype='name')

# Create synthesizer
synth = GaussianCopulaSynthesizer(
    metadata,
    enforce_min_max_values=True,
    enforce_rounding=True
)

# Fit and generate
synth.fit(df)
synthetic_df = synth.sample(num_rows=1000)
```

**Quality Evaluation:**
```python
from sdv.evaluation.single_table import (
    run_diagnostic,
    evaluate_quality,
    get_column_plot
)

# Run diagnostic
diagnostic = run_diagnostic(real_df, synthetic_df, metadata)
print(diagnostic.get_score())

# Evaluate quality
quality_report = evaluate_quality(real_df, synthetic_df, metadata)
print(quality_report.get_score())

# Get column comparison
fig = get_column_plot(real_df, synthetic_df, column_name='age')
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: NEX Platform Team*
