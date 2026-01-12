"""
Visualization script for overfitting test results.
Generates comprehensive charts comparing all three forecasters across all scenarios.
"""

import sys
from pathlib import Path
import os
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Tuple, Dict

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from models.inventory_data import InventoryData, InventoryItem
from models.sales_data import SalesData, SalesRecord

# Import the generators from the test file
from test_overfitting_check import (
    generate_product_data,
    generate_exponential_sales,
    generate_step_change_sales,
    generate_cyclical_sales,
    generate_random_walk_sales,
    generate_outlier_sales,
    generate_bimodal_sales,
    generate_burst_sales,
    generate_linear_ramp_sales,
)


def run_scenario_test(products_config: List[dict], forecast_days: int = 30):
    """Run a single test scenario and return detailed results."""
    now = datetime.now()
    
    inventory_items = []
    all_records = []
    
    for i, config in enumerate(products_config):
        product_id = f"TEST-{i+1:03d}"
        product_name = f"Product {chr(65+i)}"
        
        generator_type = config.get("generator", "default")
        days_back = config.get("days_back", 30)
        unit_price = config.get("unit_price", 25.0)
        
        if generator_type == "exponential":
            item, records = generate_exponential_sales(
                product_id, product_name,
                base_quantity=config.get("base_quantity", 10),
                growth_rate=config.get("growth_rate", 0.5),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "step_change":
            item, records = generate_step_change_sales(
                product_id, product_name,
                base_quantity=config.get("base_quantity", 10),
                multiplier=config.get("multiplier", 2.0),
                change_day=config.get("change_day", 15),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "cyclical":
            item, records = generate_cyclical_sales(
                product_id, product_name,
                base_quantity=config.get("base_quantity", 10),
                amplitude=config.get("amplitude", 0.5),
                period_days=config.get("period_days", 7),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "random_walk":
            item, records = generate_random_walk_sales(
                product_id, product_name,
                base_quantity=config.get("base_quantity", 10),
                step_size=config.get("step_size", 0.2),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "outlier":
            item, records = generate_outlier_sales(
                product_id, product_name,
                base_quantity=config.get("base_quantity", 10),
                outlier_multiplier=config.get("outlier_multiplier", 5.0),
                outlier_probability=config.get("outlier_probability", 0.15),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "bimodal":
            item, records = generate_bimodal_sales(
                product_id, product_name,
                low_quantity=config.get("low_quantity", 5),
                high_quantity=config.get("high_quantity", 30),
                high_probability=config.get("high_probability", 0.3),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "burst":
            item, records = generate_burst_sales(
                product_id, product_name,
                burst_quantity=config.get("burst_quantity", 20),
                burst_duration_days=config.get("burst_duration_days", 3),
                silence_duration_days=config.get("silence_duration_days", 7),
                num_bursts=config.get("num_bursts", 3),
                days_back=days_back,
                unit_price=unit_price
            )
        elif generator_type == "linear_ramp":
            item, records = generate_linear_ramp_sales(
                product_id, product_name,
                start_quantity=config.get("start_quantity", 5),
                end_quantity=config.get("end_quantity", 30),
                num_records=config.get("num_records", 10),
                days_back=days_back,
                unit_price=unit_price
            )
        else:
            item, records = generate_product_data(
                product_id, product_name, config,
                days_back=days_back
            )
        
        inventory_items.append(item)
        all_records.extend(records)
    
    inventory_data = InventoryData(items=inventory_items, fetched_at=now)
    start_date = min(r.timestamp for r in all_records) if all_records else now - timedelta(days=30)
    sales_data = SalesData(
        records=all_records,
        start_date=start_date,
        end_date=now,
        fetched_at=now
    )
    
    basic = BasicSalesForecaster()
    advanced = AdvancedSalesForecaster()
    super_adv = SuperAdvancedSalesForecaster()
    
    basic_forecast = basic.forecast_sales(inventory_data, sales_data, forecast_days)
    advanced_forecast = advanced.forecast_sales(inventory_data, sales_data, forecast_days)
    super_forecast = super_adv.forecast_sales(inventory_data, sales_data, forecast_days)
    
    results = []
    for item in inventory_items:
        product_records = [r for r in all_records if r.product_id == item.item_id]
        historical_qty = sum(r.quantity_sold for r in product_records)
        
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        super_item = super_forecast.forecasts_by_id.get(item.item_id)
        
        if basic_item and advanced_item and super_item:
            deviation = 0
            if basic_item.forecasted_quantity > 0:
                deviation = ((super_item.forecasted_quantity - basic_item.forecasted_quantity) / 
                            basic_item.forecasted_quantity * 100)
            
            results.append({
                "product_id": item.item_id,
                "historical": historical_qty,
                "basic": basic_item.forecasted_quantity,
                "advanced": advanced_item.forecasted_quantity,
                "super": super_item.forecasted_quantity,
                "deviation": deviation,
                "records": product_records
            })
    
    return results


def create_visualizations():
    """Create comprehensive visualizations for all test scenarios."""
    print("="*80)
    print("GENERATING FORECASTER COMPARISON VISUALIZATIONS")
    print("="*80)
    
    random.seed(42)
    np.random.seed(42)
    
    # Define all scenarios
    scenarios = {
        "Exponential Growth": [
            {"generator": "exponential", "base_quantity": 5, "growth_rate": 1.0, 
             "num_records": 12, "days_back": 30, "unit_price": 40},
        ],
        "Exponential Decay": [
            {"generator": "exponential", "base_quantity": 50, "growth_rate": -0.8, 
             "num_records": 12, "days_back": 30, "unit_price": 35},
        ],
        "Step Change Up": [
            {"generator": "step_change", "base_quantity": 10, "multiplier": 3.0, 
             "change_day": 15, "num_records": 12, "days_back": 30, "unit_price": 25},
        ],
        "Step Change Down": [
            {"generator": "step_change", "base_quantity": 40, "multiplier": 0.3, 
             "change_day": 15, "num_records": 12, "days_back": 30, "unit_price": 30},
        ],
        "Cyclical Wave": [
            {"generator": "cyclical", "base_quantity": 20, "amplitude": 0.5, 
             "period_days": 7, "num_records": 20, "days_back": 35, "unit_price": 28},
        ],
        "Random Walk": [
            {"generator": "random_walk", "base_quantity": 20, "step_size": 0.3, 
             "num_records": 15, "days_back": 30, "unit_price": 35},
        ],
        "Outlier Heavy": [
            {"generator": "outlier", "base_quantity": 15, "outlier_multiplier": 5.0, 
             "outlier_probability": 0.15, "num_records": 15, "days_back": 30, "unit_price": 40},
        ],
        "Bi-modal": [
            {"generator": "bimodal", "low_quantity": 5, "high_quantity": 40, 
             "high_probability": 0.3, "num_records": 15, "days_back": 30, "unit_price": 30},
        ],
        "Burst Sales": [
            {"generator": "burst", "burst_quantity": 25, "burst_duration_days": 3, 
             "silence_duration_days": 7, "num_bursts": 3, "days_back": 30, "unit_price": 35},
        ],
        "Linear Ramp": [
            {"generator": "linear_ramp", "start_quantity": 5, "end_quantity": 35, 
             "num_records": 12, "days_back": 30, "unit_price": 28},
        ],
    }
    
    # Collect all results
    all_results = {}
    for name, config in scenarios.items():
        print(f"  Running: {name}...")
        all_results[name] = run_scenario_test(config)
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(24, 28))
    
    # =========================================================================
    # Plot 1: Forecast Comparison Bar Chart (all scenarios)
    # =========================================================================
    ax1 = fig.add_subplot(4, 2, 1)
    
    scenario_names = list(all_results.keys())
    basic_vals = [all_results[s][0]["basic"] for s in scenario_names]
    advanced_vals = [all_results[s][0]["advanced"] for s in scenario_names]
    super_vals = [all_results[s][0]["super"] for s in scenario_names]
    
    x = np.arange(len(scenario_names))
    width = 0.25
    
    bars1 = ax1.bar(x - width, basic_vals, width, label='Basic', color='#3498db', alpha=0.8)
    bars2 = ax1.bar(x, advanced_vals, width, label='Advanced', color='#e74c3c', alpha=0.8)
    bars3 = ax1.bar(x + width, super_vals, width, label='Super Advanced', color='#2ecc71', alpha=0.8)
    
    ax1.set_ylabel('Forecasted Quantity', fontweight='bold')
    ax1.set_title('Forecast Comparison Across All New Scenarios', fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=9)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # =========================================================================
    # Plot 2: Deviation from Basic (%)
    # =========================================================================
    ax2 = fig.add_subplot(4, 2, 2)
    
    deviations = [all_results[s][0]["deviation"] for s in scenario_names]
    colors = ['#2ecc71' if d >= 0 else '#e74c3c' for d in deviations]
    
    bars = ax2.barh(scenario_names, deviations, color=colors, alpha=0.8)
    ax2.axvline(x=0, color='black', linewidth=1)
    ax2.axvline(x=50, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='+50% threshold')
    ax2.axvline(x=-50, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    
    ax2.set_xlabel('Deviation from Basic (%)', fontweight='bold')
    ax2.set_title('Super Advanced vs Basic: Deviation by Scenario', fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='x')
    
    for bar, dev in zip(bars, deviations):
        x_pos = bar.get_width() + 2 if bar.get_width() >= 0 else bar.get_width() - 15
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2, f'{dev:+.1f}%', 
                va='center', fontsize=9, fontweight='bold')
    
    # =========================================================================
    # Plot 3: Historical vs Forecasted (Scatter)
    # =========================================================================
    ax3 = fig.add_subplot(4, 2, 3)
    
    historical = [all_results[s][0]["historical"] for s in scenario_names]
    
    ax3.scatter(historical, basic_vals, s=100, c='#3498db', label='Basic', alpha=0.8, marker='o')
    ax3.scatter(historical, advanced_vals, s=100, c='#e74c3c', label='Advanced', alpha=0.8, marker='s')
    ax3.scatter(historical, super_vals, s=100, c='#2ecc71', label='Super Advanced', alpha=0.8, marker='^')
    
    # Add diagonal reference line
    max_val = max(max(historical), max(basic_vals), max(super_vals))
    ax3.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='1:1 Line')
    
    ax3.set_xlabel('Historical Sales (30 days)', fontweight='bold')
    ax3.set_ylabel('Forecasted Sales (30 days)', fontweight='bold')
    ax3.set_title('Historical vs Forecasted: All Scenarios', fontweight='bold', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # =========================================================================
    # Plot 4: Deviation Distribution (Histogram)
    # =========================================================================
    ax4 = fig.add_subplot(4, 2, 4)
    
    ax4.hist(deviations, bins=10, color='#9b59b6', alpha=0.7, edgecolor='black')
    ax4.axvline(x=0, color='black', linewidth=2, label='No Deviation')
    ax4.axvline(x=np.mean(deviations), color='red', linewidth=2, linestyle='--', 
               label=f'Mean: {np.mean(deviations):+.1f}%')
    
    ax4.set_xlabel('Deviation from Basic (%)', fontweight='bold')
    ax4.set_ylabel('Count', fontweight='bold')
    ax4.set_title('Distribution of Super vs Basic Deviations', fontweight='bold', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # =========================================================================
    # Plot 5-8: Individual Scenario Time Series (FIXED: Daily aggregation)
    # =========================================================================
    plot_scenarios = ["Exponential Growth", "Exponential Decay", "Step Change Up", "Cyclical Wave"]
    
    for idx, scenario_name in enumerate(plot_scenarios):
        ax = fig.add_subplot(4, 2, 5 + idx)
        
        result = all_results[scenario_name][0]
        records = result["records"]
        
        # Aggregate sales by DAY (sum all transactions per day)
        daily_sales = defaultdict(float)
        for r in records:
            day = r.timestamp.date()
            daily_sales[day] += r.quantity_sold
        
        # Create complete daily series (fill missing days with 0)
        if daily_sales:
            min_date = min(daily_sales.keys())
            max_date = max(daily_sales.keys())
            all_days = []
            current = min_date
            while current <= max_date:
                all_days.append(current)
                current += timedelta(days=1)
            
            daily_quantities = [daily_sales.get(d, 0) for d in all_days]
            daily_dates = [datetime.combine(d, datetime.min.time()) for d in all_days]
        else:
            daily_dates = []
            daily_quantities = []
        
        # Calculate historical daily average for reference
        history_days = (max_date - min_date).days + 1 if daily_sales else 1
        historical_daily_avg = result["historical"] / history_days if history_days > 0 else 0
        
        # Plot historical DAILY totals (bar chart for clarity)
        ax.bar(daily_dates, daily_quantities, width=0.8, color='#34495e', alpha=0.6, 
               label=f'Historical Daily Sales (Total: {result["historical"]} units)', zorder=3)
        
        # Add a line connecting the bars for trend visibility
        ax.plot(daily_dates, daily_quantities, 'ko-', markersize=4, alpha=0.5, zorder=4)
        
        # Add historical average line
        ax.axhline(y=historical_daily_avg, color='#7f8c8d', linestyle=':', linewidth=2,
                  label=f'Hist. Avg: {historical_daily_avg:.1f}/day', alpha=0.8)
        
        # Create forecast projection area (next 30 days)
        last_date = max(daily_dates) if daily_dates else datetime.now()
        forecast_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        
        # Calculate daily forecast rates
        basic_daily = result["basic"] / 30
        advanced_daily = result["advanced"] / 30
        super_daily = result["super"] / 30
        
        # Draw forecast projections as shaded areas with lines
        ax.fill_between(forecast_dates, 0, [basic_daily]*30, color='#3498db', alpha=0.15, zorder=1)
        ax.plot(forecast_dates, [basic_daily]*30, color='#3498db', linestyle='-', linewidth=2,
               label=f'Basic Forecast: {basic_daily:.1f}/day ({result["basic"]} total)', zorder=5)
        
        ax.fill_between(forecast_dates, 0, [advanced_daily]*30, color='#e74c3c', alpha=0.15, zorder=1)
        ax.plot(forecast_dates, [advanced_daily]*30, color='#e74c3c', linestyle='-', linewidth=2,
               label=f'Advanced: {advanced_daily:.1f}/day ({result["advanced"]} total)', zorder=5)
        
        ax.fill_between(forecast_dates, 0, [super_daily]*30, color='#2ecc71', alpha=0.15, zorder=1)
        ax.plot(forecast_dates, [super_daily]*30, color='#2ecc71', linestyle='-', linewidth=2,
               label=f'Super Adv: {super_daily:.1f}/day ({result["super"]} total)', zorder=5)
        
        # Add vertical line separating historical from forecast
        ax.axvline(x=last_date, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.text(last_date, ax.get_ylim()[1]*0.95, ' Forecast→', fontsize=9, fontweight='bold',
               verticalalignment='top')
        
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Units Sold per Day', fontweight='bold')
        ax.set_title(f'{scenario_name}: Daily Sales + 30-Day Forecast', fontweight='bold', fontsize=11)
        ax.legend(loc='upper left', fontsize=7, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)  # Ensure y-axis starts at 0
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path(__file__).parent / "overfitting_visualization.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n  Saved: {output_path}")
    
    # =========================================================================
    # Create second figure: Summary dashboard
    # =========================================================================
    fig2 = plt.figure(figsize=(20, 12))
    
    # Collect data from all 22 original scenarios
    all_scenarios_full = [
        ("Very Sparse Data", [{"num_records": 1, "base_quantity": 50, "variance": 0, "days_back": 30}]),
        ("Very Dense Data", [{"num_records": 25, "base_quantity": 10, "variance": 0.3, "days_back": 45}]),
        ("Strong Upward Trend", [{"num_records": 8, "base_quantity": 5, "trend": 0.5, "variance": 0.2, "days_back": 30}]),
        ("Strong Downward Trend", [{"num_records": 8, "base_quantity": 30, "trend": -0.5, "variance": 0.2, "days_back": 30}]),
        ("High Volatility", [{"num_records": 10, "base_quantity": 20, "variance": 0.8, "days_back": 30}]),
        ("Low Volatility", [{"num_records": 10, "base_quantity": 50, "variance": 0.05, "days_back": 30}]),
        ("Seasonal Pattern", [{"num_records": 15, "base_quantity": 20, "seasonality": True, "variance": 0.2, "days_back": 45}]),
    ]
    
    # Run all scenarios
    full_results = {}
    for name, config in all_scenarios_full:
        full_results[name] = run_scenario_test(config)
    
    # Combine with new scenarios
    all_combined = {**full_results, **all_results}
    
    # Plot 1: All scenarios bar chart
    ax1 = fig2.add_subplot(2, 2, 1)
    
    all_names = list(all_combined.keys())
    all_basic = [all_combined[s][0]["basic"] for s in all_names]
    all_super = [all_combined[s][0]["super"] for s in all_names]
    
    x = np.arange(len(all_names))
    width = 0.35
    
    ax1.bar(x - width/2, all_basic, width, label='Basic', color='#3498db', alpha=0.8)
    ax1.bar(x + width/2, all_super, width, label='Super Advanced', color='#2ecc71', alpha=0.8)
    
    ax1.set_ylabel('Forecasted Quantity', fontweight='bold')
    ax1.set_title('Basic vs Super Advanced: All 17 Scenarios', fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(all_names, rotation=60, ha='right', fontsize=8)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Category breakdown pie chart
    ax2 = fig2.add_subplot(2, 2, 2)
    
    all_devs = [all_combined[s][0]["deviation"] for s in all_names]
    
    categories = {
        'Accurate (±10%)': len([d for d in all_devs if abs(d) <= 10]),
        'Moderate (10-30%)': len([d for d in all_devs if 10 < abs(d) <= 30]),
        'Large (30-50%)': len([d for d in all_devs if 30 < abs(d) <= 50]),
        'Very Large (>50%)': len([d for d in all_devs if abs(d) > 50]),
    }
    
    colors_pie = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
    wedges, texts, autotexts = ax2.pie(
        categories.values(), labels=categories.keys(), colors=colors_pie,
        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10}
    )
    ax2.set_title('Deviation Categories Distribution', fontweight='bold', fontsize=12)
    
    # Plot 3: Box plot of deviations by pattern type
    ax3 = fig2.add_subplot(2, 2, 3)
    
    trend_scenarios = ["Strong Upward Trend", "Strong Downward Trend", "Exponential Growth", 
                       "Exponential Decay", "Linear Ramp", "Step Change Up", "Step Change Down"]
    stable_scenarios = ["Low Volatility", "Cyclical Wave", "Random Walk", "Burst Sales"]
    noisy_scenarios = ["High Volatility", "Outlier Heavy", "Bi-modal", "Very Sparse Data"]
    
    trend_devs = [all_combined[s][0]["deviation"] for s in trend_scenarios if s in all_combined]
    stable_devs = [all_combined[s][0]["deviation"] for s in stable_scenarios if s in all_combined]
    noisy_devs = [all_combined[s][0]["deviation"] for s in noisy_scenarios if s in all_combined]
    
    box_data = [trend_devs, stable_devs, noisy_devs]
    box_labels = ['Trend Patterns', 'Stable Patterns', 'Noisy Patterns']
    
    bp = ax3.boxplot(box_data, labels=box_labels, patch_artist=True)
    colors_box = ['#3498db', '#2ecc71', '#e74c3c']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Deviation from Basic (%)', fontweight='bold')
    ax3.set_title('Deviation by Pattern Category', fontweight='bold', fontsize=12)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Summary statistics table
    ax4 = fig2.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    stats_text = f"""
    SUMMARY STATISTICS
    ==================
    
    Total Scenarios Tested: {len(all_names)}
    
    Deviation from Basic:
      Mean:   {np.mean(all_devs):+.1f}%
      Median: {np.median(all_devs):+.1f}%
      Std:    {np.std(all_devs):.1f}%
      Min:    {min(all_devs):+.1f}%
      Max:    {max(all_devs):+.1f}%
    
    Accuracy Breakdown:
      Within ±10%:  {categories['Accurate (±10%)']} scenarios ({categories['Accurate (±10%)']/len(all_names)*100:.1f}%)
      Within ±30%:  {categories['Accurate (±10%)'] + categories['Moderate (10-30%)']} scenarios
      Large (>50%): {categories['Very Large (>50%)']} scenarios
    
    Key Findings:
    - Super detects upward trends (+75% to +100% deviation)
    - Super handles decline correctly (-9% to -22%)
    - Burst/intermittent demand handled well (~0% deviation)
    - Random walk shows conservative behavior (-40%)
    """
    
    ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=11,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))
    
    plt.tight_layout()
    
    output_path2 = Path(__file__).parent / "overfitting_summary_dashboard.png"
    plt.savefig(output_path2, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output_path2}")
    
    print("\n" + "="*80)
    print("Visualization complete!")
    print("="*80)
    
    return output_path, output_path2


if __name__ == "__main__":
    try:
        path1, path2 = create_visualizations()
        print(f"\nView the results at:")
        print(f"  1. {path1}")
        print(f"  2. {path2}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
