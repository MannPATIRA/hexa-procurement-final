"""
Standalone visualization script to compare all three sales forecasters.

Run with: python tests/sales_forecaster/visualize_forecasters.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path (same as conftest.py)
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def create_comprehensive_visualization():
    """Create a comprehensive visualization comparing all three forecasters."""
    
    print("="*80)
    print("SALES FORECASTER COMPARISON VISUALIZATION")
    print("="*80)
    print("\nFetching data and generating forecasts...")
    
    # Fetch data
    erp_fetcher = MockERPDataFetcher()
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    # Generate forecasts with all three methods
    print("  - Running Basic Sales Forecaster...")
    basic_forecaster = BasicSalesForecaster()
    basic_forecast = basic_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    print("  - Running Advanced Sales Forecaster...")
    advanced_forecaster = AdvancedSalesForecaster()
    advanced_forecast = advanced_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    print("  - Running Super Advanced Sales Forecaster...")
    super_forecaster = SuperAdvancedSalesForecaster()
    super_forecast = super_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    # Print detailed comparison table
    print("\n" + "="*100)
    print("DETAILED COMPARISON TABLE")
    print("="*100)
    print(f"{'Product':<15} {'Basic Qty':<12} {'Advanced Qty':<14} {'Super Qty':<12} "
          f"{'Basic Rev':<12} {'Advanced Rev':<14} {'Super Rev':<12} {'Model':<15}")
    print("-"*100)
    
    for item in inventory_data.items:
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        super_item = super_forecast.forecasts_by_id.get(item.item_id)
        
        if basic_item and advanced_item and super_item:
            # Get model used from routing log
            routing = [r for r in super_forecaster.get_routing_log() if r['product_id'] == item.item_id]
            model_used = routing[0]['recommended_model'] if routing else 'N/A (fallback)'
            
            print(f"{item.item_name:<15} "
                  f"{basic_item.forecasted_quantity:<12} "
                  f"{advanced_item.forecasted_quantity:<14} "
                  f"{super_item.forecasted_quantity:<12} "
                  f"${basic_item.forecasted_revenue:<11.2f} "
                  f"${advanced_item.forecasted_revenue:<13.2f} "
                  f"${super_item.forecasted_revenue:<11.2f} "
                  f"{model_used:<15}")
    
    print("="*100)
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    basic_total_qty = sum(f.forecasted_quantity for f in basic_forecast.forecasts)
    advanced_total_qty = sum(f.forecasted_quantity for f in advanced_forecast.forecasts)
    super_total_qty = sum(f.forecasted_quantity for f in super_forecast.forecasts)
    
    basic_total_rev = sum(f.forecasted_revenue or 0 for f in basic_forecast.forecasts)
    advanced_total_rev = sum(f.forecasted_revenue or 0 for f in advanced_forecast.forecasts)
    super_total_rev = sum(f.forecasted_revenue or 0 for f in super_forecast.forecasts)
    
    basic_avg_conf = np.mean([f.confidence_level or 0 for f in basic_forecast.forecasts]) * 100
    advanced_avg_conf = np.mean([f.confidence_level or 0 for f in advanced_forecast.forecasts]) * 100
    super_avg_conf = np.mean([f.confidence_level or 0 for f in super_forecast.forecasts]) * 100
    
    print(f"Total Forecasted Quantity:")
    print(f"  Basic:      {basic_total_qty:>8,} units")
    print(f"  Advanced:   {advanced_total_qty:>8,} units ({((advanced_total_qty/basic_total_qty - 1)*100):+.1f}%)")
    print(f"  Super:      {super_total_qty:>8,} units ({((super_total_qty/basic_total_qty - 1)*100):+.1f}%)")
    
    print(f"\nTotal Forecasted Revenue:")
    print(f"  Basic:      ${basic_total_rev:>12,.2f}")
    print(f"  Advanced:   ${advanced_total_rev:>12,.2f} ({((advanced_total_rev/basic_total_rev - 1)*100):+.1f}%)")
    print(f"  Super:      ${super_total_rev:>12,.2f} ({((super_total_rev/basic_total_rev - 1)*100):+.1f}%)")
    
    print(f"\nAverage Confidence Level:")
    print(f"  Basic:      {basic_avg_conf:>6.1f}%")
    print(f"  Advanced:   {advanced_avg_conf:>6.1f}%")
    print(f"  Super:      {super_avg_conf:>6.1f}%")
    
    # Model routing summary
    model_summary = super_forecaster.get_model_summary()
    if model_summary:
        print(f"\nSuper Advanced - Model Routing:")
        for model, count in model_summary.items():
            print(f"  {model}: {count} product(s)")
    
    print("="*80)
    
    # Create comprehensive visualization
    print("\nGenerating visualization...")
    
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('Comprehensive Sales Forecaster Comparison', 
                 fontsize=20, fontweight='bold', y=0.995)
    
    products = [item.item_name for item in inventory_data.items]
    x = np.arange(len(products))
    width = 0.25
    
    # Extract data
    basic_quantities = [basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                       for item in inventory_data.items]
    advanced_quantities = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                          for item in inventory_data.items]
    super_quantities = [super_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                       for item in inventory_data.items]
    
    basic_revenues = [basic_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                     for item in inventory_data.items]
    advanced_revenues = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                        for item in inventory_data.items]
    super_revenues = [super_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                     for item in inventory_data.items]
    
    basic_confidences = [basic_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                        if basic_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                        for item in inventory_data.items]
    advanced_confidences = [advanced_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                           if advanced_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                           for item in inventory_data.items]
    super_confidences = [super_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                        if super_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                        for item in inventory_data.items]
    
    # Plot 1: Quantity Comparison (Top Left)
    ax1 = plt.subplot(3, 3, 1)
    ax1.bar(x - width, basic_quantities, width, label='Basic', alpha=0.8, color='#3498db')
    ax1.bar(x, advanced_quantities, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax1.bar(x + width, super_quantities, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax1.set_xlabel('Product', fontweight='bold')
    ax1.set_ylabel('Forecasted Quantity', fontweight='bold')
    ax1.set_title('Forecasted Quantities by Product', fontweight='bold', pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(products, rotation=15, ha='right')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Revenue Comparison (Top Middle)
    ax2 = plt.subplot(3, 3, 2)
    ax2.bar(x - width, basic_revenues, width, label='Basic', alpha=0.8, color='#3498db')
    ax2.bar(x, advanced_revenues, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax2.bar(x + width, super_revenues, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax2.set_xlabel('Product', fontweight='bold')
    ax2.set_ylabel('Forecasted Revenue ($)', fontweight='bold')
    ax2.set_title('Forecasted Revenue by Product', fontweight='bold', pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(products, rotation=15, ha='right')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Confidence Levels (Top Right)
    ax3 = plt.subplot(3, 3, 3)
    ax3.bar(x - width, basic_confidences, width, label='Basic', alpha=0.8, color='#3498db')
    ax3.bar(x, advanced_confidences, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax3.bar(x + width, super_confidences, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax3.set_xlabel('Product', fontweight='bold')
    ax3.set_ylabel('Confidence Level (%)', fontweight='bold')
    ax3.set_title('Confidence Levels by Product', fontweight='bold', pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(products, rotation=15, ha='right')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim([0, 105])
    
    # Plot 4: Percentage Difference from Basic - Quantities (Middle Left)
    ax4 = plt.subplot(3, 3, 4)
    adv_diff_pct = [(advanced_quantities[i] - basic_quantities[i]) / basic_quantities[i] * 100
                    if basic_quantities[i] > 0 else 0
                    for i in range(len(products))]
    super_diff_pct = [(super_quantities[i] - basic_quantities[i]) / basic_quantities[i] * 100
                     if basic_quantities[i] > 0 else 0
                     for i in range(len(products))]
    
    x_pos = np.arange(len(products))
    ax4.bar(x_pos - width/2, adv_diff_pct, width, label='Advanced vs Basic', alpha=0.7, color='#e74c3c')
    ax4.bar(x_pos + width/2, super_diff_pct, width, label='Super vs Basic', alpha=0.7, color='#2ecc71')
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax4.set_xlabel('Product', fontweight='bold')
    ax4.set_ylabel('Percentage Difference (%)', fontweight='bold')
    ax4.set_title('Quantity: % Difference from Basic', fontweight='bold', pad=10)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(products, rotation=15, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Total Summary Comparison (Middle Middle)
    ax5 = plt.subplot(3, 3, 5)
    categories = ['Total Quantity', 'Total Revenue', 'Avg Confidence']
    basic_values = [basic_total_qty / 1000, basic_total_rev / 1000, basic_avg_conf]
    advanced_values = [advanced_total_qty / 1000, advanced_total_rev / 1000, advanced_avg_conf]
    super_values = [super_total_qty / 1000, super_total_rev / 1000, super_avg_conf]
    
    x_cat = np.arange(len(categories))
    ax5.bar(x_cat - width, basic_values, width, label='Basic', alpha=0.8, color='#3498db')
    ax5.bar(x_cat, advanced_values, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax5.bar(x_cat + width, super_values, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax5.set_xlabel('Metric', fontweight='bold')
    ax5.set_ylabel('Value (Quantity/Revenue in 1000s, Confidence in %)', fontweight='bold')
    ax5.set_title('Aggregate Summary Comparison', fontweight='bold', pad=10)
    ax5.set_xticks(x_cat)
    ax5.set_xticklabels(categories, rotation=15, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Plot 6: Model Routing Distribution (Middle Right)
    ax6 = plt.subplot(3, 3, 6)
    if model_summary:
        labels = list(model_summary.keys())
        sizes = list(model_summary.values())
        colors_pie = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        wedges, texts, autotexts = ax6.pie(sizes, labels=labels, colors=colors_pie[:len(labels)], 
                                           autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
        ax6.set_title('Super Advanced - Model Routing', fontweight='bold', pad=10)
    else:
        ax6.text(0.5, 0.5, 'No routing data\n(All products used fallback)', 
                ha='center', va='center', fontsize=12)
        ax6.set_title('Model Routing Distribution', fontweight='bold', pad=10)
    
    # Plot 7: Revenue Percentage Difference (Bottom Left)
    ax7 = plt.subplot(3, 3, 7)
    adv_rev_diff_pct = [(advanced_revenues[i] - basic_revenues[i]) / basic_revenues[i] * 100
                        if basic_revenues[i] > 0 else 0
                        for i in range(len(products))]
    super_rev_diff_pct = [(super_revenues[i] - basic_revenues[i]) / basic_revenues[i] * 100
                         if basic_revenues[i] > 0 else 0
                         for i in range(len(products))]
    
    ax7.bar(x_pos - width/2, adv_rev_diff_pct, width, label='Advanced vs Basic', alpha=0.7, color='#e74c3c')
    ax7.bar(x_pos + width/2, super_rev_diff_pct, width, label='Super vs Basic', alpha=0.7, color='#2ecc71')
    ax7.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax7.set_xlabel('Product', fontweight='bold')
    ax7.set_ylabel('Percentage Difference (%)', fontweight='bold')
    ax7.set_title('Revenue: % Difference from Basic', fontweight='bold', pad=10)
    ax7.set_xticks(x_pos)
    ax7.set_xticklabels(products, rotation=15, ha='right')
    ax7.legend()
    ax7.grid(True, alpha=0.3, axis='y')
    
    # Plot 8: Confidence Difference (Bottom Middle)
    ax8 = plt.subplot(3, 3, 8)
    adv_conf_diff = [advanced_confidences[i] - basic_confidences[i] for i in range(len(products))]
    super_conf_diff = [super_confidences[i] - basic_confidences[i] for i in range(len(products))]
    
    ax8.bar(x_pos - width/2, adv_conf_diff, width, label='Advanced vs Basic', alpha=0.7, color='#e74c3c')
    ax8.bar(x_pos + width/2, super_conf_diff, width, label='Super vs Basic', alpha=0.7, color='#2ecc71')
    ax8.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax8.set_xlabel('Product', fontweight='bold')
    ax8.set_ylabel('Confidence Difference (pp)', fontweight='bold')
    ax8.set_title('Confidence: Difference from Basic', fontweight='bold', pad=10)
    ax8.set_xticks(x_pos)
    ax8.set_xticklabels(products, rotation=15, ha='right')
    ax8.legend()
    ax8.grid(True, alpha=0.3, axis='y')
    
    # Plot 9: Forecast Range Comparison (Bottom Right)
    ax9 = plt.subplot(3, 3, 9)
    # Show min, max, and average for each forecaster
    forecaster_names = ['Basic', 'Advanced', 'Super']
    min_quantities = [min(basic_quantities), min(advanced_quantities), min(super_quantities)]
    max_quantities = [max(basic_quantities), max(advanced_quantities), max(super_quantities)]
    avg_quantities = [np.mean(basic_quantities), np.mean(advanced_quantities), np.mean(super_quantities)]
    
    x_fore = np.arange(len(forecaster_names))
    ax9.bar(x_fore, min_quantities, width=0.6, label='Min', alpha=0.6, color='#95a5a6')
    ax9.bar(x_fore, avg_quantities, width=0.6, label='Average', alpha=0.8, color='#34495e')
    ax9.bar(x_fore, max_quantities, width=0.6, label='Max', alpha=0.6, color='#ecf0f1')
    ax9.set_xlabel('Forecaster', fontweight='bold')
    ax9.set_ylabel('Quantity', fontweight='bold')
    ax9.set_title('Forecast Range Comparison', fontweight='bold', pad=10)
    ax9.set_xticks(x_fore)
    ax9.set_xticklabels(forecaster_names)
    ax9.legend()
    ax9.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    
    # Save the plot
    output_dir = 'tests/sales_forecaster'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'comprehensive_forecaster_comparison.png')
    
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(output_path, dpi=150, bbox_inches='tight', format='png')
    
    print(f"✓ Comprehensive visualization saved to: {output_path}")
    
    plt.close('all')
    
    return output_path


if __name__ == "__main__":
    try:
        output_path = create_comprehensive_visualization()
        print(f"\n{'='*80}")
        print("Visualization complete!")
        print(f"View the results at: {output_path}")
        print(f"{'='*80}\n")
    except Exception as e:
        print(f"\nError generating visualization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
