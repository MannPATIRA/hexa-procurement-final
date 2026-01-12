from datetime import datetime, timedelta
from collections import defaultdict
from sales_forecaster.interface import SalesForecasterInterface
from models.inventory_data import InventoryData
from models.sales_data import SalesData
from models.sales_forecast import SalesForecast, ForecastItem
import statistics
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings


class AdvancedSalesForecaster(SalesForecasterInterface):
    """Advanced sales forecaster using Holt-Winters Exponential Smoothing from statsmodels."""
    
    MIN_DATA_POINTS = 4  # Minimum data points needed for Holt-Winters
    
    def __init__(self, smoothing_level: float = 0.3, smoothing_trend: float = 0.1):
        """Initialize with configurable smoothing parameters.
        
        Args:
            smoothing_level: Alpha parameter for level smoothing (0-1)
            smoothing_trend: Beta parameter for trend smoothing (0-1)
        """
        self.smoothing_level = smoothing_level
        self.smoothing_trend = smoothing_trend
    
    def forecast_sales(
        self, 
        inventory_data: InventoryData, 
        sales_data: SalesData, 
        forecast_period_days: int
    ) -> SalesForecast:
        """Generate an advanced sales forecast using Holt-Winters exponential smoothing."""
        now = datetime.now()
        forecast_period_start = now
        forecast_period_end = now + timedelta(days=forecast_period_days)
        
        historical_days = (sales_data.end_date - sales_data.start_date).days
        if historical_days == 0:
            historical_days = 1
        
        forecast_items = []
        
        for item in inventory_data.items:
            records = sales_data.records_by_product.get(item.item_id, [])
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"hypothesisId": "H5", "location": "advanced:forecast_sales:product_start", "message": "Processing product", "data": {"item_id": item.item_id, "item_name": item.item_name, "num_records": len(records), "total_qty": sum(r.quantity_sold for r in records) if records else 0}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            
            if not records:
                forecast_item = self._create_default_forecast(
                    item, forecast_period_start, forecast_period_end, forecast_period_days
                )
                forecast_items.append(forecast_item)
                continue
            
            # Prepare daily time series
            daily_series = self._prepare_daily_series(records, sales_data.start_date, sales_data.end_date)
            
            # Forecast using Holt-Winters
            forecasted_quantity, confidence = self._holt_winters_forecast(
                daily_series, forecast_period_days
            )
            
            # Calculate revenue forecast based on average price per unit
            total_revenue = sum(r.total_revenue for r in records)
            total_qty = sum(r.quantity_sold for r in records)
            avg_price = total_revenue / total_qty if total_qty > 0 else 0
            forecasted_revenue = forecasted_quantity * avg_price
            
            forecast_item = ForecastItem(
                item_id=item.item_id,
                item_name=item.item_name,
                forecasted_quantity=int(forecasted_quantity),
                forecast_period_start=forecast_period_start,
                forecast_period_end=forecast_period_end,
                confidence_level=confidence,
                forecasted_revenue=forecasted_revenue,
            )
            forecast_items.append(forecast_item)
        
        return SalesForecast(
            forecasts=forecast_items,
            forecast_generated_at=now,
            forecast_period_start=forecast_period_start,
            forecast_period_end=forecast_period_end,
        )
    
    def _prepare_daily_series(
        self, 
        records: list, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.Series:
        """Prepare a daily time series from sales records, filling missing days with 0."""
        # Aggregate sales by day
        daily_sales = defaultdict(float)
        for r in records:
            day = r.timestamp.date()
            daily_sales[day] += r.quantity_sold
        
        # Create complete date range
        start = start_date.date() if hasattr(start_date, 'date') else start_date
        end = end_date.date() if hasattr(end_date, 'date') else end_date
        date_range = pd.date_range(start=start, end=end, freq='D')
        
        # Fill in values (0 for missing days)
        values = [daily_sales.get(d.date(), 0) for d in date_range]
        
        return pd.Series(values, index=date_range)
    
    def _holt_winters_forecast(
        self, 
        series: pd.Series, 
        forecast_periods: int
    ) -> tuple[float, float]:
        """
        Generate forecast using statsmodels Holt-Winters Exponential Smoothing.
        
        Returns:
            tuple of (forecasted_quantity, confidence_level)
        """
        # #region agent log
        try:
            with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"hypothesisId": "H1", "location": "advanced:_holt_winters_forecast:entry", "message": "Entry", "data": {"series_len": len(series), "series_sum": float(series.sum()), "series_mean": float(series.mean()), "non_zero_count": int((series > 0).sum()), "forecast_periods": forecast_periods}, "timestamp": __import__('time').time() * 1000}) + '\n')
        except: pass
        # #endregion
        
        # Handle edge cases
        if len(series) == 0:
            return 0, 0.3
        
        if len(series) == 1:
            return series.iloc[0] * forecast_periods, 0.3
        
        # For very short series, use simple extrapolation
        if len(series) < self.MIN_DATA_POINTS:
            avg_daily = series.mean()
            # Simple trend from first to last
            if len(series) >= 2:
                trend = (series.iloc[-1] - series.iloc[0]) / (len(series) - 1)
                # Extrapolate from last value
                last_val = series.iloc[-1]
                total = sum(last_val + trend * (i + 1) for i in range(forecast_periods))
                total = max(0, total)  # Ensure non-negative
            else:
                total = avg_daily * forecast_periods
            return total, 0.4
        
        # Check for sparse data (high zero ratio)
        zero_ratio = (series == 0).sum() / len(series)
        
        # For sparse data (>70% zeros), use historical average instead of trend extrapolation
        # because Holt-Winters produces unreliable (often negative) forecasts for intermittent demand
        if zero_ratio > 0.7:
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"hypothesisId": "H6", "location": "advanced:_holt_winters_forecast:sparse_data", "message": "Using average for sparse data", "data": {"zero_ratio": float(zero_ratio), "historical_sum": float(series.sum())}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            # Use historical total scaled to forecast period
            historical_days = len(series)
            daily_avg = series.sum() / historical_days
            total_forecast = daily_avg * forecast_periods
            return max(0, total_forecast), 0.5  # Medium confidence for sparse data
        
        # Use statsmodels Holt-Winters with additive trend
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Fit model with additive trend, no seasonality
                model = ExponentialSmoothing(
                    series.values,
                    trend='add',
                    seasonal=None,
                    damped_trend=False,  # Don't dampen - we want to extrapolate trends
                    initialization_method='estimated'
                )
                
                fit = model.fit(optimized=True)
                
                # Generate forecast
                forecast = fit.forecast(forecast_periods)
                
                # #region agent log
                try:
                    with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"hypothesisId": "H2", "location": "advanced:_holt_winters_forecast:after_fit", "message": "Model fit complete", "data": {"forecast_values": [float(x) for x in forecast[:5]], "forecast_sum": float(np.sum(forecast)), "forecast_min": float(np.min(forecast)), "forecast_max": float(np.max(forecast))}, "timestamp": __import__('time').time() * 1000}) + '\n')
                except: pass
                # #endregion
                
                # If forecast sum is negative or zero, fall back to historical average
                forecast_sum = np.sum(forecast)
                if forecast_sum <= 0:
                    # #region agent log
                    try:
                        with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                            import json
                            f.write(json.dumps({"hypothesisId": "H7", "location": "advanced:_holt_winters_forecast:negative_fallback", "message": "Falling back to average due to negative forecast", "data": {"forecast_sum": float(forecast_sum)}, "timestamp": __import__('time').time() * 1000}) + '\n')
                    except: pass
                    # #endregion
                    daily_avg = series.sum() / len(series)
                    total_forecast = daily_avg * forecast_periods
                    return max(0, total_forecast), 0.4
                
                total_forecast = forecast_sum
                
                # Calculate confidence based on fit quality
                confidence = self._calculate_confidence(series, fit)
                
                # #region agent log
                try:
                    with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                        import json
                        f.write(json.dumps({"hypothesisId": "H3", "location": "advanced:_holt_winters_forecast:return", "message": "Returning forecast", "data": {"total_forecast": float(total_forecast), "confidence": float(confidence)}, "timestamp": __import__('time').time() * 1000}) + '\n')
                except: pass
                # #endregion
                
                return total_forecast, confidence
                
        except Exception as e:
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"hypothesisId": "H4", "location": "advanced:_holt_winters_forecast:exception", "message": "Exception caught", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": __import__('time').time() * 1000}) + '\n')
            except: pass
            # #endregion
            # Fallback to simple average if model fails
            avg_daily = series.mean()
            return avg_daily * forecast_periods, 0.3
    
    def _calculate_confidence(self, series: pd.Series, fit) -> float:
        """Calculate confidence level based on model fit and data quality."""
        # Base confidence from data quantity
        data_confidence = min(1.0, len(series) / 30.0)  # Full confidence at 30+ days
        
        # Adjust for data quality (coefficient of variation)
        mean_val = series.mean()
        if mean_val > 0:
            cv = series.std() / mean_val
            stability = max(0.3, 1.0 - min(1.0, cv / 2.0))
        else:
            stability = 0.3
        
        # Adjust for model fit quality (if available)
        try:
            # Use AIC as a proxy for model quality (lower is better)
            # Normalize to 0-1 range approximately
            aic = fit.aic
            if not np.isnan(aic) and not np.isinf(aic):
                # Rough normalization - AIC values can vary widely
                aic_factor = max(0.3, 1.0 - min(1.0, abs(aic) / 1000))
            else:
                aic_factor = 0.5
        except:
            aic_factor = 0.5
        
        # Combine factors
        confidence = (data_confidence * 0.4 + stability * 0.3 + aic_factor * 0.3)
        
        return max(0.3, min(1.0, confidence))
    
    def _create_default_forecast(
        self, 
        item, 
        start: datetime, 
        end: datetime, 
        days: int
    ) -> ForecastItem:
        """Create a default forecast for items with no sales history."""
        return ForecastItem(
            item_id=item.item_id,
            item_name=item.item_name,
            forecasted_quantity=0,
            forecast_period_start=start,
            forecast_period_end=end,
            confidence_level=0.3,
            forecasted_revenue=0.0,
        )
