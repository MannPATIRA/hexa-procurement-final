"""
Visualization script for large synthetic datasets.
Shows historical data + forecasts as line graphs for 10 different large datasets.
"""

import sys
from pathlib import Path
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from models.inventory_data import InventoryData, InventoryItem
from models.sales_data import SalesData, SalesRecord


def generate_large_dataset(
    product_id: str,
    product_name: str,
    pattern_type: str,
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> tuple[InventoryItem, list[SalesRecord]]:
    """Generate a large dataset with a specific pattern."""
    now = datetime.now()
    records = []
    
    if pattern_type == "steady_growth":
        # Steady linear growth
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            base_qty = 10 + (i * 0.5)  # Growing from 10 to 10 + 0.5*num_records
            quantity = max(1, int(base_qty + random.gauss(0, 2)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "exponential_growth":
        # Exponential growth
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            base_qty = 5 * (1.05 ** i)  # 5% daily growth
            quantity = max(1, int(base_qty + random.gauss(0, base_qty * 0.1)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "declining_trend":
        # Declining trend
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            base_qty = 50 - (i * 0.3)  # Declining from 50
            quantity = max(1, int(base_qty + random.gauss(0, 3)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "cyclical":
        # Weekly cyclical pattern
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            day_of_week = timestamp.weekday()
            base_qty = 20 + 15 * np.sin(2 * np.pi * day_of_week / 7)  # Weekly cycle
            quantity = max(1, int(base_qty + random.gauss(0, 3)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "step_change":
        # Step change in the middle
        step_day = days_back // 2
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            if days_ago > step_day:
                base_qty = 10  # Before step
            else:
                base_qty = 30  # After step
            quantity = max(1, int(base_qty + random.gauss(0, 2)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "volatile":
        # High volatility, no clear trend
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            base_qty = 20
            quantity = max(1, int(base_qty + random.gauss(0, 15)))  # High variance
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "stable":
        # Stable, low variance
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            base_qty = 25
            quantity = max(1, int(base_qty + random.gauss(0, 2)))  # Low variance
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "seasonal_peak":
        # Seasonal peak pattern
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            # Peak in middle of period
            peak_day = days_back / 2
            distance_from_peak = abs(days_ago - peak_day)
            base_qty = 40 - (distance_from_peak * 0.3)  # Peak at center
            quantity = max(1, int(base_qty + random.gauss(0, 3)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "burst_pattern":
        # Burst sales followed by quiet periods
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            # Burst every 7 days
            if int(days_ago) % 7 < 2:
                base_qty = 40  # Burst
            else:
                base_qty = 5  # Quiet
            quantity = max(1, int(base_qty + random.gauss(0, 2)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    elif pattern_type == "recovery":
        # Decline then recovery
        for i in range(num_records):
            days_ago = (days_back * (num_records - i - 1)) / num_records
            timestamp = now - timedelta(days=days_ago)
            midpoint = days_back / 2
            if days_ago > midpoint:
                # Declining phase
                base_qty = 40 - ((days_ago - midpoint) * 0.4)
            else:
                # Recovery phase
                base_qty = 20 + ((midpoint - days_ago) * 0.4)
            quantity = max(1, int(base_qty + random.gauss(0, 3)))
            records.append(SalesRecord(
                timestamp=timestamp,
                product_id=product_id,
                product_name=product_name,
                quantity_sold=quantity,
                unit_price=unit_price,
                total_revenue=quantity * unit_price,
                customer_id=f"CUST-{random.randint(1, 100):03d}"
            ))
    
    records.sort(key=lambda x: x.timestamp)
    
    item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        quantity=100,
        unit_price=unit_price,
        location="WAREHOUSE-01",
        last_updated=datetime.now()
    )
    
    return item, records


def prepare_daily_series(records: list[SalesRecord], start_date: datetime, end_date: datetime) -> dict:
    """Prepare daily aggregated series for plotting."""
    daily_sales = defaultdict(float)
    for r in records:
        day = r.timestamp.date()
        daily_sales[day] += r.quantity_sold
    
    # Create complete date range
    start = start_date.date() if hasattr(start_date, 'date') else start_date
    end = end_date.date() if hasattr(end_date, 'date') else end_date
    current = start
    dates = []
    values = []
    
    while current <= end:
        dates.append(datetime.combine(current, datetime.min.time()))
        values.append(daily_sales.get(current, 0))
        current += timedelta(days=1)
    
    return {"dates": dates, "values": values}


def create_visualization():
    """Create visualization with 10 large datasets."""
    print("="*80)
    print("GENERATING LARGE DATASET VISUALIZATIONS")
    print("="*80)
    
    random.seed(42)
    np.random.seed(42)
    
    # Define 10 large datasets
    datasets = [
        {"pattern": "steady_growth", "name": "Steady Growth", "records": 60, "days": 90},
        {"pattern": "exponential_growth", "name": "Exponential Growth", "records": 50, "days": 80},
        {"pattern": "declining_trend", "name": "Declining Trend", "records": 55, "days": 85},
        {"pattern": "cyclical", "name": "Cyclical Pattern", "records": 70, "days": 100},
        {"pattern": "step_change", "name": "Step Change", "records": 65, "days": 90},
        {"pattern": "volatile", "name": "High Volatility", "records": 60, "days": 90},
        {"pattern": "stable", "name": "Stable Sales", "records": 50, "days": 80},
        {"pattern": "seasonal_peak", "name": "Seasonal Peak", "records": 55, "days": 85},
        {"pattern": "burst_pattern", "name": "Burst Pattern", "records": 70, "days": 100},
        {"pattern": "recovery", "name": "Recovery Pattern", "records": 60, "days": 90},
    ]
    
    forecast_days = 30
    basic = BasicSalesForecaster()
    advanced = AdvancedSalesForecaster()
    super_adv = SuperAdvancedSalesForecaster()
    
    # Create figure with 10 subplots (2 rows x 5 columns)
    fig = plt.figure(figsize=(30, 12))
    
    for idx, dataset_config in enumerate(datasets):
        print(f"  Processing: {dataset_config['name']}...")
        
        product_id = f"LARGE-{idx+1:03d}"
        product_name = f"Product {dataset_config['name']}"
        
        item, records = generate_large_dataset(
            product_id=product_id,
            product_name=product_name,
            pattern_type=dataset_config['pattern'],
            num_records=dataset_config['records'],
            days_back=dataset_config['days'],
            unit_price=25.0
        )
        
        inventory_data = InventoryData(items=[item], fetched_at=datetime.now())
        start_date = min(r.timestamp for r in records)
        sales_data = SalesData(
            records=records,
            start_date=start_date,
            end_date=datetime.now(),
            fetched_at=datetime.now()
        )
        
        # Generate forecasts
        basic_forecast = basic.forecast_sales(inventory_data, sales_data, forecast_days)
        advanced_forecast = advanced.forecast_sales(inventory_data, sales_data, forecast_days)
        super_forecast = super_adv.forecast_sales(inventory_data, sales_data, forecast_days)
        
        basic_item = basic_forecast.forecasts_by_id.get(product_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(product_id)
        super_item = super_forecast.forecasts_by_id.get(product_id)
        
        # Prepare historical data
        historical = prepare_daily_series(records, start_date, datetime.now())
        
        # Create subplot
        ax = fig.add_subplot(2, 5, idx + 1)
        
        # Plot historical data
        ax.plot(historical["dates"], historical["values"], 
               'o-', color='#34495e', linewidth=2, markersize=4, 
               label='Historical Sales', alpha=0.7, zorder=3)
        
        # Calculate forecast daily rates
        last_date = max(historical["dates"])
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
        
        basic_daily = basic_item.forecasted_quantity / forecast_days if basic_item else 0
        advanced_daily = advanced_item.forecasted_quantity / forecast_days if advanced_item else 0
        super_daily = super_item.forecasted_quantity / forecast_days if super_item else 0
        
        # Plot forecasts
        ax.plot(forecast_dates, [basic_daily] * forecast_days, 
               '--', color='#3498db', linewidth=2, label=f'Basic: {basic_daily:.1f}/day', alpha=0.8)
        ax.plot(forecast_dates, [advanced_daily] * forecast_days, 
               '--', color='#e74c3c', linewidth=2, label=f'Advanced: {advanced_daily:.1f}/day', alpha=0.8)
        ax.plot(forecast_dates, [super_daily] * forecast_days, 
               '--', color='#2ecc71', linewidth=2, label=f'Super: {super_daily:.1f}/day', alpha=0.8)
        
        # Add vertical line separating historical from forecast
        ax.axvline(x=last_date, color='black', linestyle=':', linewidth=1.5, alpha=0.5)
        
        ax.set_xlabel('Date', fontweight='bold', fontsize=9)
        ax.set_ylabel('Units/Day', fontweight='bold', fontsize=9)
        ax.set_title(f'{dataset_config["name"]}\n({dataset_config["records"]} records, {dataset_config["days"]} days)', 
                    fontweight='bold', fontsize=10)
        ax.legend(loc='upper left', fontsize=7, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right', fontsize=7)
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path(__file__).parent / "large_datasets_visualization.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n  Saved: {output_path}")
    
    print("\n" + "="*80)
    print("Visualization complete!")
    print("="*80)
    
    return output_path


if __name__ == "__main__":
    try:
        path = create_visualization()
        print(f"\nView the results at: {path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
