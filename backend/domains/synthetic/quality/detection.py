"""Detection metrics for synthetic data quality evaluation.

The key idea: if synthetic data is good, a classifier should NOT be able
to easily distinguish between real and synthetic records.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

logger = logging.getLogger(__name__)


@dataclass
class DetectionReport:
    """Report for synthetic data detection evaluation."""
    overall_score: float  # 0-1, how hard is it to detect (higher = better synthetic)
    
    # Detection accuracy (0.5 = random, can't distinguish; 1.0 = perfect detection)
    detection_accuracy: float
    detection_auc: float
    
    # Cross-validation scores
    cv_scores: List[float] = field(default_factory=list)
    cv_mean: float = 0.0
    cv_std: float = 0.0
    
    # Per-model results
    model_results: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Most distinguishing features
    distinguishing_features: List[Tuple[str, float]] = field(default_factory=list)
    
    recommendations: List[str] = field(default_factory=list)


class DetectionEvaluator:
    """Evaluate how easily synthetic data can be distinguished from real data.
    
    A good synthetic dataset should be indistinguishable from real data.
    If a classifier can easily tell them apart, the synthetic data has issues.
    
    Ideal result: accuracy ≈ 0.5 (random guessing)
    Poor result: accuracy > 0.8 (easily detectable)
    """
    
    def __init__(
        self,
        n_splits: int = 5,
        random_state: int = 42,
        max_features: int = 30,
    ):
        """Initialize detection evaluator.
        
        Args:
            n_splits: Number of CV folds
            random_state: Random seed
            max_features: Maximum features to use
        """
        self.n_splits = n_splits
        self.random_state = random_state
        self.max_features = max_features
    
    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
    ) -> DetectionReport:
        """Evaluate how distinguishable synthetic data is from real.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            
        Returns:
            DetectionReport with scores
        """
        # Prepare combined dataset
        X, y, feature_cols = self._prepare_detection_data(real_data, synthetic_data)
        
        if X is None:
            return DetectionReport(
                overall_score=0.5,
                detection_accuracy=0.5,
                detection_auc=0.5,
                recommendations=["Could not prepare data for detection evaluation."],
            )
        
        logger.info(f"Evaluating detectability with {len(feature_cols)} features")
        
        # Try multiple classifiers
        model_results = {}
        all_scores = []
        all_aucs = []
        
        classifiers = {
            "random_forest": RandomForestClassifier(
                n_estimators=50, max_depth=8, random_state=self.random_state, n_jobs=-1
            ),
            "logistic_regression": LogisticRegression(
                max_iter=500, random_state=self.random_state
            ),
        }
        
        for name, clf in classifiers.items():
            try:
                scores, auc, cv_scores = self._evaluate_classifier(clf, X, y)
                model_results[name] = {
                    "accuracy": round(scores, 4),
                    "auc": round(auc, 4),
                    "cv_mean": round(np.mean(cv_scores), 4),
                    "cv_std": round(np.std(cv_scores), 4),
                }
                all_scores.append(scores)
                all_aucs.append(auc)
            except Exception as e:
                logger.warning(f"Classifier {name} failed: {e}")
                model_results[name] = {"error": str(e)}
        
        if not all_scores:
            return DetectionReport(
                overall_score=0.5,
                detection_accuracy=0.5,
                detection_auc=0.5,
                recommendations=["All classifiers failed. Data may have issues."],
            )
        
        # Use best (worst for us) detection accuracy
        best_accuracy = max(all_scores)
        best_auc = max(all_aucs)
        
        # Get feature importances from best model
        distinguishing_features = self._get_distinguishing_features(
            X, y, feature_cols
        )
        
        # Calculate overall score (inverse of detection - higher = better synthetic)
        # If accuracy is 0.5 (random), score is 1.0
        # If accuracy is 1.0 (perfect detection), score is 0.0
        # Clamp between 0 and 1
        overall_score = max(0, min(1, 1 - 2 * (best_accuracy - 0.5)))
        
        # Cross-validation details
        cv_scores = self._cross_validate(X, y)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            best_accuracy, distinguishing_features
        )
        
        return DetectionReport(
            overall_score=round(overall_score, 3),
            detection_accuracy=round(best_accuracy, 3),
            detection_auc=round(best_auc, 3),
            cv_scores=[round(s, 4) for s in cv_scores],
            cv_mean=round(np.mean(cv_scores), 4),
            cv_std=round(np.std(cv_scores), 4),
            model_results=model_results,
            distinguishing_features=distinguishing_features[:10],
            recommendations=recommendations,
        )
    
    def _prepare_detection_data(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[str]]:
        """Prepare data for detection task."""
        try:
            # Use only common columns
            common_cols = list(set(real_data.columns) & set(synthetic_data.columns))
            if not common_cols:
                return None, None, []
            
            real_df = real_data[common_cols].copy()
            synth_df = synthetic_data[common_cols].copy()
            
            # Add labels (0 = real, 1 = synthetic)
            real_df['__is_synthetic__'] = 0
            synth_df['__is_synthetic__'] = 1
            
            # Combine
            combined = pd.concat([real_df, synth_df], ignore_index=True)
            
            # Shuffle
            combined = combined.sample(frac=1, random_state=self.random_state).reset_index(drop=True)
            
            y = combined['__is_synthetic__'].values
            X = combined.drop(columns=['__is_synthetic__'])
            
            # Limit features
            if len(X.columns) > self.max_features:
                variances = []
                for col in X.columns:
                    if pd.api.types.is_numeric_dtype(X[col]):
                        variances.append((col, X[col].var()))
                    else:
                        variances.append((col, X[col].nunique()))
                variances.sort(key=lambda x: x[1], reverse=True)
                X = X[[v[0] for v in variances[:self.max_features]]]
            
            feature_cols = list(X.columns)
            
            # Encode categoricals
            for col in X.select_dtypes(include=['object', 'category']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].fillna('__missing__'))
            
            # Fill nulls
            X = X.fillna(0)
            
            # Scale
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            return X_scaled, y, feature_cols
            
        except Exception as e:
            logger.warning(f"Detection data preparation failed: {e}")
            return None, None, []
    
    def _evaluate_classifier(
        self,
        clf,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[float, float, List[float]]:
        """Evaluate a single classifier."""
        cv = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        
        # Cross-validation scores
        cv_scores = cross_val_score(clf, X, y, cv=cv, scoring='accuracy')
        
        # Fit on all data for AUC
        clf.fit(X, y)
        y_proba = clf.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, y_proba)
        
        return np.mean(cv_scores), auc, list(cv_scores)
    
    def _cross_validate(self, X: np.ndarray, y: np.ndarray) -> List[float]:
        """Run cross-validation with best model."""
        clf = RandomForestClassifier(
            n_estimators=50, max_depth=8, random_state=self.random_state, n_jobs=-1
        )
        cv = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        return list(cross_val_score(clf, X, y, cv=cv, scoring='accuracy'))
    
    def _get_distinguishing_features(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_cols: List[str],
    ) -> List[Tuple[str, float]]:
        """Get features that most distinguish real from synthetic."""
        try:
            clf = RandomForestClassifier(
                n_estimators=50, max_depth=8, random_state=self.random_state, n_jobs=-1
            )
            clf.fit(X, y)
            
            importances = clf.feature_importances_
            feature_importance = list(zip(feature_cols, importances))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            return [(name, round(imp, 4)) for name, imp in feature_importance]
            
        except Exception as e:
            logger.warning(f"Feature importance extraction failed: {e}")
            return []
    
    def _generate_recommendations(
        self,
        detection_accuracy: float,
        distinguishing_features: List[Tuple[str, float]],
    ) -> List[str]:
        """Generate recommendations based on detection results."""
        recommendations = []
        
        if detection_accuracy <= 0.55:
            recommendations.append(
                "Excellent! Synthetic data is nearly indistinguishable from real data."
            )
        elif detection_accuracy <= 0.65:
            recommendations.append(
                "Good synthetic quality. Minor detectable differences exist."
            )
        elif detection_accuracy <= 0.75:
            recommendations.append(
                "Moderate detectability. Consider using a more advanced synthesizer "
                "like CTGAN or TVAE for better results."
            )
        else:
            recommendations.append(
                "High detectability indicates quality issues. The synthetic data "
                "has noticeable patterns different from real data."
            )
        
        if distinguishing_features and detection_accuracy > 0.6:
            top_features = [f[0] for f in distinguishing_features[:3]]
            recommendations.append(
                f"Most distinguishing columns: {', '.join(top_features)}. "
                "These columns may need special attention."
            )
        
        return recommendations
