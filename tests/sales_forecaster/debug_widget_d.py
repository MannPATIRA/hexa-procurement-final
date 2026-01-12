"""
Debug script specifically for Widget D in the original mock data.
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
import numpy as np

# Fetch original mock data
erp_fetcher = MockERPDataFetcher()
inventory_data = erp_fetcher.fetch_inventory_data()
sales_data = erp_fetcher.fetch_sales_data()

# Find Widget D
widget_d = None
for item in inventory_data.items:
    if item.item_id == "PROD-004":
        widget_d = item
        break

if not widget_d:
    print("Widget D not found!")
    sys.exit(1)

# Get Widget D sales records
widget_d_records = sales_data.records_by_product.get("PROD-004", [])
print("="*80)
print("WIDGET D DEBUG ANALYSIS")
print("="*80)
print(f"\nProduct: {widget_d.item_name} (ID: {widget_d.item_id})")
print(f"Unit Price: ${widget_d.unit_price}")
print(f"\nSales Records ({len(widget_d_records)}):")
for r in sorted(widget_d_records, key=lambda x: x.timestamp):
    print(f"  {r.timestamp.strftime('%Y-%m-%d')}: {r.quantity_sold} units @ ${r.unit_price} = ${r.total_revenue}")

total_historical = sum(r.quantity_sold for r in widget_d_records)
days_span = (max(r.timestamp for r in widget_d_records) - min(r.timestamp for r in widget_d_records)).days
print(f"\nTotal Historical Quantity: {total_historical} units")
print(f"Days Span: {days_span} days")
print(f"Average per Day (all days): {total_historical / 30:.2f} units")
print(f"Average per Day (sales days only): {total_historical / len(widget_d_records):.2f} units")

# Test time series preparation
super_forecaster = SuperAdvancedSalesForecaster()
time_series = super_forecaster._prepare_time_series(widget_d_records, sales_data)
print(f"\nTime Series (after resampling):")
print(f"  Length: {len(time_series)} periods")
print(f"  Sum: {np.sum(time_series):.2f}")
print(f"  Mean: {np.mean(time_series):.2f}")
print(f"  Std: {np.std(time_series):.2f}")
print(f"  Non-zero periods: {np.count_nonzero(time_series)}")
print(f"  Zero ratio: {(time_series == 0).sum() / len(time_series):.2%}")
print(f"  First 10 values: {time_series[:10]}")

# Check diagnostics
diagnostics = super_forecaster._compute_diagnostics("PROD-004", time_series, widget_d_records)
print(f"\nDiagnostics:")
print(f"  History Length: {diagnostics.history_length}")
print(f"  Zero Ratio: {diagnostics.zero_ratio:.2%}")
print(f"  Coefficient of Variation: {diagnostics.coefficient_of_variation:.2f}")
print(f"  Data Quality Score: {diagnostics.data_quality_score:.2f}")

# Check routing
routed_diagnostics = super_forecaster._route_to_model(diagnostics)
print(f"  Recommended Model: {routed_diagnostics.recommended_model.value}")

# Generate forecasts
print(f"\n{'='*80}")
print("FORECAST COMPARISON (30 days)")
print(f"{'='*80}")

basic_forecaster = BasicSalesForecaster()
advanced_forecaster = AdvancedSalesForecaster()

basic_forecast = basic_forecaster.forecast_sales(inventory_data, sales_data, 30)
advanced_forecast = advanced_forecaster.forecast_sales(inventory_data, sales_data, 30)
super_forecast = super_forecaster.forecast_sales(inventory_data, sales_data, 30)

basic_item = basic_forecast.forecasts_by_id.get("PROD-004")
advanced_item = advanced_forecast.forecasts_by_id.get("PROD-004")
super_item = super_forecast.forecasts_by_id.get("PROD-004")

print(f"\nBasic Forecaster:")
print(f"  Quantity: {basic_item.forecasted_quantity}")
print(f"  Revenue: ${basic_item.forecasted_revenue:.2f}")
print(f"  Confidence: {basic_item.confidence_level * 100:.1f}%")

print(f"\nAdvanced Forecaster:")
print(f"  Quantity: {advanced_item.forecasted_quantity}")
print(f"  Revenue: ${advanced_item.forecasted_revenue:.2f}")
print(f"  Confidence: {advanced_item.confidence_level * 100:.1f}%")

print(f"\nSuper Advanced Forecaster:")
print(f"  Quantity: {super_item.forecasted_quantity}")
print(f"  Revenue: ${super_item.forecasted_revenue:.2f}")
print(f"  Confidence: {super_item.confidence_level * 100:.1f}%")

# Test Holt-Winters directly
print(f"\n{'='*80}")
print("HOLT-WINTERS DIRECT TEST")
print(f"{'='*80}")
forecast_periods = 30  # Daily frequency, so 30 days = 30 periods
hw_forecast = super_forecaster._holt_winters_forecast(time_series, forecast_periods)
print(f"  Forecast array (first 10): {hw_forecast[:10]}")
print(f"  Forecast sum: {np.sum(hw_forecast):.2f}")
print(f"  Forecast mean per period: {np.mean(hw_forecast):.2f}")
print(f"  Historical average: {np.mean(time_series):.2f}")
print(f"  Min per period (floor): {np.mean(time_series) * 0.3:.2f}")
