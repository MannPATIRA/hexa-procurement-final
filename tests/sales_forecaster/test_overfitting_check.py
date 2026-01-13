"""
Overfitting Check: Test forecasters with diverse random datasets
to ensure the model generalizes well beyond Widget A-D data.

Tests multiple scenarios:
1. Different data densities (sparse to dense)
2. Different trends (up, down, flat, volatile)
3. Different seasonalities
4. Different price ranges
5. Different history lengths
6. Edge cases (single record, all zeros, constant values)
"""

import sys
from pathlib import Path
import os
import json
import random
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Tuple, Dict

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from sales_forecaster.advanced_sales_forecaster import AdvancedSalesForecaster
from sales_forecaster.super_advanced_sales_forecaster import SuperAdvancedSalesForecaster
from models.inventory_data import InventoryData, InventoryItem, ItemType
from models.sales_data import SalesData, SalesRecord

LOG_PATH = "/Users/ishaanmakkar/Documents/hexa-procurement-final/.cursor/debug.log"


def log_debug(message: str, data: dict, hypothesis_id: str = "OVERFIT"):
    """Log debug information."""
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps({
                "sessionId": "overfitting-check",
                "runId": "generalization-test",
                "hypothesisId": hypothesis_id,
                "location": "test_overfitting_check.py",
                "message": message,
                "data": data,
                "timestamp": __import__('time').time() * 1000
            }) + '\n')
    except:
        pass


def generate_product_data(
    product_id: str,
    product_name: str,
    config: dict,
    days_back: int = 30
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate a single product with configurable characteristics."""
    now = datetime.now()
    
    num_records = config.get("num_records", 5)
    base_quantity = config.get("base_quantity", 10)
    variance = config.get("variance", 0.3)
    trend = config.get("trend", 0.0)  # positive = increasing
    seasonality = config.get("seasonality", False)
    unit_price = config.get("unit_price", 25.0)
    
    records = []
    
    for i in range(num_records):
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Apply trend
        trend_factor = 1.0 + (trend * (days_back - days_ago) / days_back)
        
        # Apply seasonality
        seasonality_factor = 1.0
        if seasonality:
            day_of_week = timestamp.weekday()
            seasonality_factor = 1.3 if day_of_week < 5 else 0.6
        
        # Random variance
        variance_factor = random.uniform(1 - variance, 1 + variance)
        
        quantity = max(1, int(base_quantity * trend_factor * seasonality_factor * variance_factor))
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


# ============================================================================
# SPECIALIZED DATA GENERATORS FOR COMPLEX PATTERNS
# ============================================================================

def generate_exponential_sales(
    product_id: str,
    product_name: str,
    base_quantity: int,
    growth_rate: float,  # positive for growth, negative for decay
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with exponential growth or decay pattern."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        # Evenly distribute records over time
        days_ago = days_back * (num_records - i - 1) / max(1, num_records - 1)
        timestamp = now - timedelta(days=days_ago)
        
        # Exponential factor: e^(growth_rate * progress)
        progress = (days_back - days_ago) / days_back  # 0 to 1
        exp_factor = np.exp(growth_rate * progress)
        
        quantity = max(1, int(base_quantity * exp_factor * random.uniform(0.9, 1.1)))
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_step_change_sales(
    product_id: str,
    product_name: str,
    base_quantity: int,
    multiplier: float,  # multiplier after step change
    change_day: int,  # days ago when change occurred
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with sudden step change (up or down)."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Apply step change: before change_day use base, after use multiplied
        if days_ago > change_day:
            quantity = base_quantity
        else:
            quantity = int(base_quantity * multiplier)
        
        # Add some noise
        quantity = max(1, int(quantity * random.uniform(0.85, 1.15)))
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_cyclical_sales(
    product_id: str,
    product_name: str,
    base_quantity: int,
    amplitude: float,  # amplitude as fraction of base (e.g., 0.5 = ±50%)
    period_days: int,  # length of one cycle
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with cyclical/sine wave pattern."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Sine wave pattern
        cycle_position = 2 * np.pi * (days_back - days_ago) / period_days
        wave_factor = 1 + amplitude * np.sin(cycle_position)
        
        quantity = max(1, int(base_quantity * wave_factor * random.uniform(0.9, 1.1)))
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_random_walk_sales(
    product_id: str,
    product_name: str,
    base_quantity: int,
    step_size: float,  # max step as fraction of current value
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with random walk (no trend, pure noise)."""
    now = datetime.now()
    records = []
    
    current_qty = base_quantity
    
    for i in range(num_records):
        days_ago = days_back * (num_records - i - 1) / max(1, num_records - 1)
        timestamp = now - timedelta(days=days_ago)
        
        # Random walk step
        step = current_qty * step_size * random.uniform(-1, 1)
        current_qty = max(1, int(current_qty + step))
        
        records.append(SalesRecord(
            timestamp=timestamp,
            product_id=product_id,
            product_name=product_name,
            quantity_sold=current_qty,
            unit_price=unit_price,
            total_revenue=current_qty * unit_price,
            customer_id=f"CUST-{random.randint(1, 100):03d}"
        ))
    
    records.sort(key=lambda x: x.timestamp)
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_outlier_sales(
    product_id: str,
    product_name: str,
    base_quantity: int,
    outlier_multiplier: float,  # how much bigger outliers are
    outlier_probability: float,  # probability of outlier
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with occasional extreme outliers."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Decide if this is an outlier
        if random.random() < outlier_probability:
            quantity = int(base_quantity * outlier_multiplier * random.uniform(0.8, 1.2))
        else:
            quantity = int(base_quantity * random.uniform(0.85, 1.15))
        
        quantity = max(1, quantity)
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_bimodal_sales(
    product_id: str,
    product_name: str,
    low_quantity: int,
    high_quantity: int,
    high_probability: float,  # probability of high mode
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with bi-modal distribution (alternating high/low)."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        days_ago = random.uniform(0, days_back)
        timestamp = now - timedelta(days=days_ago)
        
        # Choose mode
        if random.random() < high_probability:
            quantity = int(high_quantity * random.uniform(0.9, 1.1))
        else:
            quantity = int(low_quantity * random.uniform(0.9, 1.1))
        
        quantity = max(1, quantity)
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_burst_sales(
    product_id: str,
    product_name: str,
    burst_quantity: int,
    burst_duration_days: int,
    silence_duration_days: int,
    num_bursts: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with burst patterns (clusters followed by silence)."""
    now = datetime.now()
    records = []
    
    cycle_length = burst_duration_days + silence_duration_days
    
    for burst in range(num_bursts):
        burst_start = days_back - (burst * cycle_length)
        burst_end = burst_start - burst_duration_days
        
        if burst_end < 0:
            break
        
        # Generate records within burst
        num_records_per_burst = random.randint(3, 6)
        for _ in range(num_records_per_burst):
            days_ago = random.uniform(max(0, burst_end), min(days_back, burst_start))
            timestamp = now - timedelta(days=days_ago)
            
            quantity = max(1, int(burst_quantity * random.uniform(0.8, 1.2)))
            
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def generate_linear_ramp_sales(
    product_id: str,
    product_name: str,
    start_quantity: int,
    end_quantity: int,
    num_records: int,
    days_back: int,
    unit_price: float = 25.0
) -> Tuple[InventoryItem, List[SalesRecord]]:
    """Generate sales data with linear increase/decrease over time."""
    now = datetime.now()
    records = []
    
    for i in range(num_records):
        # Evenly distribute records
        days_ago = days_back * (num_records - i - 1) / max(1, num_records - 1)
        timestamp = now - timedelta(days=days_ago)
        
        # Linear interpolation
        progress = (days_back - days_ago) / days_back
        quantity = int(start_quantity + (end_quantity - start_quantity) * progress)
        quantity = max(1, int(quantity * random.uniform(0.9, 1.1)))
        
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
    
    inventory_item = InventoryItem(
        item_id=product_id,
        item_name=product_name,
        item_type=ItemType.PRODUCT,
        quantity=random.randint(50, 500),
        unit_price=unit_price,
        location=f"Warehouse-{random.randint(1, 5)}",
        last_updated=now - timedelta(days=random.randint(0, 7)),
        supplier_id=f"SUP-{random.randint(1, 10):03d}"
    )
    
    return inventory_item, records


def run_single_test(
    test_name: str,
    products_config: List[dict],
    forecast_days: int = 30
) -> dict:
    """Run a single test scenario and return results."""
    now = datetime.now()
    
    inventory_items = []
    all_records = []
    
    for i, config in enumerate(products_config):
        product_id = f"TEST-{i+1:03d}"
        product_name = f"Product {chr(65+i)}"
        
        # Check if special generator is specified
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
            # Default generator
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
    
    # Run all three forecasters
    basic = BasicSalesForecaster()
    advanced = AdvancedSalesForecaster()
    super_adv = SuperAdvancedSalesForecaster()
    
    basic_forecast = basic.forecast_sales(inventory_data, sales_data, forecast_days)
    advanced_forecast = advanced.forecast_sales(inventory_data, sales_data, forecast_days)
    super_forecast = super_adv.forecast_sales(inventory_data, sales_data, forecast_days)
    
    results = {
        "test_name": test_name,
        "num_products": len(products_config),
        "products": []
    }
    
    for i, (config, item) in enumerate(zip(products_config, inventory_items)):
        product_records = [r for r in all_records if r.product_id == item.item_id]
        historical_qty = sum(r.quantity_sold for r in product_records)
        
        basic_item = basic_forecast.forecasts_by_id.get(item.item_id)
        advanced_item = advanced_forecast.forecasts_by_id.get(item.item_id)
        super_item = super_forecast.forecasts_by_id.get(item.item_id)
        
        if not (basic_item and advanced_item and super_item):
            continue
        
        product_result = {
            "product_id": item.item_id,
            "config": config,
            "historical_qty": historical_qty,
            "num_records": len(product_records),
            "basic_qty": basic_item.forecasted_quantity,
            "advanced_qty": advanced_item.forecasted_quantity,
            "super_qty": super_item.forecasted_quantity,
            "basic_conf": basic_item.confidence_level or 0,
            "advanced_conf": advanced_item.confidence_level or 0,
            "super_conf": super_item.confidence_level or 0,
        }
        
        # Calculate deviation from basic
        if basic_item.forecasted_quantity > 0:
            product_result["super_vs_basic_pct"] = (
                (super_item.forecasted_quantity - basic_item.forecasted_quantity) /
                basic_item.forecasted_quantity * 100
            )
        else:
            product_result["super_vs_basic_pct"] = 0
        
        results["products"].append(product_result)
    
    return results


def run_overfitting_tests():
    """Run comprehensive overfitting tests."""
    print("="*100)
    print("OVERFITTING CHECK: Testing Model Generalization")
    print("="*100)
    
    all_results = []
    all_deviations = []
    
    # Test Scenarios - designed to be very different from Widget A-D
    test_scenarios = [
        # Scenario 1: Very sparse data (opposite of dense Widget data)
        {
            "name": "Very Sparse Data (1-2 records)",
            "products": [
                {"num_records": 1, "base_quantity": 50, "variance": 0, "days_back": 30, "unit_price": 100},
                {"num_records": 2, "base_quantity": 25, "variance": 0.2, "days_back": 30, "unit_price": 50},
                {"num_records": 2, "base_quantity": 100, "variance": 0.1, "days_back": 60, "unit_price": 200},
            ]
        },
        # Scenario 2: Very dense data
        {
            "name": "Very Dense Data (20-30 records)",
            "products": [
                {"num_records": 20, "base_quantity": 5, "variance": 0.4, "days_back": 30, "unit_price": 15},
                {"num_records": 25, "base_quantity": 10, "variance": 0.3, "days_back": 45, "unit_price": 30},
                {"num_records": 30, "base_quantity": 8, "variance": 0.5, "days_back": 60, "unit_price": 25},
            ]
        },
        # Scenario 3: Strong upward trend
        {
            "name": "Strong Upward Trend",
            "products": [
                {"num_records": 8, "base_quantity": 5, "trend": 0.5, "variance": 0.2, "days_back": 30, "unit_price": 40},
                {"num_records": 10, "base_quantity": 3, "trend": 0.8, "variance": 0.15, "days_back": 45, "unit_price": 60},
            ]
        },
        # Scenario 4: Strong downward trend
        {
            "name": "Strong Downward Trend",
            "products": [
                {"num_records": 8, "base_quantity": 30, "trend": -0.5, "variance": 0.2, "days_back": 30, "unit_price": 40},
                {"num_records": 10, "base_quantity": 50, "trend": -0.7, "variance": 0.15, "days_back": 45, "unit_price": 20},
            ]
        },
        # Scenario 5: High volatility
        {
            "name": "High Volatility (0.8+ variance)",
            "products": [
                {"num_records": 10, "base_quantity": 20, "variance": 0.8, "days_back": 30, "unit_price": 35},
                {"num_records": 12, "base_quantity": 15, "variance": 0.9, "days_back": 40, "unit_price": 45},
            ]
        },
        # Scenario 6: Very low volatility (constant-ish)
        {
            "name": "Low Volatility (near constant)",
            "products": [
                {"num_records": 10, "base_quantity": 50, "variance": 0.05, "days_back": 30, "unit_price": 100},
                {"num_records": 8, "base_quantity": 25, "variance": 0.08, "days_back": 25, "unit_price": 75},
            ]
        },
        # Scenario 7: Seasonal pattern
        {
            "name": "Seasonal Pattern",
            "products": [
                {"num_records": 15, "base_quantity": 20, "seasonality": True, "variance": 0.2, "days_back": 45, "unit_price": 30},
                {"num_records": 12, "base_quantity": 10, "seasonality": True, "variance": 0.3, "days_back": 35, "unit_price": 55},
            ]
        },
        # Scenario 8: Mixed patterns
        {
            "name": "Mixed Patterns",
            "products": [
                {"num_records": 3, "base_quantity": 100, "variance": 0.5, "days_back": 30, "unit_price": 10},  # sparse, high qty
                {"num_records": 20, "base_quantity": 2, "variance": 0.2, "days_back": 30, "unit_price": 500},  # dense, low qty
                {"num_records": 8, "base_quantity": 15, "trend": 0.3, "variance": 0.3, "days_back": 60, "unit_price": 45},
            ]
        },
        # Scenario 9: Extreme price ranges
        {
            "name": "Extreme Price Ranges",
            "products": [
                {"num_records": 5, "base_quantity": 1000, "variance": 0.3, "days_back": 30, "unit_price": 0.50},  # cheap, high volume
                {"num_records": 5, "base_quantity": 1, "variance": 0.2, "days_back": 30, "unit_price": 5000},  # expensive, low volume
            ]
        },
        # Scenario 10: Long history
        {
            "name": "Long History (90 days)",
            "products": [
                {"num_records": 15, "base_quantity": 12, "variance": 0.35, "days_back": 90, "unit_price": 28},
                {"num_records": 20, "base_quantity": 8, "variance": 0.4, "days_back": 90, "unit_price": 42},
            ]
        },
        # Scenario 11: Very short history
        {
            "name": "Very Short History (7 days)",
            "products": [
                {"num_records": 5, "base_quantity": 15, "variance": 0.25, "days_back": 7, "unit_price": 35},
                {"num_records": 7, "base_quantity": 20, "variance": 0.3, "days_back": 7, "unit_price": 25},
            ]
        },
        # Scenario 12: Many products (scale test)
        {
            "name": "Many Products (10 products)",
            "products": [
                {"num_records": random.randint(3, 15), "base_quantity": random.randint(5, 50), 
                 "variance": random.uniform(0.1, 0.6), "days_back": random.randint(20, 60), 
                 "unit_price": random.uniform(10, 100)}
                for _ in range(10)
            ]
        },
        
        # ====================================================================
        # NEW TEST SCENARIOS (10 additional patterns)
        # ====================================================================
        
        # Scenario 13: Exponential Growth (sales doubling weekly)
        {
            "name": "Exponential Growth",
            "products": [
                {"generator": "exponential", "base_quantity": 5, "growth_rate": 1.0, 
                 "num_records": 12, "days_back": 30, "unit_price": 40},
                {"generator": "exponential", "base_quantity": 10, "growth_rate": 0.7, 
                 "num_records": 15, "days_back": 45, "unit_price": 30},
            ]
        },
        # Scenario 14: Exponential Decay (sales halving weekly)
        {
            "name": "Exponential Decay",
            "products": [
                {"generator": "exponential", "base_quantity": 50, "growth_rate": -0.8, 
                 "num_records": 12, "days_back": 30, "unit_price": 35},
                {"generator": "exponential", "base_quantity": 30, "growth_rate": -1.0, 
                 "num_records": 10, "days_back": 40, "unit_price": 50},
            ]
        },
        # Scenario 15: Step Change Up (sudden 3x increase mid-period)
        {
            "name": "Step Change Up (3x)",
            "products": [
                {"generator": "step_change", "base_quantity": 10, "multiplier": 3.0, 
                 "change_day": 15, "num_records": 12, "days_back": 30, "unit_price": 25},
                {"generator": "step_change", "base_quantity": 8, "multiplier": 2.5, 
                 "change_day": 20, "num_records": 15, "days_back": 40, "unit_price": 45},
            ]
        },
        # Scenario 16: Step Change Down (sudden 70% drop mid-period)
        {
            "name": "Step Change Down (70% drop)",
            "products": [
                {"generator": "step_change", "base_quantity": 40, "multiplier": 0.3, 
                 "change_day": 15, "num_records": 12, "days_back": 30, "unit_price": 30},
                {"generator": "step_change", "base_quantity": 25, "multiplier": 0.4, 
                 "change_day": 10, "num_records": 10, "days_back": 25, "unit_price": 55},
            ]
        },
        # Scenario 17: Cyclical/Wave Pattern (weekly cycle)
        {
            "name": "Cyclical Wave Pattern",
            "products": [
                {"generator": "cyclical", "base_quantity": 20, "amplitude": 0.5, 
                 "period_days": 7, "num_records": 20, "days_back": 35, "unit_price": 28},
                {"generator": "cyclical", "base_quantity": 15, "amplitude": 0.6, 
                 "period_days": 10, "num_records": 18, "days_back": 40, "unit_price": 42},
            ]
        },
        # Scenario 18: Random Walk (pure noise, no trend)
        {
            "name": "Random Walk (No Pattern)",
            "products": [
                {"generator": "random_walk", "base_quantity": 20, "step_size": 0.3, 
                 "num_records": 15, "days_back": 30, "unit_price": 35},
                {"generator": "random_walk", "base_quantity": 30, "step_size": 0.25, 
                 "num_records": 12, "days_back": 35, "unit_price": 25},
            ]
        },
        # Scenario 19: Outlier Heavy (normal with extreme spikes)
        {
            "name": "Outlier Heavy Data",
            "products": [
                {"generator": "outlier", "base_quantity": 15, "outlier_multiplier": 5.0, 
                 "outlier_probability": 0.15, "num_records": 15, "days_back": 30, "unit_price": 40},
                {"generator": "outlier", "base_quantity": 10, "outlier_multiplier": 8.0, 
                 "outlier_probability": 0.1, "num_records": 12, "days_back": 35, "unit_price": 55},
            ]
        },
        # Scenario 20: Bi-modal Distribution (alternating high/low)
        {
            "name": "Bi-modal Distribution",
            "products": [
                {"generator": "bimodal", "low_quantity": 5, "high_quantity": 40, 
                 "high_probability": 0.3, "num_records": 15, "days_back": 30, "unit_price": 30},
                {"generator": "bimodal", "low_quantity": 8, "high_quantity": 50, 
                 "high_probability": 0.4, "num_records": 12, "days_back": 35, "unit_price": 45},
            ]
        },
        # Scenario 21: Burst Sales (clusters followed by silence)
        {
            "name": "Burst Sales Pattern",
            "products": [
                {"generator": "burst", "burst_quantity": 25, "burst_duration_days": 3, 
                 "silence_duration_days": 7, "num_bursts": 3, "days_back": 30, "unit_price": 35},
                {"generator": "burst", "burst_quantity": 15, "burst_duration_days": 5, 
                 "silence_duration_days": 10, "num_bursts": 2, "days_back": 30, "unit_price": 50},
            ]
        },
        # Scenario 22: Gradual Linear Ramp (steady increase)
        {
            "name": "Gradual Linear Ramp",
            "products": [
                {"generator": "linear_ramp", "start_quantity": 5, "end_quantity": 35, 
                 "num_records": 12, "days_back": 30, "unit_price": 28},
                {"generator": "linear_ramp", "start_quantity": 10, "end_quantity": 40, 
                 "num_records": 15, "days_back": 45, "unit_price": 38},
            ]
        },
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*100}")
        print(f"Testing: {scenario['name']}")
        print(f"{'='*100}")
        
        results = run_single_test(
            scenario['name'],
            scenario['products']
        )
        
        all_results.append(results)
        
        # Print results
        print(f"\n{'Product':<12} {'Records':<8} {'Historical':<10} {'Basic':<8} {'Advanced':<10} {'Super':<8} {'Deviation':<10}")
        print("-"*80)
        
        for p in results['products']:
            deviation_str = f"{p['super_vs_basic_pct']:+.1f}%"
            print(f"{p['product_id']:<12} {p['num_records']:<8} {p['historical_qty']:<10} "
                  f"{p['basic_qty']:<8} {p['advanced_qty']:<10} {p['super_qty']:<8} {deviation_str:<10}")
            
            all_deviations.append({
                "scenario": scenario['name'],
                "product_id": p['product_id'],
                "deviation_pct": p['super_vs_basic_pct'],
                "config": p['config']
            })
            
            # Log each result
            log_debug(f"Product forecast result", {
                "scenario": scenario['name'],
                "product_id": p['product_id'],
                "num_records": p['num_records'],
                "basic_qty": p['basic_qty'],
                "super_qty": p['super_qty'],
                "deviation_pct": p['super_vs_basic_pct'],
                "config_base_qty": p['config'].get('base_quantity'),
                "config_variance": p['config'].get('variance'),
                "config_trend": p['config'].get('trend', 0),
            })
    
    # Summary Statistics
    print(f"\n{'='*100}")
    print("OVERFITTING ANALYSIS SUMMARY")
    print(f"{'='*100}")
    
    deviations = [d['deviation_pct'] for d in all_deviations]
    
    print(f"\nTotal Products Tested: {len(deviations)}")
    print(f"Mean Deviation from Basic: {np.mean(deviations):+.1f}%")
    print(f"Std Deviation: {np.std(deviations):.1f}%")
    print(f"Min Deviation: {min(deviations):+.1f}%")
    print(f"Max Deviation: {max(deviations):+.1f}%")
    print(f"Median Deviation: {np.median(deviations):+.1f}%")
    
    # Check for systematic bias
    positive_deviations = [d for d in deviations if d > 0]
    negative_deviations = [d for d in deviations if d < 0]
    near_zero = [d for d in deviations if abs(d) <= 10]
    
    print(f"\nDeviation Distribution:")
    print(f"  Positive (Super > Basic): {len(positive_deviations)} ({len(positive_deviations)/len(deviations)*100:.1f}%)")
    print(f"  Negative (Super < Basic): {len(negative_deviations)} ({len(negative_deviations)/len(deviations)*100:.1f}%)")
    print(f"  Near Zero (±10%): {len(near_zero)} ({len(near_zero)/len(deviations)*100:.1f}%)")
    
    # Check for large deviations
    large_deviations = [d for d in all_deviations if abs(d['deviation_pct']) > 50]
    print(f"\nLarge Deviations (>50%): {len(large_deviations)}")
    
    if large_deviations:
        print("\n  Scenarios with large deviations:")
        for d in large_deviations:
            print(f"    {d['scenario']} - {d['product_id']}: {d['deviation_pct']:+.1f}%")
    
    # Log summary
    log_debug("Overfitting check summary", {
        "total_products": len(deviations),
        "mean_deviation": float(np.mean(deviations)),
        "std_deviation": float(np.std(deviations)),
        "min_deviation": float(min(deviations)),
        "max_deviation": float(max(deviations)),
        "positive_count": len(positive_deviations),
        "negative_count": len(negative_deviations),
        "near_zero_count": len(near_zero),
        "large_deviation_count": len(large_deviations)
    }, hypothesis_id="SUMMARY")
    
    # Overfitting Assessment
    print(f"\n{'='*100}")
    print("OVERFITTING ASSESSMENT")
    print(f"{'='*100}")
    
    # Criteria for detecting overfitting:
    # 1. Mean deviation should be near 0 (no systematic bias)
    # 2. Std deviation should be reasonable (not too high variance)
    # 3. Near-zero deviations should be common
    
    issues = []
    
    if abs(np.mean(deviations)) > 20:
        issues.append(f"Systematic bias detected: mean deviation = {np.mean(deviations):+.1f}%")
    
    if np.std(deviations) > 100:
        issues.append(f"High variance in predictions: std = {np.std(deviations):.1f}%")
    
    if len(near_zero) / len(deviations) < 0.3:
        issues.append(f"Low accuracy: only {len(near_zero)/len(deviations)*100:.1f}% within ±10%")
    
    if len(large_deviations) / len(deviations) > 0.3:
        issues.append(f"Too many large deviations: {len(large_deviations)/len(deviations)*100:.1f}%")
    
    if issues:
        print("\n⚠️  POTENTIAL OVERFITTING ISSUES:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n✓ No significant overfitting detected")
        print("  - Mean deviation near zero (no systematic bias)")
        print("  - Reasonable variance across scenarios")
        print("  - Good proportion of accurate predictions")
    
    return all_results, all_deviations


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    
    try:
        results, deviations = run_overfitting_tests()
        print(f"\n{'='*100}")
        print("Overfitting check complete!")
        print(f"{'='*100}\n")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
