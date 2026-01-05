"""Test case that visualizes the materials forecast as a graph."""

from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def test_visualize_materials_forecast():
    """Generate and visualize materials forecast as a graph with all materials."""
    erp_fetcher = MockERPDataFetcher()
    materials_lookup = erp_fetcher.get_materials_lookup()
    
    # Generate sales forecast first
    sales_forecaster = BasicSalesForecaster()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days=30)
    
    # Generate materials forecast
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    materials_forecast = materials_forecaster.forecast_materials(sales_forecast, bom_data, forecast_period_days=30)
    
    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Get unique materials and assign colors
    colormap = plt.colormaps['tab10']
    colors = [colormap(i) for i in range(len(materials_forecast.forecasts))]
    material_colors = {forecast.material_id: colors[i] for i, forecast in enumerate(materials_forecast.forecasts)}
    
    # Plot forecasted quantities for each material
    forecast_start = materials_forecast.forecast_period_start
    forecast_end = materials_forecast.forecast_period_end
    total_days = (forecast_end - forecast_start).days
    
    for forecast_item in materials_forecast.forecasts:
        material_id = forecast_item.material_id
        material_name = forecast_item.material_name
        color = material_colors[material_id]
        
        # Calculate daily forecasted quantity
        daily_forecast = forecast_item.forecasted_quantity / total_days if total_days > 0 else 0
        
        # Create forecast timeline (daily points)
        from datetime import timedelta
        forecast_dates = [forecast_start + timedelta(days=i) for i in range(total_days + 1)]
        forecast_quantities = [daily_forecast] * len(forecast_dates)
        
        # Convert to matplotlib date format
        mpl_forecast_dates = mdates.date2num(forecast_dates)
        
        plt.plot(mpl_forecast_dates, forecast_quantities, '-', color=color, 
                linewidth=2.5, alpha=0.8, label=f'{material_name} ({material_id})')
    
    # Formatting
    plt.xlabel('Date', fontsize=12, fontweight='bold')
    plt.ylabel('Daily Material Quantity Required', fontsize=12, fontweight='bold')
    plt.title('Materials Forecast: Required Materials by Product Sales Forecast', fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates properly
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save the plot
    import os
    output_dir = 'tests/materials_forecaster'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'materials_forecast_visualization.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Materials forecast visualization saved to: {output_path}")
    
    # Show the plot (will display if running interactively, otherwise just saves)
    try:
        plt.show(block=False)
    except Exception:
        pass  # If display is not available, just continue
    
    plt.close()
    
    # Assert that forecast was generated successfully
    assert len(materials_forecast.forecasts) > 0
    assert materials_forecast.forecast_period_start <= datetime.now()
    assert materials_forecast.forecast_period_end > materials_forecast.forecast_period_start
    assert os.path.exists(output_path), f"Visualization file was not created at {output_path}"

