import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
import re

class ChatService:
    """Advanced natural language query interface for data with contextual understanding"""
    
    def __init__(self):
        self.conversation_context = []
    
    def query(self, query: str, df: Optional[pd.DataFrame] = None, dataset_id: Optional[str] = None) -> str:
        """Process natural language queries with advanced understanding"""
        query_lower = query.lower()
        
        if df is None:
            return self._handle_general_query(query)
        
        # Store query context
        self.conversation_context.append(query_lower)
        
        # Analyze query intent
        intent = self._detect_intent(query_lower)
        
        # Route to appropriate handler
        if intent == "overview":
            return self._generate_dataset_overview(df)
        elif intent == "statistics":
            return self._handle_statistics_query(query_lower, df)
        elif intent == "trends":
            return self._analyze_trends(query_lower, df)
        elif intent == "comparison":
            return self._handle_comparison(query_lower, df)
        elif intent == "insights":
            return self._generate_quick_insights(df)
        elif intent == "recommendations":
            return self._generate_recommendations(df)
        elif intent == "quality":
            return self._assess_data_quality(df)
        elif intent == "prediction":
            return self._handle_prediction_query(query_lower, df)
        elif intent == "correlation":
            return self._analyze_correlations(query_lower, df)
        else:
            return self._generate_intelligent_response(query, df)
    
    def _detect_intent(self, query: str) -> str:
        """Detect user's intent from the query"""
        # Overview intents
        if any(word in query for word in ["overview", "summary", "describe", "tell me about", "what is this"]):
            return "overview"
        
        # Statistics intents
        if any(word in query for word in ["mean", "average", "median", "max", "min", "sum", "total", "count"]):
            return "statistics"
        
        # Trend intents
        if any(word in query for word in ["trend", "pattern", "over time", "growing", "declining", "increasing", "decreasing"]):
            return "trends"
        
        # Comparison intents
        if any(word in query for word in ["compare", "difference", "between", "vs", "versus", "higher", "lower"]):
            return "comparison"
        
        # Insights intents
        if any(word in query for word in ["insight", "finding", "discover", "what should i know", "key takeaway"]):
            return "insights"
        
        # Recommendation intents
        if any(word in query for word in ["recommend", "suggest", "what should i", "next step", "action"]):
            return "recommendations"
        
        # Quality intents
        if any(word in query for word in ["quality", "missing", "null", "complete", "clean", "issue"]):
            return "quality"
        
        # Prediction intents
        if any(word in query for word in ["predict", "forecast", "future", "will", "expect"]):
            return "prediction"
        
        # Correlation intents
        if any(word in query for word in ["correlation", "relationship", "related", "connected", "affect"]):
            return "correlation"
        
        return "general"
    
    def _generate_dataset_overview(self, df: pd.DataFrame) -> str:
        """Generate comprehensive dataset overview"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        
        overview = [
            f"📊 **Dataset Overview**\n",
            f"• **Size**: {len(df):,} rows × {len(df.columns)} columns",
            f"• **Numeric Features**: {len(numeric_cols)} ({', '.join(numeric_cols[:3].tolist())}" + 
            (f", and {len(numeric_cols)-3} more" if len(numeric_cols) > 3 else "") + ")",
            f"• **Categorical Features**: {len(categorical_cols)}"
        ]
        
        # Data quality
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        overview.append(f"• **Completeness**: {100-missing_pct:.1f}%")
        
        # Key statistics
        if len(numeric_cols) > 0:
            overview.append(f"\n📈 **Quick Stats**:")
            for col in numeric_cols[:3]:
                mean_val = df[col].mean()
                std_val = df[col].std()
                cv = (std_val / mean_val * 100) if mean_val != 0 else 0
                overview.append(f"• {col}: avg {mean_val:.2f}, range [{df[col].min():.2f} - {df[col].max():.2f}]")
        
        overview.append(f"\n💡 **Tip**: Ask me about trends, correlations, or specific insights!")
        
        return "\n".join(overview)
    
    def _handle_statistics_query(self, query: str, df: pd.DataFrame) -> str:
        """Handle detailed statistics queries"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return "I couldn't find any numeric columns to calculate statistics. This dataset appears to contain only categorical data."
        
        # Detect which column is being asked about
        target_col = self._extract_column_name(query, df.columns.tolist())
        
        if target_col is None:
            target_col = numeric_cols[0]
        
        stats = {
            "mean": df[target_col].mean(),
            "median": df[target_col].median(),
            "std": df[target_col].std(),
            "min": df[target_col].min(),
            "max": df[target_col].max(),
            "q25": df[target_col].quantile(0.25),
            "q75": df[target_col].quantile(0.75)
        }
        
        # Calculate coefficient of variation for volatility insight
        cv = (stats['std'] / stats['mean'] * 100) if stats['mean'] != 0 else 0
        
        response = [
            f"📊 **Statistics for {target_col}**\n",
            f"• **Average**: {stats['mean']:.2f}",
            f"• **Median**: {stats['median']:.2f} (50th percentile)",
            f"• **Range**: {stats['min']:.2f} to {stats['max']:.2f}",
            f"• **Std Deviation**: {stats['std']:.2f}",
            f"• **Quartiles**: Q1={stats['q25']:.2f}, Q3={stats['q75']:.2f}",
            f"\n💡 **Insight**: This metric shows {'high' if cv > 50 else 'moderate' if cv > 25 else 'low'} volatility (CV: {cv:.1f}%)"
        ]
        
        # Detect outliers
        iqr = stats['q75'] - stats['q25']
        outliers = len(df[(df[target_col] < stats['q25'] - 1.5*iqr) | (df[target_col] > stats['q75'] + 1.5*iqr)])
        if outliers > 0:
            response.append(f"⚠️  **Alert**: {outliers} outliers detected ({outliers/len(df)*100:.1f}% of data)")
        
        return "\n".join(response)
    
    def _analyze_trends(self, query: str, df: pd.DataFrame) -> str:
        """Analyze trends in the data"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return "No numeric data available for trend analysis."
        
        trends = []
        for col in numeric_cols[:3]:
            if len(df) > 1:
                first_val = df[col].iloc[0]
                last_val = df[col].iloc[-1]
                change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                direction = "📈 increasing" if change > 5 else "📉 decreasing" if change < -5 else "➡️  stable"
                
                # Calculate momentum
                first_half = df[col].iloc[:len(df)//2].mean()
                second_half = df[col].iloc[len(df)//2:].mean()
                momentum = "accelerating" if second_half > first_half else "decelerating"
                
                trends.append(f"• **{col}**: {direction} ({change:+.1f}%), {momentum}")
        
        response = [
            f"📈 **Trend Analysis**\n"
        ] + trends
        
        response.append(f"\n💡 **Recommendation**: Monitor metrics showing high volatility for potential opportunities or risks.")
        
        return "\n".join(response)
    
    def _handle_comparison(self, query: str, df: pd.DataFrame) -> str:
        """Handle comparison queries between metrics or segments"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return "I need at least 2 numeric columns to make comparisons."
        
        # Compare top metrics
        comparisons = []
        for i in range(min(2, len(numeric_cols))):
            col = numeric_cols[i]
            mean_val = df[col].mean()
            median_val = df[col].median()
            
            # Compare mean vs median
            diff_pct = ((mean_val - median_val) / median_val * 100) if median_val != 0 else 0
            skew = "right-skewed (high values pulling up average)" if diff_pct > 10 else \
                   "left-skewed (low values pulling down average)" if diff_pct < -10 else "balanced"
            
            comparisons.append(f"• **{col}**: Mean={mean_val:.2f} vs Median={median_val:.2f} → {skew}")
        
        # Compare columns
        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            ratio = df[col1].mean() / df[col2].mean() if df[col2].mean() != 0 else 0
            comparisons.append(f"\n• **{col1} vs {col2}**: Ratio of {ratio:.2f}:1")
        
        return "📊 **Comparison Analysis**\n\n" + "\n".join(comparisons)
    
    def _generate_quick_insights(self, df: pd.DataFrame) -> str:
        """Generate quick actionable insights"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        insights = [f"💡 **Key Insights**\n"]
        
        # Data completeness
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_pct > 5:
            insights.append(f"⚠️  **Data Quality**: {missing_pct:.1f}% missing data - consider data cleaning")
        else:
            insights.append(f"✅ **Data Quality**: Excellent! Only {missing_pct:.1f}% missing")
        
        # Correlation insights
        if len(numeric_cols) >= 2:
            numeric_df = df[numeric_cols]
            corr_matrix = numeric_df.corr()
            
            # Find strongest correlation
            corr_values = corr_matrix.unstack()
            corr_values = corr_values[corr_values < 1.0].abs().sort_values(ascending=False)
            
            if len(corr_values) > 0:
                strongest = corr_values.index[0]
                corr_val = numeric_df.corr().loc[strongest[0], strongest[1]]
                strength = "strong" if abs(corr_val) > 0.7 else "moderate" if abs(corr_val) > 0.5 else "weak"
                insights.append(f"🔗 **Correlation**: {strongest[0]} and {strongest[1]} show {strength} relationship ({corr_val:.2f})")
        
        # Variability insights
        if len(numeric_cols) > 0:
            cvs = []
            for col in numeric_cols:
                if df[col].mean() != 0:
                    cv = df[col].std() / df[col].mean() * 100
                    cvs.append((col, cv))
            
            if cvs:
                most_volatile = max(cvs, key=lambda x: x[1])
                most_stable = min(cvs, key=lambda x: x[1])
                insights.append(f"📊 **Volatility**: {most_volatile[0]} is most volatile ({most_volatile[1]:.1f}% CV), {most_stable[0]} is most stable ({most_stable[1]:.1f}% CV)")
        
        insights.append(f"\n💡 **Tip**: Ask me to 'recommend next steps' for actionable guidance!")
        
        return "\n".join(insights)
    
    def _generate_recommendations(self, df: pd.DataFrame) -> str:
        """Generate strategic recommendations"""
        recommendations = [f"🎯 **Strategic Recommendations**\n"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Check data quality
        missing = df.isnull().sum()
        high_missing = missing[missing > len(df) * 0.1]
        if len(high_missing) > 0:
            recommendations.append(f"1. **Data Quality**: Address missing values in {', '.join(high_missing.index[:2])}")
        else:
            recommendations.append(f"1. **Data Quality**: ✅ Your data quality is good!")
        
        # Check for trends
        if len(numeric_cols) > 0 and len(df) > 1:
            declining_metrics = []
            for col in numeric_cols[:3]:
                if df[col].iloc[-1] < df[col].iloc[0]:
                    declining_metrics.append(col)
            
            if declining_metrics:
                recommendations.append(f"2. **Trends**: Monitor declining metrics: {', '.join(declining_metrics)}")
            else:
                recommendations.append(f"2. **Trends**: ✅ Metrics show positive momentum!")
        
        # Outlier recommendations
        if len(numeric_cols) > 0:
            outlier_cols = []
            for col in numeric_cols:
                Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)])
                if outliers > len(df) * 0.05:
                    outlier_cols.append(col)
            
            if outlier_cols:
                recommendations.append(f"3. **Anomalies**: Investigate outliers in {', '.join(outlier_cols[:2])}")
        
        recommendations.append(f"\n4. **Next Steps**: Consider building predictive models or generating detailed insights")
        recommendations.append(f"5. **Visualization**: Create charts to visualize trends and patterns")
        
        return "\n".join(recommendations)
    
    def _assess_data_quality(self, df: pd.DataFrame) -> str:
        """Assess data quality comprehensively"""
        quality_report = [f"🔍 **Data Quality Assessment**\n"]
        
        # Completeness
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = (1 - missing_cells / total_cells) * 100
        
        quality_report.append(f"• **Completeness**: {completeness:.1f}% " + 
                            ("✅ Excellent" if completeness > 95 else "⚠️  Needs attention"))
        
        # Missing data details
        missing = df.isnull().sum()
        cols_with_missing = missing[missing > 0]
        if len(cols_with_missing) > 0:
            quality_report.append(f"• **Missing Data**: {len(cols_with_missing)} columns affected")
            for col in cols_with_missing.index[:3]:
                pct = missing[col] / len(df) * 100
                quality_report.append(f"  - {col}: {missing[col]} values ({pct:.1f}%)")
        else:
            quality_report.append(f"• **Missing Data**: None! ✅")
        
        # Duplicates
        duplicates = df.duplicated().sum()
        quality_report.append(f"• **Duplicates**: {duplicates} rows " + 
                            ("✅ Clean" if duplicates == 0 else "⚠️  Consider deduplication"))
        
        # Consistency
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cvs = [df[col].std() / df[col].mean() for col in numeric_cols if df[col].mean() != 0]
            avg_cv = np.mean(cvs) if cvs else 0
            quality_report.append(f"• **Consistency**: {'High' if avg_cv < 0.5 else 'Moderate' if avg_cv < 1 else 'Low'} " +
                                f"(Avg CV: {avg_cv:.2f})")
        
        # Overall score
        overall_score = (completeness * 0.6 + (100 - duplicates/len(df)*100) * 0.4)
        quality_report.append(f"\n**Overall Quality Score**: {overall_score:.1f}/100 🎯")
        
        return "\n".join(quality_report)
    
    def _handle_prediction_query(self, query: str, df: pd.DataFrame) -> str:
        """Handle prediction-related queries"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return "Prediction requires numeric data. This dataset doesn't have numeric columns suitable for forecasting."
        
        # Simple trend-based prediction
        predictions = [f"🔮 **Prediction Insights**\n"]
        
        for col in numeric_cols[:2]:
            if len(df) > 1:
                # Calculate trend
                values = df[col].values
                trend = np.polyfit(range(len(values)), values, 1)[0]
                
                # Project next value
                next_value = values[-1] + trend
                change_pct = (trend / values[-1] * 100) if values[-1] != 0 else 0
                
                direction = "increase" if trend > 0 else "decrease"
                predictions.append(f"• **{col}**: Expected to {direction} to ~{next_value:.2f} ({change_pct:+.1f}%)")
        
        predictions.append(f"\n💡 **Note**: For accurate predictions, use the Predictive Models feature with more sophisticated algorithms!")
        
        return "\n".join(predictions)
    
    def _analyze_correlations(self, query: str, df: pd.DataFrame) -> str:
        """Deep correlation analysis"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return "I need at least 2 numeric columns to analyze correlations."
        
        corr_matrix = numeric_df.corr()
        
        # Find all strong correlations
        strong_corr = []
        for i, col1 in enumerate(corr_matrix.columns):
            for col2 in corr_matrix.columns[i+1:]:
                corr_val = corr_matrix.loc[col1, col2]
                if abs(corr_val) > 0.5:
                    strength = "very strong" if abs(corr_val) > 0.8 else "strong" if abs(corr_val) > 0.7 else "moderate"
                    direction = "positive" if corr_val > 0 else "negative"
                    strong_corr.append((col1, col2, corr_val, strength, direction))
        
        if not strong_corr:
            return "🔗 **Correlation Analysis**: No strong correlations found. Your metrics appear to be independent of each other."
        
        response = [f"🔗 **Correlation Analysis**\n"]
        
        for col1, col2, corr_val, strength, direction in strong_corr[:5]:
            icon = "📈" if direction == "positive" else "📉"
            response.append(f"{icon} **{col1} ↔ {col2}**: {strength} {direction} correlation ({corr_val:.3f})")
            
            # Add interpretation
            if direction == "positive":
                response.append(f"   → When {col1} increases, {col2} tends to increase")
            else:
                response.append(f"   → When {col1} increases, {col2} tends to decrease")
        
        response.append(f"\n💡 **Insight**: Use these relationships for predictive modeling or business strategy!")
        
        return "\n".join(response)
    
    def _extract_column_name(self, query: str, columns: List[str]) -> Optional[str]:
        """Extract column name from query"""
        query_lower = query.lower()
        for col in columns:
            if col.lower() in query_lower:
                return col
        return None
    
    def _handle_general_query(self, query: str) -> str:
        """Handle queries when no dataset is specified"""
        if "upload" in query.lower() or "add data" in query.lower():
            return "📁 To get started, upload a dataset in the **Data Upload** section. I'll be able to analyze it and answer your questions!"
        
        if "help" in query.lower() or "what can you do" in query.lower():
            return """🤖 **I can help you with:**

• 📊 Data analysis & statistics
• 📈 Trend identification & forecasting  
• 🔗 Correlation analysis
• 💡 Strategic insights & recommendations
• 🎯 Data quality assessment
• 📉 Anomaly detection
• 🔮 Predictive suggestions

**To get started**: Upload a dataset and ask me anything!

**Example questions**:
- "Give me an overview of this data"
- "What trends do you see?"
- "Are there any correlations?"
- "What should I focus on?"
- "Recommend next steps"
"""
        
        return "👋 Hi! I'm your AI data assistant. Upload a dataset to get started, or ask me 'what can you do' to learn more!"
    
    def _generate_intelligent_response(self, query: str, df: pd.DataFrame) -> str:
        """Generate contextually intelligent response"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        response = [
            f"🤔 I analyzed your question about this dataset with {len(df):,} rows.\n"
        ]
        
        # Provide relevant context
        if len(numeric_cols) > 0:
            response.append(f"📊 **Available metrics**: {', '.join(numeric_cols[:4].tolist())}")
            response.append(f"\n💡 **Try asking**:")
            response.append(f"• 'Show me trends'")
            response.append(f"• 'What are the key insights?'")
            response.append(f"• 'Are there any correlations?'")
            response.append(f"• 'Recommend next steps'")
        
        return "\n".join(response)
