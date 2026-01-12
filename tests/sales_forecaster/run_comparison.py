#!/usr/bin/env python3
"""Standalone script to compare forecasters and generate visualization."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher

def main():
    """Compare Basic vs Advanced forecasters and create visualization."""
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    # Generate forecasts with both methods
    print("Generating forecasts...")
    basic_forecaster = BasicSalesForecaster()
    advanced_forecaster = AdvancedSalesForecaster()
    
    basic_forecast = basic_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    advanced_forecast = advanced_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    # Print comparison table
    print("\n" + "="*80)
    print("SALES FORECAST COMPARISON: Basic vs Advanced")
    print("="*80)
    print(f"{'Product':<15} {'Basic Qty':<12} {'Advanced Qty':<14} {'Difference':<12} {'Basic Rev':<12} {'Advanced Rev':<14}")
    print("-"*80)
    
    for item in inventory_data.items:
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        
        if basic_item and advanced_item:
            diff_qty = advanced_item.forecasted_quantity - basic_item.forecasted_quantity
            diff_pct = (diff_qty / basic_item.forecasted_quantity * 100) if basic_item.forecasted_quantity > 0 else 0
            
            print(f"{item.item_name:<15} {basic_item.forecasted_quantity:<12} "
                  f"{advanced_item.forecasted_quantity:<14} {diff_qty:+.1f} ({diff_pct:+.1f}%) "
                  f"${basic_item.forecasted_revenue:<11.2f} ${advanced_item.forecasted_revenue:<13.2f}")
    
    print("="*80)
    
    # Create comparison visualization
    print("Creating visualization...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Sales Forecast Comparison: Basic vs Advanced Forecaster', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Quantity Comparison by Product
    ax1 = axes[0, 0]
    products = [item.item_name for item in inventory_data.items]
    basic_quantities = [basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                       for item in inventory_data.items]
    advanced_quantities = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                          for item in inventory_data.items]
    
    x = range(len(products))
    width = 0.35
    ax1.bar([i - width/2 for i in x], basic_quantities, width, label='Basic', alpha=0.8, color='#3498db')
    ax1.bar([i + width/2 for i in x], advanced_quantities, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax1.set_xlabel('Product', fontweight='bold')
    ax1.set_ylabel('Forecasted Quantity', fontweight='bold')
    ax1.set_title('Forecasted Quantities by Product', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(products, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Revenue Comparison by Product
    ax2 = axes[0, 1]
    basic_revenues = [basic_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                     for item in inventory_data.items]
    advanced_revenues = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                        for item in inventory_data.items]
    
    ax2.bar([i - width/2 for i in x], basic_revenues, width, label='Basic', alpha=0.8, color='#3498db')
    ax2.bar([i + width/2 for i in x], advanced_revenues, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax2.set_xlabel('Product', fontweight='bold')
    ax2.set_ylabel('Forecasted Revenue ($)', fontweight='bold')
    ax2.set_title('Forecasted Revenue by Product', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(products, rotation=15, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Percentage Difference
    ax3 = axes[1, 0]
    differences = [(advanced_forecast.forecasts_by_id[item.item_id].forecasted_quantity - 
                   basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity) / 
                  basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity * 100
                  if basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity > 0 else 0
                  for item in inventory_data.items]
    
    colors = ['green' if d >= 0 else 'red' for d in differences]
    ax3.bar(products, differences, alpha=0.7, color=colors)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax3.set_xlabel('Product', fontweight='bold')
    ax3.set_ylabel('Percentage Difference (%)', fontweight='bold')
    ax3.set_title('Percentage Difference: Advanced vs Basic', fontweight='bold')
    ax3.set_xticklabels(products, rotation=15, ha='right')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Confidence Levels Comparison
    ax4 = axes[1, 1]
    basic_confidences = [basic_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                        if basic_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                        for item in inventory_data.items]
    advanced_confidences = [advanced_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                           if advanced_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                           for item in inventory_data.items]
    
    ax4.bar([i - width/2 for i in x], basic_confidences, width, label='Basic', alpha=0.8, color='#3498db')
    ax4.bar([i + width/2 for i in x], advanced_confidences, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax4.set_xlabel('Product', fontweight='bold')
    ax4.set_ylabel('Confidence Level (%)', fontweight='bold')
    ax4.set_title('Confidence Levels Comparison', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(products, rotation=15, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_ylim([0, 105])
    
    plt.tight_layout()
    
    # Save the plot
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, 'forecaster_comparison.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', format='png')
    print(f"\n✓ Comparison visualization saved to: {output_path}")
    
    plt.close('all')
    print("Done!")

if __name__ == '__main__':
    main()
