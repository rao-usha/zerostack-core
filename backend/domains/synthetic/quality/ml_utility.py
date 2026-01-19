"""ML utility metrics for synthetic data quality evaluation.

The key idea: if synthetic data is good, a model trained on it should perform
well when tested on real data (Train on Synthetic, Test on Real - TSTR).
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    mean_squared_error, r2_score, mean_absolute_error
)

logger = logging.getLogger(__name__)


@dataclass
class MLUtilityReport:
    """Report for ML utility evaluation."""
    overall_score: float  # 0-1, how useful is synthetic for ML
    task_type: str  # "classification" or "regression"
    target_column: str
    
    # TSTR: Train on Synthetic, Test on Real
    tstr_score: float
    
    # TRTR: Train on Real, Test on Real (baseline)
    trtr_score: float
    
    # How close TSTR is to TRTR (1.0 = perfect)
    utility_ratio: float = 0.0
    
    # Metrics dicts
    tstr_metrics: Dict[str, float] = field(default_factory=dict)
    trtr_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Feature importance comparison
    feature_importance_correlation: Optional[float] = None
    
    recommendations: List[str] = field(default_factory=list)


class MLUtilityEvaluator:
    """Evaluate how useful synthetic data is for training ML models.
    
    Uses the TSTR (Train on Synthetic, Test on Real) methodology:
    1. Train a model on synthetic data
    2. Test on held-out real data
    3. Compare to baseline (trained on real data)
    
    If TSTR performance is close to TRTR (Train Real, Test Real),
    the synthetic data has high ML utility.
    """
    
    def __init__(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        max_features: int = 20,
    ):
        """Initialize ML utility evaluator.
        
        Args:
            test_size: Fraction of real data to hold out for testing
            random_state: Random seed for reproducibility
            max_features: Maximum features to use (for performance)
        """
        self.test_size = test_size
        self.random_state = random_state
        self.max_features = max_features
    
    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        target_column: str,
        task_type: Optional[str] = None,
    ) -> MLUtilityReport:
        """Evaluate ML utility of synthetic data.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            target_column: Column to predict
            task_type: "classification" or "regression", auto-detected if None
            
        Returns:
            MLUtilityReport with scores and metrics
        """
        if target_column not in real_data.columns:
            raise ValueError(f"Target column '{target_column}' not in real data")
        if target_column not in synthetic_data.columns:
            raise ValueError(f"Target column '{target_column}' not in synthetic data")
        
        # Prepare data
        real_prepared = self._prepare_data(real_data, target_column)
        synth_prepared = self._prepare_data(synthetic_data, target_column)
        
        if real_prepared is None or synth_prepared is None:
            return MLUtilityReport(
                overall_score=0.0,
                task_type="unknown",
                target_column=target_column,
                tstr_score=0.0,
                trtr_score=0.0,
                recommendations=["Could not prepare data for ML evaluation."],
            )
        
        X_real, y_real, feature_cols = real_prepared
        X_synth, y_synth, _ = synth_prepared
        
        # Auto-detect task type
        if task_type is None:
            task_type = self._detect_task_type(y_real)
        
        logger.info(f"Evaluating ML utility for {task_type} task on '{target_column}'")
        
        # Split real data into train and test
        X_real_train, X_real_test, y_real_train, y_real_test = train_test_split(
            X_real, y_real,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y_real if task_type == "classification" else None,
        )
        
        # TRTR: Train on Real, Test on Real (baseline)
        trtr_score, trtr_metrics, trtr_model = self._train_and_evaluate(
            X_real_train, y_real_train,
            X_real_test, y_real_test,
            task_type,
        )
        
        # TSTR: Train on Synthetic, Test on Real
        tstr_score, tstr_metrics, tstr_model = self._train_and_evaluate(
            X_synth, y_synth,
            X_real_test, y_real_test,
            task_type,
        )
        
        # Calculate utility ratio (how close TSTR is to TRTR)
        if trtr_score > 0:
            utility_ratio = min(1.0, tstr_score / trtr_score)
        else:
            utility_ratio = 0.0
        
        # Feature importance comparison
        fi_correlation = self._compare_feature_importance(
            trtr_model, tstr_model, feature_cols, task_type
        )
        
        # Overall score (weighted)
        overall_score = 0.7 * utility_ratio + 0.3 * (fi_correlation or 0.5)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            utility_ratio, fi_correlation, task_type, tstr_metrics, trtr_metrics
        )
        
        return MLUtilityReport(
            overall_score=round(overall_score, 3),
            task_type=task_type,
            target_column=target_column,
            tstr_score=round(tstr_score, 3),
            tstr_metrics=tstr_metrics,
            trtr_score=round(trtr_score, 3),
            trtr_metrics=trtr_metrics,
            utility_ratio=round(utility_ratio, 3),
            feature_importance_correlation=round(fi_correlation, 3) if fi_correlation else None,
            recommendations=recommendations,
        )
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str,
    ) -> Optional[Tuple[np.ndarray, np.ndarray, List[str]]]:
        """Prepare data for ML by encoding and scaling."""
        try:
            df = df.copy()
            
            # Separate features and target
            y = df[target_column].copy()
            X = df.drop(columns=[target_column])
            
            # Remove columns with too many nulls
            null_pct = X.isnull().mean()
            X = X.loc[:, null_pct < 0.5]
            
            # Limit features
            if len(X.columns) > self.max_features:
                # Keep most varied columns
                variances = []
                for col in X.columns:
                    if pd.api.types.is_numeric_dtype(X[col]):
                        variances.append((col, X[col].var()))
                    else:
                        variances.append((col, X[col].nunique()))
                variances.sort(key=lambda x: x[1], reverse=True)
                X = X[[v[0] for v in variances[:self.max_features]]]
            
            feature_cols = list(X.columns)
            
            # Encode categorical features
            for col in X.select_dtypes(include=['object', 'category']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].fillna('__missing__'))
            
            # Fill remaining nulls
            X = X.fillna(0)
            
            # Encode target if categorical
            if not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = le.fit_transform(y.fillna('__missing__'))
            else:
                y = y.fillna(y.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            return X_scaled, np.array(y), feature_cols
            
        except Exception as e:
            logger.warning(f"Data preparation failed: {e}")
            return None
    
    def _detect_task_type(self, y: np.ndarray) -> str:
        """Auto-detect if classification or regression."""
        unique_values = len(np.unique(y))
        
        if unique_values <= 10:
            return "classification"
        elif unique_values / len(y) < 0.05:  # Less than 5% unique
            return "classification"
        else:
            return "regression"
    
    def _train_and_evaluate(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        task_type: str,
    ) -> Tuple[float, Dict[str, float], Any]:
        """Train model and evaluate on test set."""
        try:
            if task_type == "classification":
                # Use Random Forest for robustness
                model = RandomForestClassifier(
                    n_estimators=50,
                    max_depth=10,
                    random_state=self.random_state,
                    n_jobs=-1,
                )
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                y_proba = model.predict_proba(X_test)
                
                accuracy = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                # AUC for binary, average for multiclass
                if len(np.unique(y_train)) == 2:
                    auc = roc_auc_score(y_test, y_proba[:, 1])
                else:
                    try:
                        auc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
                    except:
                        auc = 0.5
                
                return accuracy, {
                    "accuracy": round(accuracy, 4),
                    "f1_score": round(f1, 4),
                    "auc": round(auc, 4),
                }, model
                
            else:  # regression
                model = RandomForestRegressor(
                    n_estimators=50,
                    max_depth=10,
                    random_state=self.random_state,
                    n_jobs=-1,
                )
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                
                # Normalize R2 to 0-1 (can be negative)
                score = max(0, r2)
                
                return score, {
                    "r2_score": round(r2, 4),
                    "rmse": round(rmse, 4),
                    "mae": round(mae, 4),
                }, model
                
        except Exception as e:
            logger.warning(f"Model training failed: {e}")
            return 0.0, {"error": str(e)}, None
    
    def _compare_feature_importance(
        self,
        model1: Any,
        model2: Any,
        feature_cols: List[str],
        task_type: str,
    ) -> Optional[float]:
        """Compare feature importance between models."""
        try:
            if model1 is None or model2 is None:
                return None
            
            fi1 = model1.feature_importances_
            fi2 = model2.feature_importances_
            
            # Spearman correlation of feature importance rankings
            from scipy.stats import spearmanr
            correlation, _ = spearmanr(fi1, fi2)
            
            # Convert to 0-1 score (correlation can be -1 to 1)
            return (correlation + 1) / 2
            
        except Exception as e:
            logger.warning(f"Feature importance comparison failed: {e}")
            return None
    
    def _generate_recommendations(
        self,
        utility_ratio: float,
        fi_correlation: Optional[float],
        task_type: str,
        tstr_metrics: Dict,
        trtr_metrics: Dict,
    ) -> List[str]:
        """Generate recommendations based on ML utility."""
        recommendations = []
        
        if utility_ratio >= 0.9:
            recommendations.append(
                "Excellent ML utility! Synthetic data can effectively replace real data for model training."
            )
        elif utility_ratio >= 0.75:
            recommendations.append(
                "Good ML utility. Synthetic data is suitable for model development and testing."
            )
        elif utility_ratio >= 0.5:
            recommendations.append(
                "Moderate ML utility. Consider using more training data or a different synthesizer."
            )
        else:
            recommendations.append(
                "Low ML utility. The synthetic data may not capture patterns needed for ML. "
                "Try CTGAN or TVAE with more epochs, or increase source data size."
            )
        
        if fi_correlation is not None and fi_correlation < 0.7:
            recommendations.append(
                "Feature importance differs between models trained on real vs synthetic data. "
                "Some feature relationships may not be well preserved."
            )
        
        return recommendations
