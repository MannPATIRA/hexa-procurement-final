"""Test case that visualizes the sales forecast as a graph."""

from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def test_visualize_sales_forecast():
    """Generate and visualize sales forecast as a graph with all products."""
    forecaster = BasicSalesForecaster()
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    # Generate forecast
    forecast = forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    # Prepare historical sales data for visualization
    # Group sales by product and date
    historical_sales = defaultdict(lambda: defaultdict(int))
    for record in sales_data.records:
        date_key = record.timestamp.date()
        historical_sales[record.product_id][date_key] += record.quantity_sold
    
    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Plot historical sales for each product
    colormap = plt.colormaps['tab10']
    colors = [colormap(i) for i in range(len(inventory_data.items))]
    product_colors = {item.item_id: colors[i] for i, item in enumerate(inventory_data.items)}
    
    # Plot historical data
    for item in inventory_data.items:
        product_id = item.item_id
        product_name = item.item_name
        color = product_colors[product_id]
        
        # Get historical sales for this product
        product_history = historical_sales.get(product_id, {})
        if product_history:
            dates = sorted(product_history.keys())
            quantities = [product_history[date] for date in dates]
            
            # Convert dates to datetime for plotting
            date_times = [datetime.combine(date, datetime.min.time()) for date in dates]
            
            # Convert to matplotlib date format
            mpl_dates = mdates.date2num(date_times)
            
            plt.plot(mpl_dates, quantities, 'o-', color=color, alpha=0.6, 
                    linewidth=2, markersize=4, label=f'{product_name} (Historical)')
    
    # Plot forecasted sales
    forecast_start = forecast.forecast_period_start
    forecast_end = forecast.forecast_period_end
    
    for forecast_item in forecast.forecasts:
        product_id = forecast_item.item_id
        product_name = forecast_item.item_name
        color = product_colors[product_id]
        
        # Calculate daily forecasted quantity
        total_days = (forecast_end - forecast_start).days
        daily_forecast = forecast_item.forecasted_quantity / total_days if total_days > 0 else 0
        
        # Create forecast timeline (daily points)
        forecast_dates = [forecast_start + timedelta(days=i) for i in range(total_days + 1)]
        forecast_quantities = [daily_forecast] * len(forecast_dates)
        
        # Convert to matplotlib date format
        mpl_forecast_dates = mdates.date2num(forecast_dates)
        
        plt.plot(mpl_forecast_dates, forecast_quantities, '--', color=color, 
                linewidth=2.5, alpha=0.8, label=f'{product_name} (Forecast)')
    
    # Add vertical line to separate historical from forecast
    forecast_start_num = float(mdates.date2num(forecast_start))
    plt.axvline(x=forecast_start_num, color='gray', linestyle=':', linewidth=2, alpha=0.7, label='Forecast Start')
    
    # Formatting
    plt.xlabel('Date', fontsize=12, fontweight='bold')
    plt.ylabel('Daily Sales Quantity', fontsize=12, fontweight='bold')
    plt.title('Sales Forecast: Historical vs Projected Sales by Product', fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates properly
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save the plot
    import os
    output_dir = 'tests/sales_forecaster'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'sales_forecast_visualization.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Sales forecast visualization saved to: {output_path}")
    
    # Show the plot (will display if running interactively, otherwise just saves)
    try:
        plt.show(block=False)
    except Exception:
        pass  # If display is not available, just continue
    
    plt.close()
    
    # Assert that forecast was generated successfully
    assert len(forecast.forecasts) > 0
    assert forecast.forecast_period_start <= datetime.now()
    assert forecast.forecast_period_end > forecast.forecast_period_start
    assert os.path.exists(output_path), f"Visualization file was not created at {output_path}"

