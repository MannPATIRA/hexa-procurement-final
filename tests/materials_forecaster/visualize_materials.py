"""
Visualization script for materials historical usage and forecast.
Shows both past materials consumption (from sales history) and future forecasts.
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def plot_materials_historical_and_forecast(
    historical_usage: dict,
    materials_forecast_basic,
    materials_forecast_advanced,
    output_path: Path | None = None
):
    """
    Create a combined visualization showing historical materials usage and future forecasts
    from both Basic and Super Advanced forecasters.
    
    Args:
        historical_usage: Dictionary from calculate_historical_usage() method
                         Format: {material_id: [{'date': datetime, 'quantity_used': float, ...}, ...]}
        materials_forecast_basic: MaterialsForecast object from Basic sales forecaster
        materials_forecast_advanced: MaterialsForecast object from Super Advanced sales forecaster
        output_path: Optional path to save the visualization. If None, saves to default location.
    """
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Get unique materials and assign colors
    all_material_ids = set(historical_usage.keys()) | {f.material_id for f in materials_forecast_basic.forecasts} | {f.material_id for f in materials_forecast_advanced.forecasts}
    colormap = plt.colormaps['tab10']
    colors = [colormap(i % 10) for i in range(len(all_material_ids))]
    material_colors = {mat_id: colors[i] for i, mat_id in enumerate(sorted(all_material_ids))}
    
    # Plot historical usage for each material
    for material_id, usage_records in historical_usage.items():
        if not usage_records:
            continue
            
        material_name = usage_records[0]['material_name']
        color = material_colors.get(material_id, '#000000')
        
        # Extract dates and quantities
        dates = [r['date'] for r in usage_records]
        quantities = [r['quantity_used'] for r in usage_records]
        
        # Aggregate by day (in case multiple sales on same day)
        daily_usage = defaultdict(float)
        for date, qty in zip(dates, quantities):
            day = date.date()
            daily_usage[day] += qty
        
        # Sort by date
        sorted_dates = sorted(daily_usage.keys())
        daily_quantities = [daily_usage[d] for d in sorted_dates]
        daily_datetimes = [datetime.combine(d, datetime.min.time()) for d in sorted_dates]
        
        # Plot historical data
        ax.plot(daily_datetimes, daily_quantities, 'o-', color=color, 
               linewidth=2, markersize=5, alpha=0.7, 
               label=f'{material_name} (Historical)', zorder=3)
    
    # Plot Basic forecast for each material
    forecast_start = materials_forecast_basic.forecast_period_start
    forecast_end = materials_forecast_basic.forecast_period_end
    forecast_days = (forecast_end - forecast_start).days
    
    for forecast_item in materials_forecast_basic.forecasts:
        material_id = forecast_item.material_id
        material_name = forecast_item.material_name
        color = material_colors.get(material_id, '#000000')
        
        # Calculate daily forecasted quantity
        daily_forecast = forecast_item.forecasted_quantity / forecast_days if forecast_days > 0 else 0
        
        # Create forecast timeline
        forecast_dates = [forecast_start + timedelta(days=i) for i in range(forecast_days)]
        forecast_quantities = [daily_forecast] * len(forecast_dates)
        
        # Plot Basic forecast as dashed line
        ax.plot(forecast_dates, forecast_quantities, '--', color=color,
               linewidth=2.5, alpha=0.8,
               label=f'{material_name} (Basic Forecast)', zorder=2)
    
    # Plot Super Advanced forecast for each material
    for forecast_item in materials_forecast_advanced.forecasts:
        material_id = forecast_item.material_id
        material_name = forecast_item.material_name
        color = material_colors.get(material_id, '#000000')
        
        # Calculate daily forecasted quantity
        daily_forecast = forecast_item.forecasted_quantity / forecast_days if forecast_days > 0 else 0
        
        # Create forecast timeline
        forecast_dates = [forecast_start + timedelta(days=i) for i in range(forecast_days)]
        forecast_quantities = [daily_forecast] * len(forecast_dates)
        
        # Plot Super Advanced forecast as dotted line with different alpha
        ax.plot(forecast_dates, forecast_quantities, ':', color=color,
               linewidth=3, alpha=0.9,
               label=f'{material_name} (Super Advanced Forecast)', zorder=2)
    
    # Add vertical line separating historical from forecast
    if historical_usage:
        # Find the latest historical date
        all_historical_dates = []
        for usage_records in historical_usage.values():
            for record in usage_records:
                all_historical_dates.append(record['date'])
        
        if all_historical_dates:
            last_historical_date = max(all_historical_dates)
            ax.axvline(x=last_historical_date, color='black', linestyle=':', 
                      linewidth=2, alpha=0.7, label='Historical → Forecast', zorder=1)
            # Add text annotation
            ax.text(last_historical_date, ax.get_ylim()[1] * 0.95, ' Forecast→', 
                   fontsize=10, fontweight='bold', verticalalignment='top')
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Daily Material Quantity', fontsize=12, fontweight='bold')
    ax.set_title('Materials Usage: Historical vs Forecast', fontsize=14, fontweight='bold', pad=15)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    # Format x-axis to show dates properly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save the plot
    if output_path is None:
        output_path = Path(__file__).parent / 'materials_historical_and_forecast.png'
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Materials visualization saved to: {output_path}")
    
    plt.close()
    
    return output_path


def main():
    """Main function to generate and visualize materials historical usage and forecast."""
    print("="*80)
    print("GENERATING MATERIALS HISTORICAL USAGE AND FORECAST VISUALIZATION")
    print("="*80)
    
    # Fetch data
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    bom_data = erp_fetcher.fetch_bom_data()
    
    # Generate sales forecasts using both Basic and Super Advanced
    print("\n  Generating sales forecast (Basic)...")
    basic_sales_forecaster = BasicSalesForecaster()
    basic_sales_forecast = basic_sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    print("  Generating sales forecast (Super Advanced)...")
    advanced_sales_forecaster = SuperAdvancedSalesForecaster()
    advanced_sales_forecast = advanced_sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Generate materials forecasts from both sales forecasts
    print("  Generating materials forecast (Basic)...")
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    materials_forecast_basic = materials_forecaster.forecast_materials(
        basic_sales_forecast, bom_data, forecast_period_days=30
    )
    
    print("  Generating materials forecast (Super Advanced)...")
    materials_forecast_advanced = materials_forecaster.forecast_materials(
        advanced_sales_forecast, bom_data, forecast_period_days=30
    )
    
    # Calculate historical materials usage
    print("  Calculating historical materials usage from sales history...")
    historical_usage = materials_forecaster.calculate_historical_usage(sales_data, bom_data)
    
    # Create visualization
    print("  Creating combined visualization...")
    output_path = plot_materials_historical_and_forecast(
        historical_usage, 
        materials_forecast_basic,
        materials_forecast_advanced
    )
    
    print("\n" + "="*80)
    print("Visualization complete!")
    print("="*80)
    print(f"\nView the results at: {output_path}")
    
    # Print summary statistics
    print("\nSummary:")
    print(f"  Materials with historical data: {len(historical_usage)}")
    print(f"  Materials in forecast (Basic): {len(materials_forecast_basic.forecasts)}")
    print(f"  Materials in forecast (Super Advanced): {len(materials_forecast_advanced.forecasts)}")
    
    print("\nComparison:")
    for material_id in historical_usage.keys():
        usage_records = historical_usage[material_id]
        if usage_records:
            total_historical = sum(r['quantity_used'] for r in usage_records)
            material_name = usage_records[0]['material_name']
            basic_forecast_item = materials_forecast_basic.forecasts_by_id.get(material_id)
            advanced_forecast_item = materials_forecast_advanced.forecasts_by_id.get(material_id)
            
            basic_forecast = basic_forecast_item.forecasted_quantity if basic_forecast_item else 0
            advanced_forecast = advanced_forecast_item.forecasted_quantity if advanced_forecast_item else 0
            difference = advanced_forecast - basic_forecast
            
            print(f"  {material_name}:")
            print(f"    Historical: {total_historical:.1f}")
            print(f"    Basic Forecast: {basic_forecast:.1f}")
            print(f"    Super Advanced Forecast: {advanced_forecast:.1f}")
            print(f"    Difference: {difference:+.1f} ({difference/total_historical*100 if total_historical > 0 else 0:+.1f}%)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
