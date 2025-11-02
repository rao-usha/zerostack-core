import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm

class SyntheticDataGenerator:
    """Generate synthetic data that preserves statistical properties of original data"""
    
    def generate(self, df: pd.DataFrame, num_rows: int = 1000) -> pd.DataFrame:
        """Generate synthetic data based on original dataset"""
        synthetic_data = {}
        
        for column in df.columns:
            col_data = df[column]
            
            # Handle different data types
            if pd.api.types.is_numeric_dtype(col_data):
                # For numeric columns, use Gaussian distribution or preserve distribution
                if col_data.nunique() > 10:  # Continuous
                    mean = col_data.mean()
                    std = col_data.std()
                    # Clip to reasonable range
                    min_val = col_data.min()
                    max_val = col_data.max()
                    
                    # Generate synthetic data
                    synthetic_col = np.random.normal(mean, std, num_rows)
                    synthetic_col = np.clip(synthetic_col, min_val, max_val)
                    synthetic_data[column] = synthetic_col
                else:  # Discrete numeric
                    # Use distribution
                    synthetic_data[column] = np.random.choice(
                        col_data.unique(),
                        size=num_rows,
                        p=self._get_probabilities(col_data)
                    )
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                # For datetime, generate dates in similar range
                min_date = col_data.min()
                max_date = col_data.max()
                date_range = (max_date - min_date).days
                synthetic_data[column] = pd.date_range(
                    min_date,
                    periods=num_rows,
                    freq='D'
                )[:num_rows]
            else:
                # For categorical, preserve distribution
                synthetic_data[column] = np.random.choice(
                    col_data.unique(),
                    size=num_rows,
                    p=self._get_probabilities(col_data)
                )
        
        return pd.DataFrame(synthetic_data)
    
    def _get_probabilities(self, series: pd.Series) -> np.ndarray:
        """Calculate probability distribution for categorical/discrete data"""
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)
        
        # Create probability array matching unique values
        unique_values = series.unique()
        prob_array = np.array([probabilities.get(val, 0) for val in unique_values])
        
        # Normalize to ensure sum is 1
        if prob_array.sum() > 0:
            prob_array = prob_array / prob_array.sum()
        else:
            prob_array = np.ones(len(unique_values)) / len(unique_values)
        
        return prob_array

