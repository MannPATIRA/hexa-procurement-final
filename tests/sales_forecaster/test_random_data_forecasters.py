"""
Test script to compare forecasters with random/fake datasets.
Investigates discrepancies, especially for Widget D.
"""

import sys
from pathlib import Path
import os

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import random

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from models.inventory_data import InventoryData, InventoryItem, ItemType
from models.sales_data import SalesData, SalesRecord


def generate_random_sales_data(
    product_id: str,
    product_name: str,
    num_records: int,
    days_back: int,
    base_quantity: float = 10.0,
    quantity_variance: float = 0.3,
    trend: float = 0.0,  # 0 = no trend, positive = increasing, negative = decreasing
    seasonality: bool = False,
    unit_price: float = 25.0
) -> list[SalesRecord]:
    """Generate random sales records for a product."""
    records = []
    now = datetime.now()
    
    for i in range(num_records):
        # Distribute records over the time period
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Base quantity with trend
        trend_factor = 1.0 + (trend * (days_back - days_ago) / days_back)
        
        # Add seasonality if requested (weekly pattern)
        seasonality_factor = 1.0
        if seasonality:
            day_of_week = timestamp.weekday()
            # Higher sales on weekdays, lower on weekends
            seasonality_factor = 1.2 if day_of_week < 5 else 0.7
        
        # Random variance
        variance = random.uniform(1 - quantity_variance, 1 + quantity_variance)
        
        quantity = max(1, int(base_quantity * trend_factor * seasonality_factor * variance))
        
        total_revenue = quantity * unit_price
        
        records.append(SalesRecord(
            timestamp=timestamp,
            product_id=product_id,
            product_name=product_name,
            quantity_sold=quantity,
            unit_price=unit_price,
            total_revenue=total_revenue,
            customer_id=f"CUST-{random.randint(1, 10):03d}"
        ))
    
    # Sort by timestamp
    records.sort(key=lambda x: x.timestamp)
    return records


def create_test_dataset(
    dataset_name: str,
    num_products: int = 4,
    days_back: int = 30,
    records_per_product: int = 5
) -> tuple[InventoryData, SalesData]:
    """Create a test dataset with random sales data."""
    now = datetime.now()
    start_date = now - timedelta(days=days_back)
    
    inventory_items = []
    all_sales_records = []
    
    # Generate products with different characteristics
    product_configs = [
        {"base_qty": 15, "variance": 0.3, "trend": 0.0, "seasonality": False, "price": 25.5},
        {"base_qty": 8, "variance": 0.4, "trend": 0.1, "seasonality": False, "price": 45.0},
        {"base_qty": 5, "variance": 0.5, "trend": -0.05, "seasonality": True, "price": 75.0},
        {"base_qty": 20, "variance": 0.25, "trend": 0.05, "seasonality": False, "price": 35.0},
    ]
    
    for i in range(num_products):
        product_id = f"PROD-{i+1:03d}"
        product_name = f"Widget {chr(65+i)}"  # A, B, C, D
        
        config = product_configs[i % len(product_configs)]
        
        # Create inventory item
        inventory_items.append(InventoryItem(
            item_id=product_id,
            item_name=product_name,
            item_type=ItemType.PRODUCT,
            quantity=random.randint(10, 200),
            unit_price=config["price"],
            location=f"Warehouse-{(i % 3) + 1}",
            last_updated=now - timedelta(days=random.randint(0, 7)),
            supplier_id=f"SUP-{(i % 3) + 1:03d}"
        ))
        
        # Generate sales records
        records = generate_random_sales_data(
            product_id=product_id,
            product_name=product_name,
            num_records=records_per_product,
            days_back=days_back,
            base_quantity=config["base_qty"],
            quantity_variance=config["variance"],
            trend=config["trend"],
            seasonality=config["seasonality"],
            unit_price=config["price"]
        )
        all_sales_records.extend(records)
    
    # Create data structures
    inventory_data = InventoryData(
        items=inventory_items,
        fetched_at=now
    )
    
    sales_data = SalesData(
        records=all_sales_records,
        start_date=start_date,
        end_date=now,
        fetched_at=now
    )
    
    return inventory_data, sales_data


def compare_forecasters_on_dataset(
    dataset_name: str,
    inventory_data: InventoryData,
    sales_data: SalesData,
    forecast_period_days: int = 30
) -> dict:
    """Compare all three forecasters on a dataset and return results."""
    results = {
        "dataset_name": dataset_name,
        "products": {},
        "discrepancies": []
    }
    
    # Generate forecasts
    basic_forecaster = BasicSalesForecaster()
    advanced_forecaster = AdvancedSalesForecaster()
    super_forecaster = SuperAdvancedSalesForecaster()
    
    basic_forecast = basic_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    advanced_forecast = advanced_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    super_forecast = super_forecaster.forecast_sales(inventory_data, sales_data, forecast_period_days)
    
    # Analyze each product
    for item in inventory_data.items:
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        super_item = super_forecast.forecasts_by_id.get(item.item_id)
        
        if not (basic_item and advanced_item and super_item):
            continue
        
        # Get sales history for this product
        product_records = sales_data.records_by_product.get(item.item_id, [])
        quantities = [r.quantity_sold for r in product_records]
        
        product_result = {
            "product_id": item.item_id,
            "product_name": item.item_name,
            "num_sales_records": len(product_records),
            "total_historical_qty": sum(quantities),
            "avg_historical_qty": np.mean(quantities) if quantities else 0,
            "basic_qty": basic_item.forecasted_quantity,
            "advanced_qty": advanced_item.forecasted_quantity,
            "super_qty": super_item.forecasted_quantity,
            "basic_rev": basic_item.forecasted_revenue,
            "advanced_rev": advanced_item.forecasted_revenue,
            "super_rev": super_item.forecasted_revenue,
            "basic_conf": basic_item.confidence_level or 0,
            "advanced_conf": advanced_item.confidence_level or 0,
            "super_conf": super_item.confidence_level or 0,
        }
        
        # Calculate differences
        if basic_item.forecasted_quantity > 0:
            product_result["super_vs_basic_pct"] = (
                (super_item.forecasted_quantity - basic_item.forecasted_quantity) / 
                basic_item.forecasted_quantity * 100
            )
            product_result["advanced_vs_basic_pct"] = (
                (advanced_item.forecasted_quantity - basic_item.forecasted_quantity) / 
                basic_item.forecasted_quantity * 100
            )
        else:
            product_result["super_vs_basic_pct"] = 0
            product_result["advanced_vs_basic_pct"] = 0
        
        # Check for large discrepancies (>30% difference)
        if abs(product_result["super_vs_basic_pct"]) > 30:
            product_result["large_discrepancy"] = True
            results["discrepancies"].append(product_result)
        else:
            product_result["large_discrepancy"] = False
        
        # Get model routing info
        routing = [r for r in super_forecaster.get_routing_log() if r['product_id'] == item.item_id]
        if routing:
            product_result["model_used"] = routing[0]['recommended_model']
            product_result["history_length"] = routing[0].get('history_length', 0)
            product_result["zero_ratio"] = routing[0].get('zero_ratio', 0)
            product_result["data_quality"] = routing[0].get('data_quality', 0)
        else:
            product_result["model_used"] = "fallback"
            product_result["history_length"] = 0
            product_result["zero_ratio"] = 0
            product_result["data_quality"] = 0
        
        results["products"][item.item_id] = product_result
    
    return results


def run_comprehensive_tests():
    """Run multiple test scenarios with different data characteristics."""
    print("="*100)
    print("COMPREHENSIVE FORECASTER COMPARISON WITH RANDOM DATA")
    print("="*100)
    
    test_scenarios = [
        ("Sparse Data (3 records)", 4, 30, 3),
        ("Normal Data (5 records)", 4, 30, 5),
        ("Dense Data (10 records)", 4, 30, 10),
        ("Short History (15 days)", 4, 15, 5),
        ("Long History (60 days)", 4, 60, 8),
        ("Very Sparse (2 records)", 4, 30, 2),
        ("High Variance", 4, 30, 5),
        ("Trending Up", 4, 30, 5),
        ("Trending Down", 4, 30, 5),
        ("Seasonal Pattern", 4, 30, 5),
    ]
    
    all_results = []
    all_discrepancies = []
    
    for scenario_name, num_products, days_back, records_per_product in test_scenarios:
        print(f"\n{'='*100}")
        print(f"Testing: {scenario_name}")
        print(f"{'='*100}")
        
        # Generate dataset
        inventory_data, sales_data = create_test_dataset(
            dataset_name=scenario_name,
            num_products=num_products,
            days_back=days_back,
            records_per_product=records_per_product
        )
        
        # Compare forecasters
        results = compare_forecasters_on_dataset(
            scenario_name,
            inventory_data,
            sales_data,
            forecast_period_days=30
        )
        
        all_results.append(results)
        
        # Print summary for this scenario
        print(f"\nResults for {scenario_name}:")
        print(f"{'Product':<15} {'Basic':<10} {'Advanced':<10} {'Super':<10} {'Super%':<10} {'Model':<15}")
        print("-"*80)
        
        for product_id, product_result in results["products"].items():
            print(f"{product_result['product_name']:<15} "
                  f"{product_result['basic_qty']:<10} "
                  f"{product_result['advanced_qty']:<10} "
                  f"{product_result['super_qty']:<10} "
                  f"{product_result['super_vs_basic_pct']:>+8.1f}% "
                  f"{product_result['model_used']:<15}")
        
        # Track large discrepancies
        if results["discrepancies"]:
            print(f"\n⚠️  Large discrepancies found ({len(results['discrepancies'])}):")
            for disc in results["discrepancies"]:
                print(f"  - {disc['product_name']}: Super={disc['super_qty']}, Basic={disc['basic_qty']}, "
                      f"Diff={disc['super_vs_basic_pct']:+.1f}%, Model={disc['model_used']}, "
                      f"Records={disc['num_sales_records']}, History={disc['history_length']}")
                all_discrepancies.append({
                    "scenario": scenario_name,
                    **disc
                })
    
    # Summary analysis
    print(f"\n{'='*100}")
    print("SUMMARY ANALYSIS")
    print(f"{'='*100}")
    
    print(f"\nTotal scenarios tested: {len(test_scenarios)}")
    print(f"Total large discrepancies (>30%): {len(all_discrepancies)}")
    
    if all_discrepancies:
        print(f"\n⚠️  Products with large discrepancies:")
        print(f"{'Scenario':<25} {'Product':<15} {'Super':<10} {'Basic':<10} {'Diff%':<10} {'Model':<15} {'Records':<10}")
        print("-"*100)
        
        # Group by product name
        by_product = defaultdict(list)
        for disc in all_discrepancies:
            by_product[disc['product_name']].append(disc)
        
        for product_name, discs in sorted(by_product.items()):
            for disc in discs:
                print(f"{disc['scenario']:<25} "
                      f"{disc['product_name']:<15} "
                      f"{disc['super_qty']:<10} "
                      f"{disc['basic_qty']:<10} "
                      f"{disc['super_vs_basic_pct']:>+8.1f}% "
                      f"{disc['model_used']:<15} "
                      f"{disc['num_sales_records']:<10}")
        
        # Focus on Widget D specifically
        widget_d_discrepancies = [d for d in all_discrepancies if d['product_name'] == 'Widget D']
        if widget_d_discrepancies:
            print(f"\n{'='*100}")
            print("WIDGET D SPECIFIC ANALYSIS")
            print(f"{'='*100}")
            print(f"Found {len(widget_d_discrepancies)} scenarios with Widget D discrepancies:")
            for disc in widget_d_discrepancies:
                print(f"\n  Scenario: {disc['scenario']}")
                print(f"    Super Advanced: {disc['super_qty']} units")
                print(f"    Basic:          {disc['basic_qty']} units")
                print(f"    Advanced:       {disc['advanced_qty']} units")
                print(f"    Difference:     {disc['super_vs_basic_pct']:+.1f}%")
                print(f"    Model Used:     {disc['model_used']}")
                print(f"    Sales Records:  {disc['num_sales_records']}")
                print(f"    History Length: {disc['history_length']}")
                print(f"    Zero Ratio:     {disc['zero_ratio']:.2f}")
                print(f"    Data Quality:   {disc['data_quality']:.2f}")
                print(f"    Total Historical Qty: {disc['total_historical_qty']}")
                print(f"    Avg Historical Qty:   {disc['avg_historical_qty']:.2f}")
    
    return all_results, all_discrepancies


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    try:
        results, discrepancies = run_comprehensive_tests()
        print(f"\n{'='*100}")
        print("Testing complete!")
        print(f"{'='*100}\n")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
