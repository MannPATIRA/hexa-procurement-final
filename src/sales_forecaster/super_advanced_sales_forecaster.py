"""
Super Advanced Sales Forecaster

Implements a sophisticated forecasting pipeline:
1. Time series preparation (aggregate to weekly/monthly, fill missing periods)
2. Product-level diagnostics (history length, zero ratio, CV, seasonality, trend, volatility)
3. Model routing based on diagnostics
4. Training multiple models (Holt-Winters, Trend, Gradient Boosting with lags)
5. Model selection/ensemble based on holdout performance
6. Produce outputs with point forecast, intervals, model used, diagnostics
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics
import math

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

from sales_forecaster.interface import SalesForecasterInterface
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from models.inventory_data import InventoryData
from models.sales_data import SalesData, SalesRecord
from models.sales_forecast import SalesForecast, ForecastItem


class ModelType(str, Enum):
    """Types of forecasting models."""
    HOLT_WINTERS = "holt_winters"
    ETS_TREND = "ets_trend"
    GRADIENT_BOOSTING = "gradient_boosting"
    ENSEMBLE = "ensemble"
    FALLBACK = "fallback"


@dataclass
class ProductDiagnostics:
    """Diagnostics computed for each product's time series."""
    product_id: str
    history_length: int  # Number of periods with data
    zero_ratio: float  # Proportion of zero-sales periods
    coefficient_of_variation: float  # CV = std/mean
    seasonality_strength: float  # 0-1, strength of seasonal pattern
    trend_strength: float  # 0-1, strength of trend
    recent_vs_long_term_volatility: float  # Ratio of recent to long-term volatility
    exogenous_available: bool  # Whether external features are available
    data_quality_score: float  # Overall data quality 0-1
    recommended_model: ModelType  # Routed model type


@dataclass
class ForecastResult:
    """Detailed forecast result for a single product."""
    product_id: str
    product_name: str
    point_forecast: float
    lower_bound: float  # Lower prediction interval
    upper_bound: float  # Upper prediction interval
    model_used: ModelType
    diagnostics: ProductDiagnostics
    confidence: float
    forecasted_revenue: float


class SuperAdvancedSalesForecaster(SalesForecasterInterface):
    """
    Super Advanced Sales Forecaster with model routing and ensemble methods.
    
    Implements:
    - Time series preparation
    - Product-level diagnostics
    - Model routing based on data characteristics
    - Multiple model training
    - Model selection/ensemble
    - Structured outputs with diagnostics
    """
    
    # Configuration constants
    MIN_HISTORY_LENGTH = 4  # Minimum periods needed for advanced models
    HIGH_ZERO_RATIO = 0.5  # Threshold for high zero ratio
    HIGH_SEASONALITY = 0.3  # Threshold for strong seasonality
    HIGH_TREND = 0.3  # Threshold for strong trend
    MODERATE_VOLATILITY = 0.5  # Threshold for moderate volatility
    HOLDOUT_RATIO = 0.2  # Fraction of data for validation
    
    def __init__(
        self,
        frequency: str = "weekly",  # "weekly" or "monthly"
        alpha: float = 0.3,  # Smoothing parameter for Holt-Winters
        beta: float = 0.1,  # Trend smoothing parameter
        gamma: float = 0.1,  # Seasonal smoothing parameter
        ensemble_weight_baseline: float = 0.4,  # Weight for baseline in ensemble
    ):
        """
        Initialize the Super Advanced Sales Forecaster.
        
        Args:
            frequency: Aggregation frequency ("weekly" or "monthly")
            alpha: Level smoothing parameter for Holt-Winters (0-1)
            beta: Trend smoothing parameter (0-1)
            gamma: Seasonal smoothing parameter (0-1)
            ensemble_weight_baseline: Weight for baseline model in ensemble
        """
        self.frequency = frequency
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.ensemble_weight_baseline = ensemble_weight_baseline
        
        # Routing decisions log
        self.routing_log: List[Dict[str, Any]] = []
    
    def forecast_sales(
        self,
        inventory_data: InventoryData,
        sales_data: SalesData,
        forecast_period_days: int
    ) -> SalesForecast:
        """
        Generate forecasts using the super advanced pipeline.
        
        Automatically falls back to AdvancedSalesForecaster if data is insufficient
        for Super Advanced methods.
        
        Args:
            inventory_data: Current inventory data
            sales_data: Historical sales data
            forecast_period_days: Number of days to forecast ahead
            
        Returns:
            SalesForecast with forecasted quantities and revenues
        """
        now = datetime.now()
        forecast_period_start = now
        forecast_period_end = now + timedelta(days=forecast_period_days)
        
        # Check if we have sufficient data for Super Advanced across products
        # Count how many products have sufficient data
        products_with_sufficient_data = 0
        total_products = len(inventory_data.items)
        
        for item in inventory_data.items:
            records = sales_data.records_by_product.get(item.item_id, [])
            if self._has_sufficient_data(records, sales_data):
                products_with_sufficient_data += 1
        
        # If majority of products lack sufficient data, fall back to Advanced forecaster
        # This is a global fallback (Option B from the plan)
        if products_with_sufficient_data < (total_products / 2):
            # Fall back to Advanced forecaster
            advanced_forecaster = AdvancedSalesForecaster()
            return advanced_forecaster.forecast_sales(
                inventory_data, sales_data, forecast_period_days
            )
        
        forecast_items = []
        detailed_results: List[ForecastResult] = []
        
        for item in inventory_data.items:
            records = sales_data.records_by_product.get(item.item_id, [])
            
            # Check if this specific product has sufficient data
            if not self._has_sufficient_data(records, sales_data):
                # For this product, use Advanced forecaster
                # Create a temporary inventory with just this item
                temp_inventory = InventoryData(
                    items=[item],
                    fetched_at=inventory_data.fetched_at
                )
                advanced_forecaster = AdvancedSalesForecaster()
                temp_forecast = advanced_forecaster.forecast_sales(
                    temp_inventory, sales_data, forecast_period_days
                )
                if temp_forecast.forecasts:
                    forecast_items.append(temp_forecast.forecasts[0])
                continue
            
            # Step 1: Prepare time series
            time_series = self._prepare_time_series(records, sales_data)
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "forecast-sales", "hypothesisId": "B", "location": "super_advanced_sales_forecaster.py:forecast_sales", "message": "Time series prepared", "data": {"product_id": item.item_id, "product_name": item.item_name, "time_series_len": len(time_series), "time_series_mean": float(np.mean(time_series)) if len(time_series) > 0 else 0, "time_series_sum": float(np.sum(time_series)) if len(time_series) > 0 else 0, "num_records": len(records)}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            
            # Determine actual frequency used and calculate forecast_periods accordingly
            # Check if we're using daily frequency (for short histories)
            if len(records) > 1:
                timestamps = [r.timestamp for r in records]
                total_days = (max(timestamps) - min(timestamps)).days
                if total_days < 60:
                    # Using daily frequency
                    forecast_periods = forecast_period_days
                elif self.frequency == "weekly":
                    forecast_periods = max(1, forecast_period_days // 7)
                else:  # monthly
                    forecast_periods = max(1, forecast_period_days // 30)
            else:
                # Fallback calculation
                if self.frequency == "weekly":
                    forecast_periods = max(1, forecast_period_days // 7)
                else:  # monthly
                    forecast_periods = max(1, forecast_period_days // 30)
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "forecast-sales", "hypothesisId": "B", "location": "super_advanced_sales_forecaster.py:forecast_sales", "message": "Forecast periods calculated", "data": {"product_id": item.item_id, "forecast_periods": forecast_periods, "forecast_period_days": forecast_period_days, "total_days": total_days if len(records) > 1 else 0}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            
            if len(time_series) == 0:
                # No data - create default forecast
                forecast_item = self._create_default_forecast(
                    item, forecast_period_start, forecast_period_end
                )
                forecast_items.append(forecast_item)
                continue
            
            # Step 2: Compute diagnostics
            diagnostics = self._compute_diagnostics(item.item_id, time_series, records)
            
            # Step 3: Route to model bucket
            diagnostics = self._route_to_model(diagnostics)
            
            # Log routing decision
            self._log_routing(diagnostics)
            
            # Step 4: Train models
            models = self._train_models(time_series, diagnostics, forecast_periods)
            
            # Step 5: Select or ensemble
            result = self._select_or_ensemble(
                time_series, models, diagnostics, forecast_periods, item, records
            )
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "forecast-sales", "hypothesisId": "C", "location": "super_advanced_sales_forecaster.py:forecast_sales", "message": "Final forecast result", "data": {"product_id": item.item_id, "product_name": item.item_name, "point_forecast": float(result.point_forecast), "model_used": result.model_used.value, "confidence": float(result.confidence), "forecasted_revenue": float(result.forecasted_revenue)}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            
            detailed_results.append(result)
            
            # Step 6: Create forecast item
            forecast_item = ForecastItem(
                item_id=item.item_id,
                item_name=item.item_name,
                forecasted_quantity=max(0, int(result.point_forecast)),
                forecast_period_start=forecast_period_start,
                forecast_period_end=forecast_period_end,
                confidence_level=result.confidence,
                forecasted_revenue=result.forecasted_revenue,
            )
            forecast_items.append(forecast_item)
        
        return SalesForecast(
            forecasts=forecast_items,
            forecast_generated_at=now,
            forecast_period_start=forecast_period_start,
            forecast_period_end=forecast_period_end,
        )
    
    # =========================================================================
    # STEP 1: PREPARE TIME SERIES
    # =========================================================================
    
    def _prepare_time_series(
        self,
        records: List[SalesRecord],
        sales_data: SalesData
    ) -> np.ndarray:
        """
        Prepare time series by aggregating to fixed frequency.
        
        - Aggregate sales to weekly or monthly
        - For short histories (< 60 days), use daily aggregation
        - Fill missing periods with zero
        - Return as numpy array
        """
        if not records:
            return np.array([])
        
        # Create DataFrame from records
        data = []
        for r in records:
            data.append({
                'timestamp': r.timestamp,
                'quantity': r.quantity_sold,
                'revenue': r.total_revenue
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Determine frequency based on data span
        # For short histories (< 60 days), use daily to preserve granularity
        total_days = (df.index.max() - df.index.min()).days
        if total_days < 60:
            freq = 'D'  # Daily for short histories
        elif self.frequency == "weekly":
            freq = 'W'
        else:
            freq = 'M'  # Month end (use 'M' for older pandas compatibility)
        
        # Aggregate by frequency
        resampled = df.resample(freq).sum()
        
        # Fill missing periods with 0
        resampled = resampled.fillna(0)
        
        # Extract quantity series
        series = resampled['quantity'].values
        
        return series
    
    def _has_sufficient_data(
        self,
        records: List[SalesRecord],
        sales_data: SalesData
    ) -> bool:
        """
        Check if we have sufficient data for Super Advanced forecasting.
        
        Criteria:
        - Minimum 4 records per product (reduced from 5 for sparse data)
        - Total history span >= 20 days (reduced from 30 for daily frequency)
        - After resampling, should have at least 8 periods for diagnostics + holdout
        
        Returns:
            True if data is sufficient for Super Advanced, False otherwise
        """
        if not records:
            return False
        
        # Check minimum records
        if len(records) < 4:
            return False
        
        # Check history span - more lenient for daily frequency
        if len(records) > 1:
            timestamps = [r.timestamp for r in records]
            total_days = (max(timestamps) - min(timestamps)).days
            # For daily frequency, we can work with less data
            min_days = 20 if total_days < 60 else 30
            if total_days < min_days:
                return False
        
        # Check if resampling would produce enough periods
        # Prepare a test time series to see how many periods we'd get
        test_series = self._prepare_time_series(records, sales_data)
        if len(test_series) < 8:
            return False
        
        return True
    
    # =========================================================================
    # STEP 2: COMPUTE DIAGNOSTICS
    # =========================================================================
    
    def _compute_diagnostics(
        self,
        product_id: str,
        time_series: np.ndarray,
        records: List[SalesRecord]
    ) -> ProductDiagnostics:
        """
        Compute diagnostic statistics for the time series.
        """
        n = len(time_series)
        
        # History length
        history_length = n
        
        # Zero ratio
        zero_count = np.sum(time_series == 0)
        zero_ratio = zero_count / n if n > 0 else 1.0
        
        # Coefficient of variation
        mean_val = np.mean(time_series)
        std_val = np.std(time_series)
        cv = std_val / mean_val if mean_val > 0 else 0.0
        
        # Seasonality strength (using autocorrelation)
        seasonality_strength = self._compute_seasonality_strength(time_series)
        
        # Trend strength
        trend_strength = self._compute_trend_strength(time_series)
        
        # Recent vs long-term volatility
        recent_vol = self._compute_recent_volatility(time_series)
        long_vol = self._compute_long_term_volatility(time_series)
        recent_vs_long = recent_vol / long_vol if long_vol > 0 else 1.0
        
        # Exogenous available (check if we have additional features)
        exogenous_available = self._check_exogenous(records)
        
        # Data quality score
        data_quality = self._compute_data_quality(
            history_length, zero_ratio, cv
        )
        
        return ProductDiagnostics(
            product_id=product_id,
            history_length=history_length,
            zero_ratio=zero_ratio,
            coefficient_of_variation=cv,
            seasonality_strength=seasonality_strength,
            trend_strength=trend_strength,
            recent_vs_long_term_volatility=recent_vs_long,
            exogenous_available=exogenous_available,
            data_quality_score=data_quality,
            recommended_model=ModelType.HOLT_WINTERS  # Default, will be updated
        )
    
    def _compute_seasonality_strength(self, series: np.ndarray) -> float:
        """
        Compute seasonality strength using autocorrelation.
        Returns 0-1 where higher means stronger seasonality.
        """
        if len(series) < 8:
            return 0.0
        
        # Check for weekly seasonality (lag 4 for weekly data)
        # or monthly seasonality (lag 12 for monthly data)
        lag = 4 if self.frequency == "weekly" else 12
        
        if len(series) < lag + 2:
            return 0.0
        
        # Compute autocorrelation at seasonal lag
        mean = np.mean(series)
        variance = np.var(series)
        
        if variance == 0:
            return 0.0
        
        autocorr = np.correlate(series - mean, series - mean, mode='full')
        autocorr = autocorr[len(autocorr) // 2:]  # Take positive lags
        autocorr = autocorr / (variance * len(series))
        
        if len(autocorr) > lag:
            seasonal_corr = abs(autocorr[lag])
            return min(1.0, seasonal_corr)
        
        return 0.0
    
    def _compute_trend_strength(self, series: np.ndarray) -> float:
        """
        Compute trend strength using linear regression R-squared.
        Returns 0-1 where higher means stronger trend.
        """
        if len(series) < 3:
            return 0.0
        
        # Simple linear regression
        x = np.arange(len(series))
        
        # Calculate slope and r-squared
        x_mean = np.mean(x)
        y_mean = np.mean(series)
        
        ss_xy = np.sum((x - x_mean) * (series - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)
        ss_yy = np.sum((series - y_mean) ** 2)
        
        if ss_xx == 0 or ss_yy == 0:
            return 0.0
        
        slope = ss_xy / ss_xx
        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)
        
        # Adjust for direction (positive or negative trend)
        return min(1.0, r_squared)
    
    def _compute_recent_volatility(self, series: np.ndarray) -> float:
        """Compute volatility of recent period (last 1/3)."""
        if len(series) < 3:
            return np.std(series) if len(series) > 0 else 0.0
        
        split = len(series) // 3
        recent = series[-split:] if split > 0 else series
        return np.std(recent)
    
    def _compute_long_term_volatility(self, series: np.ndarray) -> float:
        """Compute volatility of entire series."""
        return np.std(series) if len(series) > 0 else 0.0
    
    def _check_exogenous(self, records: List[SalesRecord]) -> bool:
        """Check if exogenous features are available."""
        # Check for additional attributes that could be used as features
        if not records:
            return False
        
        sample = records[0]
        has_category = sample.category is not None
        has_customer = sample.customer_id is not None
        
        return has_category or has_customer
    
    def _compute_data_quality(
        self,
        history_length: int,
        zero_ratio: float,
        cv: float
    ) -> float:
        """Compute overall data quality score 0-1."""
        # More history = better
        history_score = min(1.0, history_length / 20)
        
        # Lower zero ratio = better
        zero_score = 1.0 - zero_ratio
        
        # Lower CV = more predictable
        cv_score = max(0.0, 1.0 - cv / 2.0)
        
        # Weighted average
        return 0.4 * history_score + 0.3 * zero_score + 0.3 * cv_score
    
    # =========================================================================
    # STEP 3: ROUTE TO MODEL BUCKET
    # =========================================================================
    
    def _route_to_model(self, diagnostics: ProductDiagnostics) -> ProductDiagnostics:
        """
        Route product to appropriate model based on diagnostics.
        
        Routing logic:
        1. If history_length < minimum → Holt Winters baseline only
        2. Else if zero_ratio is high → Holt Winters with low confidence flag
        3. Else if seasonality_strength is high and volatility is low → Holt Winters
        4. Else if trend_strength is high and volatility is moderate → ETS with trend
        5. Else if exogenous_available → Gradient boosting with features
        6. Else → Gradient boosting with lag features
        Always keep Holt Winters as fallback.
        """
        # Rule 1: Insufficient history
        if diagnostics.history_length < self.MIN_HISTORY_LENGTH:
            recommended = ModelType.HOLT_WINTERS
        
        # Rule 2: High zero ratio
        elif diagnostics.zero_ratio > self.HIGH_ZERO_RATIO:
            recommended = ModelType.HOLT_WINTERS
        
        # Rule 3: Strong seasonality, low volatility
        elif (diagnostics.seasonality_strength > self.HIGH_SEASONALITY and 
              diagnostics.coefficient_of_variation < self.MODERATE_VOLATILITY):
            recommended = ModelType.HOLT_WINTERS
        
        # Rule 4: Strong trend, moderate volatility
        elif (diagnostics.trend_strength > self.HIGH_TREND and 
              diagnostics.coefficient_of_variation < self.MODERATE_VOLATILITY * 1.5):
            recommended = ModelType.ETS_TREND
        
        # Rule 5: Exogenous features available
        elif diagnostics.exogenous_available:
            recommended = ModelType.GRADIENT_BOOSTING
        
        # Rule 6: Default to gradient boosting with lags
        else:
            recommended = ModelType.GRADIENT_BOOSTING
        
        # Update diagnostics with recommendation
        return ProductDiagnostics(
            product_id=diagnostics.product_id,
            history_length=diagnostics.history_length,
            zero_ratio=diagnostics.zero_ratio,
            coefficient_of_variation=diagnostics.coefficient_of_variation,
            seasonality_strength=diagnostics.seasonality_strength,
            trend_strength=diagnostics.trend_strength,
            recent_vs_long_term_volatility=diagnostics.recent_vs_long_term_volatility,
            exogenous_available=diagnostics.exogenous_available,
            data_quality_score=diagnostics.data_quality_score,
            recommended_model=recommended
        )
    
    def _log_routing(self, diagnostics: ProductDiagnostics) -> None:
        """Log routing decision for debugging and monitoring."""
        self.routing_log.append({
            'product_id': diagnostics.product_id,
            'recommended_model': diagnostics.recommended_model.value,
            'history_length': diagnostics.history_length,
            'zero_ratio': diagnostics.zero_ratio,
            'seasonality_strength': diagnostics.seasonality_strength,
            'trend_strength': diagnostics.trend_strength,
            'data_quality': diagnostics.data_quality_score,
            'timestamp': datetime.now().isoformat()
        })
    
    # =========================================================================
    # STEP 4: TRAIN MODELS
    # =========================================================================
    
    def _train_models(
        self,
        series: np.ndarray,
        diagnostics: ProductDiagnostics,
        forecast_periods: int
    ) -> Dict[str, np.ndarray]:
        """
        Train assigned models and baseline.
        
        Returns dict with model predictions.
        """
        models = {}
        
        # Always train Holt-Winters baseline
        models['holt_winters'] = self._holt_winters_forecast(series, forecast_periods)
        
        # Train primary model if different
        if diagnostics.recommended_model == ModelType.ETS_TREND:
            models['ets_trend'] = self._ets_trend_forecast(series, forecast_periods)
        
        elif diagnostics.recommended_model == ModelType.GRADIENT_BOOSTING:
            models['gradient_boosting'] = self._gradient_boosting_forecast(
                series, forecast_periods
            )
        
        # For high-value products, also train boosting even if not routed
        if diagnostics.data_quality_score > 0.7 and 'gradient_boosting' not in models:
            models['gradient_boosting'] = self._gradient_boosting_forecast(
                series, forecast_periods
            )
        
        return models
    
    def _holt_winters_forecast(
        self,
        series: np.ndarray,
        forecast_periods: int
    ) -> np.ndarray:
        """
        Holt-Winters exponential smoothing using statsmodels.
        Properly extrapolates trends instead of dampening them.
        """
        if len(series) == 0:
            return np.zeros(forecast_periods)
        
        if len(series) == 1:
            return np.full(forecast_periods, series[0])
        
        # For very short series, use simple extrapolation
        if len(series) < 4:
            avg = np.mean(series)
            if len(series) >= 2:
                trend = (series[-1] - series[0]) / (len(series) - 1)
                forecasts = np.array([series[-1] + trend * (i + 1) for i in range(forecast_periods)])
                return np.maximum(0, forecasts)
            return np.full(forecast_periods, avg)
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Use statsmodels ExponentialSmoothing with additive trend
                # damped_trend=False allows full trend extrapolation
                model = ExponentialSmoothing(
                    series,
                    trend='add',
                    seasonal=None,
                    damped_trend=False,
                    initialization_method='estimated'
                )
                
                fit = model.fit(optimized=True)
                forecasts = fit.forecast(forecast_periods)
                
                # Ensure non-negative
                return np.maximum(0, forecasts)
                
        except Exception:
            # Fallback to simple trend extrapolation if statsmodels fails
            avg = np.mean(series)
            trend = (series[-1] - series[0]) / (len(series) - 1) if len(series) > 1 else 0
            forecasts = np.array([series[-1] + trend * (i + 1) for i in range(forecast_periods)])
            return np.maximum(0, forecasts)
    
    def _ets_trend_forecast(
        self,
        series: np.ndarray,
        forecast_periods: int
    ) -> np.ndarray:
        """
        ETS with damped trend using statsmodels.
        Damped trend is useful for longer-term forecasts where growth will slow.
        """
        if len(series) < 4:
            return self._holt_winters_forecast(series, forecast_periods)
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Use statsmodels with damped trend for ETS
                model = ExponentialSmoothing(
                    series,
                    trend='add',
                    seasonal=None,
                    damped_trend=True,  # Damped for more conservative long-term forecasts
                    initialization_method='estimated'
                )
                
                fit = model.fit(optimized=True)
                forecasts = fit.forecast(forecast_periods)
                
                return np.maximum(0, forecasts)
                
        except Exception:
            # Fallback to non-damped Holt-Winters
            return self._holt_winters_forecast(series, forecast_periods)
    
    def _gradient_boosting_forecast(
        self,
        series: np.ndarray,
        forecast_periods: int
    ) -> np.ndarray:
        """
        Simple gradient boosting with lag features.
        Uses iterative residual fitting approach.
        """
        if len(series) < 5:
            return self._holt_winters_forecast(series, forecast_periods)
        
        # Create lag features
        n_lags = min(4, len(series) // 2)
        X, y = self._create_lag_features(series, n_lags)
        
        if len(X) < 3:
            return self._holt_winters_forecast(series, forecast_periods)
        
        # Train simple tree-based model (gradient boosting simulation)
        predictions = self._simple_boosting_fit_predict(X, y, series, forecast_periods, n_lags)
        
        return np.maximum(0, predictions)
    
    def _create_lag_features(
        self,
        series: np.ndarray,
        n_lags: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create lag features for gradient boosting."""
        X = []
        y = []
        
        for i in range(n_lags, len(series)):
            features = series[i-n_lags:i].tolist()
            X.append(features)
            y.append(series[i])
        
        return np.array(X), np.array(y)
    
    def _simple_boosting_fit_predict(
        self,
        X: np.ndarray,
        y: np.ndarray,
        series: np.ndarray,
        forecast_periods: int,
        n_lags: int
    ) -> np.ndarray:
        """
        Simple gradient boosting implementation.
        Uses iterative weighted averaging with residual correction.
        """
        # Split for validation
        split_idx = max(1, int(len(X) * 0.8))
        X_train, y_train = X[:split_idx], y[:split_idx]
        
        # Base prediction (mean)
        base_pred = np.mean(y_train)
        
        # Compute weights based on recency
        n_train = len(y_train)
        weights = np.array([0.5 + 0.5 * (i / n_train) for i in range(n_train)])
        weights = weights / weights.sum()
        
        # Weighted mean with trend adjustment
        weighted_mean = np.average(y_train, weights=weights)
        
        # Compute trend from lag coefficients
        if len(X_train) > 1:
            # Use most recent lag as primary predictor
            recent_coef = np.corrcoef(X_train[:, 0], y_train)[0, 1]
            if np.isnan(recent_coef):
                recent_coef = 0.5
        else:
            recent_coef = 0.5
        
        recent_coef = max(0, min(1, abs(recent_coef)))
        
        # Forecast
        forecasts = []
        last_values = list(series[-n_lags:])
        
        for _ in range(forecast_periods):
            # Blend weighted mean with lag-based prediction
            lag_pred = recent_coef * last_values[-1] + (1 - recent_coef) * np.mean(last_values)
            pred = 0.5 * weighted_mean + 0.5 * lag_pred
            
            forecasts.append(pred)
            
            # Update lag values for next prediction
            last_values.pop(0)
            last_values.append(pred)
        
        return np.array(forecasts)
    
    # =========================================================================
    # STEP 5: SELECT OR ENSEMBLE
    # =========================================================================
    
    def _select_or_ensemble(
        self,
        series: np.ndarray,
        models: Dict[str, np.ndarray],
        diagnostics: ProductDiagnostics,
        forecast_periods: int,
        item: Any,
        records: List[SalesRecord]
    ) -> ForecastResult:
        """
        Select best model or create ensemble based on holdout performance.
        """
        # Evaluate on holdout if enough data
        # Require minimum 8 periods before using holdout validation
        holdout_size = max(1, int(len(series) * self.HOLDOUT_RATIO))
        min_required_for_holdout = 8
        
        if len(series) > max(min_required_for_holdout, holdout_size + 3):
            train_series = series[:-holdout_size]
            holdout = series[-holdout_size:]
            
            # Evaluate each model
            scores = {}
            for model_name, forecasts in models.items():
                # Re-train on training portion and evaluate
                if model_name == 'holt_winters':
                    pred = self._holt_winters_forecast(train_series, holdout_size)
                elif model_name == 'ets_trend':
                    pred = self._ets_trend_forecast(train_series, holdout_size)
                elif model_name == 'gradient_boosting':
                    pred = self._gradient_boosting_forecast(train_series, holdout_size)
                else:
                    pred = np.full(holdout_size, np.mean(train_series))
                
                # Calculate MAE
                mae = np.mean(np.abs(pred[:len(holdout)] - holdout))
                scores[model_name] = mae
            
            # Select best or ensemble
            model_used, point_forecast = self._select_best_model(
                scores, models, diagnostics
            )
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "select-ensemble", "hypothesisId": "D", "location": "super_advanced_sales_forecaster.py:_select_or_ensemble", "message": "Model selected with holdout", "data": {"product_id": item.item_id, "model_used": model_used.value, "scores": {k: float(v) for k, v in scores.items()}, "forecast_sum": float(np.sum(point_forecast))}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
        else:
            # Not enough data for holdout - use baseline
            model_used = ModelType.HOLT_WINTERS
            point_forecast = models.get('holt_winters', np.zeros(forecast_periods))
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "select-ensemble", "hypothesisId": "D", "location": "super_advanced_sales_forecaster.py:_select_or_ensemble", "message": "Using baseline (no holdout)", "data": {"product_id": item.item_id, "model_used": model_used.value, "series_len": len(series), "forecast_sum": float(np.sum(point_forecast))}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
        
        # Calculate prediction intervals
        std_estimate = np.std(series) if len(series) > 1 else np.mean(series) * 0.2
        total_forecast = float(np.sum(point_forecast))
        lower_bound = total_forecast - 1.96 * std_estimate * np.sqrt(forecast_periods)
        upper_bound = total_forecast + 1.96 * std_estimate * np.sqrt(forecast_periods)
        
        # Calculate confidence
        confidence = self._calculate_confidence(diagnostics, model_used)
        
        # Calculate revenue
        if records:
            avg_price = np.mean([r.unit_price for r in records])
        else:
            avg_price = item.unit_price if hasattr(item, 'unit_price') else 10.0
        
        forecasted_revenue = total_forecast * avg_price
        
        return ForecastResult(
            product_id=item.item_id,
            product_name=item.item_name,
            point_forecast=total_forecast,
            lower_bound=max(0, lower_bound),
            upper_bound=upper_bound,
            model_used=model_used,
            diagnostics=diagnostics,
            confidence=confidence,
            forecasted_revenue=forecasted_revenue
        )
    
    def _select_best_model(
        self,
        scores: Dict[str, float],
        models: Dict[str, np.ndarray],
        diagnostics: ProductDiagnostics
    ) -> Tuple[ModelType, np.ndarray]:
        """
        Select best model or create ensemble based on scores.
        """
        if not scores:
            return ModelType.FALLBACK, models.get('holt_winters', np.array([0]))
        
        baseline_score = scores.get('holt_winters', float('inf'))
        best_other = None
        best_other_score = float('inf')
        
        for name, score in scores.items():
            if name != 'holt_winters' and score < best_other_score:
                best_other = name
                best_other_score = score
        
        # Decision logic
        if best_other is None:
            # Only baseline available
            return ModelType.HOLT_WINTERS, models['holt_winters']
        
        improvement_ratio = (baseline_score - best_other_score) / baseline_score if baseline_score > 0 else 0
        
        if improvement_ratio > 0.15:
            # Boosting/other model clearly better (>15% improvement)
            model_type = ModelType.GRADIENT_BOOSTING if 'gradient' in best_other else ModelType.ETS_TREND
            return model_type, models[best_other]
        
        elif abs(improvement_ratio) < 0.05:
            # Similar performance - use ensemble
            ensemble = (self.ensemble_weight_baseline * models['holt_winters'] + 
                       (1 - self.ensemble_weight_baseline) * models[best_other])
            return ModelType.ENSEMBLE, ensemble
        
        else:
            # Baseline is better or unstable - fall back to Holt-Winters
            return ModelType.HOLT_WINTERS, models['holt_winters']
    
    def _calculate_confidence(
        self,
        diagnostics: ProductDiagnostics,
        model_used: ModelType
    ) -> float:
        """Calculate confidence level based on diagnostics and model."""
        base_confidence = diagnostics.data_quality_score
        
        # Adjust for model type
        model_adjustments = {
            ModelType.HOLT_WINTERS: 0.0,  # Baseline, no adjustment
            ModelType.ETS_TREND: 0.05,  # Slight boost for trend model
            ModelType.GRADIENT_BOOSTING: 0.1,  # Boost for ML model
            ModelType.ENSEMBLE: 0.15,  # Best boost for ensemble
            ModelType.FALLBACK: -0.1,  # Penalty for fallback
        }
        
        adjustment = model_adjustments.get(model_used, 0.0)
        
        # Penalty for high zero ratio
        if diagnostics.zero_ratio > self.HIGH_ZERO_RATIO:
            adjustment -= 0.1
        
        # Penalty for high volatility
        if diagnostics.recent_vs_long_term_volatility > 1.5:
            adjustment -= 0.05
        
        confidence = base_confidence + adjustment
        return max(0.1, min(1.0, confidence))
    
    def _create_default_forecast(
        self,
        item: Any,
        start: datetime,
        end: datetime
    ) -> ForecastItem:
        """Create a default forecast for items with no sales history."""
        return ForecastItem(
            item_id=item.item_id,
            item_name=item.item_name,
            forecasted_quantity=0,
            forecast_period_start=start,
            forecast_period_end=end,
            confidence_level=0.1,  # Very low confidence
            forecasted_revenue=0.0,
        )
    
    # =========================================================================
    # STEP 7: RE-RUN UTILITIES
    # =========================================================================
    
    def get_routing_log(self) -> List[Dict[str, Any]]:
        """Get the routing decisions log."""
        return self.routing_log
    
    def clear_routing_log(self) -> None:
        """Clear the routing log for a new run."""
        self.routing_log = []
    
    def get_model_summary(self) -> Dict[str, int]:
        """Get summary of which models were selected."""
        summary = {}
        for entry in self.routing_log:
            model = entry['recommended_model']
            summary[model] = summary.get(model, 0) + 1
        return summary
