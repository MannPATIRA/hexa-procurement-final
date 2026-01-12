"""Test that compares BasicSalesForecaster vs AdvancedSalesForecaster vs SuperAdvancedSalesForecaster."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher


def test_compare_forecasters_visualization():
    """Compare Basic vs Advanced forecasters and create visualization."""
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    # Generate forecasts with both methods
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
    import os
    output_dir = 'tests/sales_forecaster'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'forecaster_comparison.png')
    
    # Suppress any warnings and save
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(output_path, dpi=150, bbox_inches='tight', format='png')
    
    print(f"\n✓ Comparison visualization saved to: {output_path}")
    
    # Explicitly close all figures
    plt.close('all')
    
    # Assertions
    assert len(basic_forecast.forecasts) > 0
    assert len(advanced_forecast.forecasts) > 0
    assert len(basic_forecast.forecasts) == len(advanced_forecast.forecasts)
    assert os.path.exists(output_path), f"Visualization file was not created at {output_path}"


def test_compare_all_three_forecasters():
    """Compare Basic vs Advanced vs Super Advanced forecasters."""
    erp_fetcher = MockERPDataFetcher()
    
    inventory_data = erp_fetcher.fetch_inventory_data()
    sales_data = erp_fetcher.fetch_sales_data()
    forecast_period_days = 30
    
    # Generate forecasts with all three methods
    basic_forecaster = BasicSalesForecaster()
    advanced_forecaster = AdvancedSalesForecaster()
    super_forecaster = SuperAdvancedSalesForecaster()
    
    basic_forecast = basic_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    advanced_forecast = advanced_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    super_forecast = super_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    # Print comparison table
    print("\n" + "="*100)
    print("SALES FORECAST COMPARISON: Basic vs Advanced vs Super Advanced")
    print("="*100)
    print(f"{'Product':<12} {'Basic':<10} {'Advanced':<10} {'Super':<10} {'B vs A':<12} {'B vs S':<12} {'Model Used':<15}")
    print("-"*100)
    
    for item in inventory_data.items:
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        super_item = super_forecast.forecasts_by_id.get(item.item_id)
        
        if basic_item and advanced_item and super_item:
            diff_adv = advanced_item.forecasted_quantity - basic_item.forecasted_quantity
            diff_super = super_item.forecasted_quantity - basic_item.forecasted_quantity
            
            diff_adv_pct = (diff_adv / basic_item.forecasted_quantity * 100) if basic_item.forecasted_quantity > 0 else 0
            diff_super_pct = (diff_super / basic_item.forecasted_quantity * 100) if basic_item.forecasted_quantity > 0 else 0
            
            # Get model used from routing log
            routing = [r for r in super_forecaster.get_routing_log() if r['product_id'] == item.item_id]
            model_used = routing[0]['recommended_model'] if routing else 'N/A'
            
            print(f"{item.item_name:<12} {basic_item.forecasted_quantity:<10} "
                  f"{advanced_item.forecasted_quantity:<10} {super_item.forecasted_quantity:<10} "
                  f"{diff_adv:+.0f} ({diff_adv_pct:+.1f}%) "
                  f"{diff_super:+.0f} ({diff_super_pct:+.1f}%) "
                  f"{model_used:<15}")
    
    print("="*100)
    
    # Print model routing summary
    print("\nSuper Advanced - Model Routing Summary:")
    print("-"*50)
    for model, count in super_forecaster.get_model_summary().items():
        print(f"  {model}: {count} products")
    
    # Create comparison visualization
    import os
    import warnings
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('Sales Forecast Comparison: Basic vs Advanced vs Super Advanced', 
                 fontsize=16, fontweight='bold')
    
    products = [item.item_name for item in inventory_data.items]
    basic_quantities = [basic_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                       for item in inventory_data.items]
    advanced_quantities = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                          for item in inventory_data.items]
    super_quantities = [super_forecast.forecasts_by_id[item.item_id].forecasted_quantity 
                       for item in inventory_data.items]
    
    x = range(len(products))
    width = 0.25
    
    # Plot 1: Quantity Comparison
    ax1 = axes[0, 0]
    ax1.bar([i - width for i in x], basic_quantities, width, label='Basic', alpha=0.8, color='#3498db')
    ax1.bar(x, advanced_quantities, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax1.bar([i + width for i in x], super_quantities, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax1.set_xlabel('Product', fontweight='bold')
    ax1.set_ylabel('Forecasted Quantity', fontweight='bold')
    ax1.set_title('Forecasted Quantities by Product', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(products, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Revenue Comparison
    ax2 = axes[0, 1]
    basic_revenues = [basic_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                     for item in inventory_data.items]
    advanced_revenues = [advanced_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                        for item in inventory_data.items]
    super_revenues = [super_forecast.forecasts_by_id[item.item_id].forecasted_revenue 
                     for item in inventory_data.items]
    
    ax2.bar([i - width for i in x], basic_revenues, width, label='Basic', alpha=0.8, color='#3498db')
    ax2.bar(x, advanced_revenues, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax2.bar([i + width for i in x], super_revenues, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax2.set_xlabel('Product', fontweight='bold')
    ax2.set_ylabel('Forecasted Revenue ($)', fontweight='bold')
    ax2.set_title('Forecasted Revenue by Product', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(products, rotation=15, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Confidence Levels
    ax3 = axes[1, 0]
    basic_confidences = [basic_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                        if basic_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                        for item in inventory_data.items]
    advanced_confidences = [advanced_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                           if advanced_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                           for item in inventory_data.items]
    super_confidences = [super_forecast.forecasts_by_id[item.item_id].confidence_level * 100
                        if super_forecast.forecasts_by_id[item.item_id].confidence_level else 0
                        for item in inventory_data.items]
    
    ax3.bar([i - width for i in x], basic_confidences, width, label='Basic', alpha=0.8, color='#3498db')
    ax3.bar(x, advanced_confidences, width, label='Advanced', alpha=0.8, color='#e74c3c')
    ax3.bar([i + width for i in x], super_confidences, width, label='Super Advanced', alpha=0.8, color='#2ecc71')
    ax3.set_xlabel('Product', fontweight='bold')
    ax3.set_ylabel('Confidence Level (%)', fontweight='bold')
    ax3.set_title('Confidence Levels Comparison', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(products, rotation=15, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim([0, 105])
    
    # Plot 4: Model routing (pie chart)
    ax4 = axes[1, 1]
    model_summary = super_forecaster.get_model_summary()
    if model_summary:
        labels = list(model_summary.keys())
        sizes = list(model_summary.values())
        colors_pie = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        ax4.pie(sizes, labels=labels, colors=colors_pie[:len(labels)], autopct='%1.1f%%', startangle=90)
        ax4.set_title('Super Advanced - Model Selection Distribution', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No routing data', ha='center', va='center')
        ax4.set_title('Model Selection Distribution', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the plot
    output_dir = 'tests/sales_forecaster'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'all_forecasters_comparison.png')
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(output_path, dpi=150, bbox_inches='tight', format='png')
    
    print(f"\n✓ All forecasters comparison saved to: {output_path}")
    
    plt.close('all')
    
    # Assertions
    assert len(basic_forecast.forecasts) > 0
    assert len(advanced_forecast.forecasts) > 0
    assert len(super_forecast.forecasts) > 0
    assert len(basic_forecast.forecasts) == len(super_forecast.forecasts)
    assert os.path.exists(output_path)
