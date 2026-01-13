"""
Procurement Workflow Visualization App

A Streamlit app that demonstrates the entire procurement workflow
from data fetching to RFQ generation, showing each step with
interactive data displays and visualizations.

Run with: streamlit run src/ui/workflow_app.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'guardrail_calculator.py'))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict

# Import all the modules
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher, mock_erp
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from internal_order_scheduler.basic_internal_order_scheduler import BasicInternalOrderScheduler
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from basic_guardrail_calculator import BasicGuardrailCalculator
from order_scheduler.basic_order_scheduler import BasicOrderScheduler
from web_scanner.mock_web_scanner import MockWebScanner
from rfq_generator.basic_rfq_generator import BasicRFQGenerator
from email_client.mock_email_client import MockEmailClient, clear_mock_email_storage
from email_listener.mock_email_listener import MockEmailListener
from reply_classifier.mock_reply_classifier import MockReplyClassifier
from auto_responder.basic_auto_responder import BasicAutoResponder
from quote_parser.basic_quote_parser import BasicQuoteParser
from quote_evaluator.basic_quote_evaluator import BasicQuoteEvaluator
from order_schedule_updater.basic_order_schedule_updater import BasicOrderScheduleUpdater

from models.inventory_data import InventoryData, InventoryItem, ItemType
from models.classification_result import ReplyType
from models.pending_clarification import PendingClarification, ClarificationPriority


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Procurement Workflow",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .step-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        color: white;
    }
    .step-number {
        font-size: 14px;
        opacity: 0.8;
    }
    .step-title {
        font-size: 22px;
        font-weight: 600;
        margin: 0;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2d5a87;
    }
    .supplier-card {
        background: #1a1a2e;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #00d4aa;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .supplier-card h4 {
        color: #00d4aa !important;
        margin: 0 0 12px 0 !important;
        font-size: 18px !important;
    }
    .supplier-card p {
        color: #e0e0e0 !important;
        margin: 6px 0 !important;
        font-size: 14px !important;
    }
    .supplier-card strong {
        color: #ffffff !important;
    }
    .supplier-card .supplier-id {
        color: #888 !important;
        font-size: 12px !important;
    }
    .supplier-card .price {
        color: #4ade80 !important;
        font-weight: bold !important;
    }
    .supplier-card .rating {
        color: #fbbf24 !important;
    }
    .rfq-card {
        background: #fff3cd;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .email-card {
        background: #2d3748;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 4px solid #4299e1;
    }
    .email-card p {
        color: #e2e8f0 !important;
        margin: 4px 0 !important;
    }
    .quote-card {
        background: #1a472a;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 4px solid #48bb78;
    }
    .quote-card p {
        color: #c6f6d5 !important;
        margin: 4px 0 !important;
    }
    .clarification-card {
        background: #744210;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 4px solid #ed8936;
    }
    .clarification-card p {
        color: #feebc8 !important;
        margin: 4px 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def step_header(step_num: int, title: str, icon: str = ""):
    """Render a styled step header."""
    st.markdown(f"""
    <div class="step-header">
        <div class="step-number">STEP {step_num}</div>
        <div class="step-title">{icon} {title}</div>
    </div>
    """, unsafe_allow_html=True)


def dataframe_from_items(items, columns_map: dict) -> pd.DataFrame:
    """Convert a list of dataclass items to a DataFrame."""
    data = []
    for item in items:
        row = {}
        for col_name, attr in columns_map.items():
            if callable(attr):
                row[col_name] = attr(item)
            else:
                row[col_name] = getattr(item, attr, None)
        data.append(row)
    return pd.DataFrame(data)


def plot_forecast_chart(forecasts, title: str, id_attr: str, name_attr: str, qty_attr: str):
    """Create a bar chart for forecast data."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    names = [getattr(f, name_attr) for f in forecasts]
    quantities = [getattr(f, qty_attr) for f in forecasts]
    ids = [getattr(f, id_attr) for f in forecasts]
    
    colors = plt.cm.Set2(range(len(names)))
    bars = ax.bar(names, quantities, color=colors, edgecolor='white', linewidth=1.5)
    
    # Add value labels on bars
    for bar, qty, item_id in zip(bars, quantities, ids):
        height = bar.get_height()
        ax.annotate(f'{qty:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Forecasted Quantity', fontsize=11)
    ax.set_xlabel('', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    return fig


def plot_forecast_timeline(forecasts, title: str, id_attr: str, name_attr: str, qty_attr: str, period_days: int = 30):
    """Create a line chart showing daily demand projection."""
    fig, ax = plt.subplots(figsize=(12, 5))
    
    colors = plt.cm.Set2(range(len(forecasts)))
    
    start_date = datetime.now()
    dates = [start_date + timedelta(days=i) for i in range(period_days)]
    
    for i, f in enumerate(forecasts):
        name = getattr(f, name_attr)
        total_qty = getattr(f, qty_attr)
        daily_qty = total_qty / period_days
        
        # Cumulative projection
        cumulative = [daily_qty * (d + 1) for d in range(period_days)]
        ax.plot(dates, cumulative, label=name, color=colors[i], linewidth=2, marker='o', markersize=3)
    
    ax.set_ylabel('Cumulative Quantity', fontsize=11)
    ax.set_xlabel('Date', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left', framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Title
    st.title("📦 Procurement Workflow Visualization")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        forecast_days = st.slider("Forecast Period (days)", 7, 90, 30)
        schedule_days = st.slider("Order Schedule (days)", 7, 60, 30)
        
        st.markdown("---")
        st.header("📊 Workflow Summary")
        
        if st.button("🔄 Run Full Workflow", type="primary", width='stretch'):
            st.session_state.run_workflow = True
        
        st.markdown("---")
        st.markdown("### Legend")
        st.markdown("📥 Data Fetching")
        st.markdown("📈 Forecasting")
        st.markdown("🔧 Calculations")
        st.markdown("🌐 External Search")
        st.markdown("📧 Communication")
    
    # Initialize workflow state
    if 'run_workflow' not in st.session_state:
        st.session_state.run_workflow = True
    
    # Run the workflow
    if st.session_state.run_workflow:
        run_workflow(forecast_days, schedule_days)


def run_workflow(forecast_days: int, schedule_days: int):
    """Execute and display the full procurement workflow."""
    
    # Clear email storage for fresh run
    clear_mock_email_storage()
    
    # Initialize fetchers
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    # ========================================================================
    # STEP 1: FETCH ERP DATA
    # ========================================================================
    step_header(1, "Fetch ERP Data", "📥")
    
    with st.spinner("Fetching data from ERP system..."):
        inventory_data = erp_fetcher.fetch_inventory_data()
        delivery_history = erp_fetcher.fetch_delivery_history()
        sales_data = erp_fetcher.fetch_sales_data()
        bom_data = erp_fetcher.fetch_bom_data()
        erp_blanket_pos = erp_fetcher.fetch_blanket_pos()
        materials_lookup = erp_fetcher.get_materials_lookup()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Inventory Items", len(inventory_data.items))
    col2.metric("Deliveries", len(delivery_history.records))
    col3.metric("Sales Records", len(sales_data.records))
    col4.metric("BOM Items", len(bom_data.items))
    col5.metric("Blanket POs", len(erp_blanket_pos.blanket_pos))
    
    with st.expander("📦 Inventory Data", expanded=False):
        df = dataframe_from_items(inventory_data.items, {
            "Item ID": "item_id",
            "Name": "item_name",
            "Quantity": "quantity",
            "Unit Price": "unit_price",
            "Location": "location",
            "Supplier ID": "supplier_id",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    with st.expander("🚚 Delivery History", expanded=False):
        df = dataframe_from_items(delivery_history.records, {
            "Delivery ID": "delivery_id",
            "Supplier": "supplier_name",
            "Product": "product_name",
            "Quantity": "quantity",
            "Status": lambda x: x.status.value,
            "Delivery Date": lambda x: x.delivery_date.strftime("%Y-%m-%d"),
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    with st.expander("💰 Sales Data", expanded=False):
        df = dataframe_from_items(sales_data.records, {
            "Date": lambda x: x.timestamp.strftime("%Y-%m-%d"),
            "Product ID": "product_id",
            "Product Name": "product_name",
            "Quantity": "quantity_sold",
            "Unit Price": "unit_price",
            "Revenue": "total_revenue",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    with st.expander("🔩 Bill of Materials (BOM)", expanded=False):
        df = dataframe_from_items(bom_data.items, {
            "Product ID": "product_id",
            "Material ID": "material_id",
            "Qty Required": "quantity_required",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    with st.expander("📋 ERP Blanket POs", expanded=False):
        df = dataframe_from_items(erp_blanket_pos.blanket_pos, {
            "BPO ID": "blanket_po_id",
            "Supplier": "supplier_name",
            "Product": "product_name",
            "Total Qty": "total_quantity",
            "Remaining": "remaining_quantity",
            "Unit Price": "unit_price",
            "Status": lambda x: x.status.value,
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ ERP data fetched successfully!")
    
    # ========================================================================
    # STEP 2: FETCH CRM DATA
    # ========================================================================
    step_header(2, "Fetch CRM Data", "📥")
    
    with st.spinner("Fetching data from CRM system..."):
        crm_blanket_pos = crm_fetcher.fetch_blanket_pos()
        approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    
    col1, col2 = st.columns(2)
    col1.metric("CRM Blanket POs", len(crm_blanket_pos.blanket_pos))
    col2.metric("Approved Suppliers", len(approved_suppliers.suppliers))
    
    with st.expander("📋 CRM Blanket POs", expanded=False):
        df = dataframe_from_items(crm_blanket_pos.blanket_pos, {
            "BPO ID": "blanket_po_id",
            "Supplier": "supplier_name",
            "Product": "product_name",
            "Total Qty": "total_quantity",
            "Remaining": "remaining_quantity",
            "Unit Price": "unit_price",
            "Status": lambda x: x.status.value,
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    with st.expander("✅ Approved Suppliers", expanded=False):
        df = dataframe_from_items(approved_suppliers.suppliers, {
            "Supplier ID": "supplier_id",
            "Name": "supplier_name",
            "Email": "contact_email",
            "Phone": "contact_phone",
            "Status": lambda x: x.status.value,
            "Rating": "rating",
            "Categories": lambda x: ", ".join(x.categories),
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ CRM data fetched successfully!")
    
    # ========================================================================
    # STEP 3: GENERATE SALES FORECAST
    # ========================================================================
    step_header(3, "Generate Sales Forecast", "📈")
    
    with st.spinner("Generating sales forecast..."):
        sales_forecaster = BasicSalesForecaster()
        sales_forecast = sales_forecaster.forecast_sales(inventory_data, sales_data, forecast_days)
    
    col1, col2, col3 = st.columns(3)
    total_forecasted = sum(f.forecasted_quantity for f in sales_forecast.forecasts)
    total_revenue = sum(f.forecasted_revenue or 0 for f in sales_forecast.forecasts)
    col1.metric("Products Forecasted", len(sales_forecast.forecasts))
    col2.metric("Total Units", f"{total_forecasted:,}")
    col3.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    # Sales forecast chart
    st.subheader("📊 Sales Forecast by Product")
    fig = plot_forecast_chart(
        sales_forecast.forecasts,
        f"Forecasted Sales ({forecast_days} days)",
        "item_id", "item_name", "forecasted_quantity"
    )
    st.pyplot(fig)
    plt.close()
    
    # Timeline chart
    st.subheader("📈 Cumulative Sales Projection")
    fig = plot_forecast_timeline(
        sales_forecast.forecasts,
        f"Cumulative Sales Over {forecast_days} Days",
        "item_id", "item_name", "forecasted_quantity", forecast_days
    )
    st.pyplot(fig)
    plt.close()
    
    with st.expander("📋 Forecast Details", expanded=False):
        df = dataframe_from_items(sales_forecast.forecasts, {
            "Product ID": "item_id",
            "Name": "item_name",
            "Forecasted Qty": "forecasted_quantity",
            "Revenue": lambda x: f"${x.forecasted_revenue:,.2f}" if x.forecasted_revenue else "N/A",
            "Confidence": lambda x: f"{x.confidence_level * 100:.0f}%" if x.confidence_level else "N/A",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ Sales forecast generated!")
    
    # ========================================================================
    # STEP 4: SCHEDULE INTERNAL ORDERS (PRODUCTION)
    # ========================================================================
    step_header(4, "Schedule Internal Orders (Production)", "🏭")
    
    with st.spinner("Scheduling internal production orders..."):
        # Filter inventory to get only products (not materials)
        product_inventory = InventoryData(
            items=[item for item in inventory_data.items if item.item_type == ItemType.PRODUCT],
            fetched_at=inventory_data.fetched_at,
        )
        
        # Get production info from mock ERP
        production_info = mock_erp.product_production_store
        
        # Schedule internal orders
        internal_scheduler = BasicInternalOrderScheduler()
        internal_schedule = internal_scheduler.schedule_internal_orders(
            sales_forecast, product_inventory, production_info, num_days=schedule_days
        )
    
    col1, col2, col3 = st.columns(3)
    total_production_qty = sum(o.quantity for o in internal_schedule.orders)
    col1.metric("Production Orders", len(internal_schedule.orders))
    col2.metric("Total Units to Produce", f"{total_production_qty:,}")
    col3.metric("Schedule Period", f"{schedule_days} days")
    
    # Internal orders chart
    if internal_schedule.orders:
        st.subheader("📊 Production Orders by Product")
        # Group orders by product
        orders_by_product = defaultdict(int)
        for order in internal_schedule.orders:
            orders_by_product[order.product_name] += order.quantity
        
        fig, ax = plt.subplots(figsize=(10, 5))
        products = list(orders_by_product.keys())
        quantities = list(orders_by_product.values())
        colors = plt.cm.Set3(range(len(products)))
        bars = ax.bar(products, quantities, color=colors, edgecolor='white', linewidth=1.5)
        
        # Add value labels
        for bar, qty in zip(bars, quantities):
            height = bar.get_height()
            ax.annotate(f'{qty:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')
        
        ax.set_ylabel('Production Quantity', fontsize=11)
        ax.set_xlabel('', fontsize=11)
        ax.set_title(f"Production Orders Scheduled ({schedule_days} days)", fontsize=14, fontweight='bold', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='x', rotation=15)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with st.expander("📋 Internal Order Schedule Details", expanded=True):
        if internal_schedule.orders:
            df = dataframe_from_items(internal_schedule.orders, {
                "Product ID": "product_id",
                "Product Name": "product_name",
                "Quantity": "quantity",
                "Start Date": lambda x: x.start_date.strftime("%Y-%m-%d"),
                "Completion Date": lambda x: x.completion_date.strftime("%Y-%m-%d"),
                "Status": lambda x: x.status.value,
            })
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No internal orders scheduled - product inventory is sufficient.")
    
    st.success("✅ Internal orders scheduled!")
    
    # ========================================================================
    # STEP 5: GENERATE MATERIALS FORECAST FROM INTERNAL ORDERS
    # ========================================================================
    step_header(5, "Generate Materials Forecast", "📈")
    
    with st.spinner("Generating materials forecast from production schedule..."):
        materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
        materials_forecast = materials_forecaster.forecast_materials_from_internal_orders(
            internal_schedule, bom_data, forecast_days
        )
    
    col1, col2 = st.columns(2)
    total_materials = sum(f.forecasted_quantity for f in materials_forecast.forecasts)
    col1.metric("Materials Forecasted", len(materials_forecast.forecasts))
    col2.metric("Total Units Needed", f"{total_materials:,.0f}")
    
    # Materials forecast chart
    st.subheader("📊 Materials Forecast by Material")
    fig = plot_forecast_chart(
        materials_forecast.forecasts,
        f"Forecasted Material Requirements ({forecast_days} days)",
        "material_id", "material_name", "forecasted_quantity"
    )
    st.pyplot(fig)
    plt.close()
    
    # Timeline chart
    st.subheader("📈 Cumulative Materials Projection")
    fig = plot_forecast_timeline(
        materials_forecast.forecasts,
        f"Cumulative Material Demand Over {forecast_days} Days",
        "material_id", "material_name", "forecasted_quantity", forecast_days
    )
    st.pyplot(fig)
    plt.close()
    
    with st.expander("📋 Materials Forecast Details", expanded=False):
        df = dataframe_from_items(materials_forecast.forecasts, {
            "Material ID": "material_id",
            "Name": "material_name",
            "Forecasted Qty": lambda x: f"{x.forecasted_quantity:,.1f}",
            "Daily Demand": lambda x: f"{x.forecasted_quantity / forecast_days:,.2f}",
            "Confidence": lambda x: f"{x.confidence_level * 100:.0f}%" if x.confidence_level else "N/A",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ Materials forecast generated!")
    
    # ========================================================================
    # STEP 6: CALCULATE SUPPLIER STATE
    # ========================================================================
    step_header(6, "Calculate Supplier State", "🔧")
    
    with st.spinner("Calculating supplier states..."):
        supplier_calculator = BasicSupplierStateCalculator()
        supplier_state_store = supplier_calculator.calculate_supplier_state(
            delivery_history, approved_suppliers, crm_blanket_pos
        )
    
    col1, col2 = st.columns(2)
    col1.metric("Supplier-Product States", len(supplier_state_store.states))
    avg_success = sum(s.success_rate for s in supplier_state_store.states) / len(supplier_state_store.states)
    col2.metric("Avg Success Rate", f"{avg_success:.1f}%")
    
    with st.expander("📊 Supplier States", expanded=False):
        df = dataframe_from_items(supplier_state_store.states, {
            "Supplier ID": "supplier_id",
            "Supplier": "supplier_name",
            "Product ID": "product_id",
            "Product": "product_name",
            "Deliveries": "total_deliveries",
            "Successful": "successful_deliveries",
            "Success Rate": lambda x: f"{x.success_rate:.0f}%",
            "Avg Lead Time": lambda x: f"{x.average_lead_time_days:.0f} days" if x.average_lead_time_days else "N/A",
            "Active BPOs": "active_blanket_pos_count",
            "Status": lambda x: x.supplier_status.value,
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ Supplier states calculated!")
    
    # ========================================================================
    # STEP 7: CALCULATE GUARDRAILS
    # ========================================================================
    step_header(7, "Calculate Inventory Guardrails", "🔧")
    
    with st.spinner("Calculating guardrails..."):
        guardrail_calculator = BasicGuardrailCalculator()
        guardrails = guardrail_calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Materials", len(guardrails.items))
    avg_rop = sum(g.reorder_point for g in guardrails.items) / len(guardrails.items)
    avg_ss = sum(g.safety_stock for g in guardrails.items) / len(guardrails.items)
    avg_eoq = sum(g.eoq for g in guardrails.items) / len(guardrails.items)
    col2.metric("Avg Reorder Point", f"{avg_rop:,.0f}")
    col3.metric("Avg Safety Stock", f"{avg_ss:,.0f}")
    col4.metric("Avg EOQ", f"{avg_eoq:,.0f}")
    
    with st.expander("📋 Guardrails by Material", expanded=True):
        df = dataframe_from_items(guardrails.items, {
            "Material ID": "material_id",
            "Name": "material_name",
            "Reorder Point": "reorder_point",
            "Safety Stock": "safety_stock",
            "EOQ": "eoq",
            "Max Stock": "maximum_stock",
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    # Guardrails visualization
    st.subheader("📊 Guardrails Comparison")
    fig, ax = plt.subplots(figsize=(12, 5))
    
    materials = [g.material_name for g in guardrails.items]
    x = range(len(materials))
    width = 0.2
    
    rop = [g.reorder_point for g in guardrails.items]
    ss = [g.safety_stock for g in guardrails.items]
    eoq = [g.eoq for g in guardrails.items]
    max_stock = [g.maximum_stock for g in guardrails.items]
    
    ax.bar([i - 1.5*width for i in x], ss, width, label='Safety Stock', color='#ff9999')
    ax.bar([i - 0.5*width for i in x], rop, width, label='Reorder Point', color='#66b3ff')
    ax.bar([i + 0.5*width for i in x], eoq, width, label='EOQ', color='#99ff99')
    ax.bar([i + 1.5*width for i in x], max_stock, width, label='Max Stock', color='#ffcc99')
    
    ax.set_ylabel('Quantity')
    ax.set_xticks(x)
    ax.set_xticklabels(materials, rotation=15)
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    st.success("✅ Guardrails calculated!")
    
    # ========================================================================
    # STEP 8: SCHEDULE EXTERNAL ORDERS
    # ========================================================================
    step_header(8, "Schedule External Orders", "📅")
    
    # Create material inventory for scheduling (low quantities to trigger orders)
    now = datetime.now()
    material_inventory = InventoryData(
        items=[
            InventoryItem(
                item_id=m_id,
                item_name=m_name,
                item_type=ItemType.MATERIAL,
                quantity=10,  # Low quantity to trigger orders
                unit_price=5.0,
                location="Warehouse-1",
                last_updated=now,
                supplier_id="SUP-001",
            )
            for m_id, m_name in materials_lookup.items()
        ],
        fetched_at=now,
    )
    
    with st.spinner("Generating order schedule..."):
        order_scheduler = BasicOrderScheduler()
        order_schedule = order_scheduler.schedule_orders(
            material_inventory, materials_forecast, supplier_state_store, guardrails, schedule_days
        )
    
    col1, col2 = st.columns(2)
    col1.metric("Orders Scheduled", len(order_schedule.orders))
    col2.metric("Projection Days", len(order_schedule.projected_levels) // len(materials_lookup) if materials_lookup else 0)
    
    with st.expander("📦 Order Schedule", expanded=True):
        if order_schedule.orders:
            df = dataframe_from_items(order_schedule.orders, {
                "Material ID": "material_id",
                "Material": "material_name",
                "Supplier": "supplier_name",
                "Order Date": lambda x: x.order_date.strftime("%Y-%m-%d"),
                "Delivery Date": lambda x: x.expected_delivery_date.strftime("%Y-%m-%d"),
                "Quantity": "order_quantity",
                "Status": lambda x: x.order_status.value,
            })
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No orders scheduled - inventory levels are sufficient.")
    
    with st.expander("📈 Projected Inventory Levels", expanded=False):
        if order_schedule.projected_levels:
            df = dataframe_from_items(order_schedule.projected_levels[:50], {  # Show first 50
                "Material ID": "material_id",
                "Date": lambda x: x.date.strftime("%Y-%m-%d"),
                "Projected Qty": "projected_quantity",
                "Below Reorder": lambda x: "⚠️ Yes" if x.is_below_reorder_point else "No",
                "Above Max": lambda x: "⚠️ Yes" if x.is_above_maximum_stock else "No",
            })
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No projected levels generated.")
    
    st.success("✅ Orders scheduled!")
    
    # ========================================================================
    # STEP 9: WEB SEARCH FOR SUPPLIERS
    # ========================================================================
    step_header(9, "Web Search for Suppliers", "🌐")
    
    with st.spinner("Searching for suppliers online..."):
        web_scanner = MockWebScanner()
        material_ids = list(materials_lookup.keys())
        material_names = list(materials_lookup.values())
        supplier_search_results = web_scanner.search_suppliers(material_ids, material_names)
    
    st.metric("Suppliers Found", len(supplier_search_results.results))
    
    st.subheader("🔍 Supplier Search Results")
    
    # Display suppliers as styled cards
    cols = st.columns(3)
    for i, supplier in enumerate(supplier_search_results.results):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="supplier-card">
                <h4>{supplier.name}</h4>
                <p class="supplier-id">ID: {supplier.supplier_id}</p>
                <p>📧 <strong>Email:</strong> {supplier.contact_email}</p>
                <p>🌐 <strong>Website:</strong> {supplier.website}</p>
                <p class="price">💰 ${supplier.estimated_price_range[0]:.2f} - ${supplier.estimated_price_range[1]:.2f} per unit</p>
                <p>⏱️ <strong>Lead Time:</strong> {supplier.estimated_lead_time_days} days</p>
                <p class="rating">⭐ <strong>Rating:</strong> {supplier.rating or 'N/A'}/5.0</p>
                <p>📜 <strong>Certs:</strong> {', '.join(supplier.certifications[:2])}</p>
                <p>🏭 <strong>Materials:</strong> {', '.join(supplier.materials_offered[:2])}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander("📋 Full Supplier Details Table", expanded=False):
        df = dataframe_from_items(supplier_search_results.results, {
            "Supplier ID": "supplier_id",
            "Name": "name",
            "Email": "contact_email",
            "Website": "website",
            "Price Range": lambda x: f"${x.estimated_price_range[0]:.2f} - ${x.estimated_price_range[1]:.2f}",
            "Lead Time": lambda x: f"{x.estimated_lead_time_days} days",
            "Rating": "rating",
            "Certifications": lambda x: ", ".join(x.certifications),
            "Materials": lambda x: ", ".join(x.materials_offered),
        })
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ Supplier search complete!")
    
    # ========================================================================
    # STEP 10: GENERATE RFQS
    # ========================================================================
    step_header(10, "Generate RFQs", "📝")
    
    with st.spinner("Generating RFQs..."):
        rfq_generator = BasicRFQGenerator()
        rfq_store = rfq_generator.generate_rfqs(order_schedule, crm_blanket_pos, supplier_search_results)
    
    st.metric("RFQs Generated", len(rfq_store.rfqs))
    
    if rfq_store.rfqs:
        with st.expander("📋 RFQ Store", expanded=True):
            df = dataframe_from_items(rfq_store.rfqs, {
                "RFQ ID": "rfq_id",
                "Material": "material_name",
                "Supplier": "supplier_name",
                "Email": "supplier_email",
                "Quantity": "quantity",
                "Delivery Date": lambda x: x.required_delivery_date.strftime("%Y-%m-%d"),
                "Status": lambda x: x.status.value,
                "Valid Until": lambda x: x.valid_until.strftime("%Y-%m-%d") if x.valid_until else "N/A",
            })
            st.dataframe(df, width='stretch', hide_index=True)
        
        st.success("✅ RFQs generated!")
    else:
        st.info("No RFQs generated - no orders in schedule or no matching suppliers.")
        return
    
    # ========================================================================
    # STEP 11: SEND RFQS
    # ========================================================================
    step_header(11, "Send RFQs via Email", "📧")
    
    with st.spinner("Sending RFQs via email..."):
        email_client = MockEmailClient()
        sent_emails = email_client.send_rfqs(rfq_store, "procurement@company.mock")
    
    st.metric("Emails Sent", len(sent_emails))
    
    # Build mapping from email_id to rfq_id from sent emails (used later)
    email_to_rfq: dict[str, str] = {}
    for email in sent_emails:
        if email.rfq_id:
            email_to_rfq[email.email_id] = email.rfq_id
    
    # Display sent emails
    st.subheader("📤 Sent Emails")
    for email in sent_emails[:5]:  # Show first 5
        st.markdown(f"""
        <div class="email-card">
            <p><strong>📧 Email ID:</strong> {email.email_id}</p>
            <p><strong>To:</strong> {email.to_address}</p>
            <p><strong>Subject:</strong> {email.subject}</p>
            <p><strong>Status:</strong> {email.status.value}</p>
            <p><strong>RFQ Ref:</strong> {email.rfq_id}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if len(sent_emails) > 5:
        st.info(f"... and {len(sent_emails) - 5} more emails")
    
    st.success("✅ RFQs sent!")
    
    # ========================================================================
    # STEP 12: LISTEN FOR REPLIES
    # ========================================================================
    step_header(12, "Listen for Email Replies", "📬")
    
    with st.spinner("Checking for replies..."):
        email_listener = MockEmailListener()
        replies = email_listener.get_replies()
    
    st.metric("Replies Received", len(replies))
    
    if replies:
        with st.expander("📩 Received Replies", expanded=True):
            # Build a display function that looks up rfq_id
            reply_data = []
            for reply in replies[:10]:
                rfq_id = email_to_rfq.get(reply.original_email_id, "N/A")
                reply_data.append({
                    "Reply ID": reply.reply_id,
                    "From": reply.from_address,
                    "Subject": reply.subject,
                    "RFQ Ref": rfq_id,
                    "Received": reply.received_at.strftime("%Y-%m-%d %H:%M") if reply.received_at else "N/A",
                })
            df = pd.DataFrame(reply_data)
            st.dataframe(df, width='stretch', hide_index=True)
        
        st.success("✅ Replies received!")
    else:
        st.info("No replies received yet.")
        return
    
    # ========================================================================
    # STEP 13: CLASSIFY REPLIES
    # ========================================================================
    step_header(13, "Classify Replies", "🏷️")
    
    with st.spinner("Classifying replies..."):
        reply_classifier = MockReplyClassifier()
        classifications = []
        
        for reply in replies:
            # Look up rfq_id via original email
            rfq_id = email_to_rfq.get(reply.original_email_id)
            classification = reply_classifier.classify(reply)
            classifications.append((reply, rfq_id, classification))
    
    # Count by type
    quote_count = sum(1 for _, _, c in classifications if c.reply_type == ReplyType.QUOTE)
    simple_clarification = sum(1 for _, _, c in classifications if c.reply_type == ReplyType.CLARIFICATION_SIMPLE)
    complex_clarification = sum(1 for _, _, c in classifications if c.reply_type == ReplyType.CLARIFICATION_COMPLEX)
    other_count = len(classifications) - quote_count - simple_clarification - complex_clarification
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Quotes", quote_count)
    col2.metric("❓ Simple Questions", simple_clarification)
    col3.metric("🤔 Complex Questions", complex_clarification)
    col4.metric("📋 Other", other_count)
    
    with st.expander("🏷️ Classification Results", expanded=True):
        data = []
        for reply, rfq_id, classification in classifications:
            data.append({
                "Reply From": reply.from_address,
                "RFQ ID": rfq_id or "N/A",
                "Type": classification.reply_type.value,
                "Confidence": f"{classification.confidence * 100:.0f}%",
                "Reasoning": classification.reasoning[:50] + "..." if len(classification.reasoning) > 50 else classification.reasoning,
            })
        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)
    
    st.success("✅ Replies classified!")
    
    # ========================================================================
    # STEP 14: AUTO-RESPOND & QUEUE FOR HUMAN
    # ========================================================================
    step_header(14, "Auto-Respond & Queue for Human Review", "🤖")
    
    with st.spinner("Processing clarification requests..."):
        auto_responder = BasicAutoResponder()
        auto_responses = []
        human_queue = []
        
        for reply, rfq_id, classification in classifications:
            if classification.reply_type == ReplyType.CLARIFICATION_SIMPLE:
                # Auto-respond
                rfq = rfq_store.rfqs_by_id.get(rfq_id) if rfq_id else None
                if rfq:
                    response = auto_responder.respond(reply, rfq, "procurement@company.mock")
                    auto_responses.append((reply, response))
            elif classification.reply_type == ReplyType.CLARIFICATION_COMPLEX:
                # Queue for human
                clarification = PendingClarification(
                    clarification_id=f"CLR-{reply.reply_id}",
                    original_email_id=reply.reply_id,
                    rfq_id=rfq_id or "",
                    supplier_id=reply.from_address.split("@")[0],
                    supplier_name=reply.from_address,
                    supplier_email=reply.from_address,
                    question_text=reply.body[:200] if reply.body else "N/A",
                    priority=ClarificationPriority.MEDIUM,
                    created_at=datetime.now(),
                )
                human_queue.append(clarification)
    
    col1, col2 = st.columns(2)
    col1.metric("🤖 Auto-Responses Sent", len(auto_responses))
    col2.metric("👤 Queued for Human", len(human_queue))
    
    if auto_responses:
        st.subheader("🤖 Auto-Responses")
        for reply, response in auto_responses[:3]:
            st.markdown(f"""
            <div class="email-card">
                <p><strong>Original From:</strong> {reply.from_address}</p>
                <p><strong>Response To:</strong> {response.to_address}</p>
                <p><strong>Subject:</strong> {response.subject}</p>
            </div>
            """, unsafe_allow_html=True)
    
    if human_queue:
        st.subheader("👤 Human Review Queue")
        for clarification in human_queue[:3]:
            st.markdown(f"""
            <div class="clarification-card">
                <p><strong>ID:</strong> {clarification.clarification_id}</p>
                <p><strong>From:</strong> {clarification.supplier_email}</p>
                <p><strong>Priority:</strong> {clarification.priority.value}</p>
                <p><strong>Question:</strong> {clarification.question_text[:100]}...</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.success("✅ Clarifications processed!")
    
    # ========================================================================
    # STEP 15: EXTRACT QUOTES
    # ========================================================================
    step_header(15, "Extract & Parse Quotes", "💰")
    
    with st.spinner("Extracting quotes from replies..."):
        quote_parser = BasicQuoteParser()
        quotes = []
        
        for reply, rfq_id, classification in classifications:
            if classification.reply_type == ReplyType.QUOTE:
                rfq = rfq_store.rfqs_by_id.get(rfq_id) if rfq_id else None
                if rfq:
                    quote = quote_parser.parse(reply, rfq)
                    quotes.append(quote)
    
    st.metric("Quotes Extracted", len(quotes))
    
    if quotes:
        st.subheader("💰 Extracted Quotes")
        for quote in quotes[:5]:
            st.markdown(f"""
            <div class="quote-card">
                <p><strong>Quote ID:</strong> {quote.quote_id}</p>
                <p><strong>Supplier:</strong> {quote.supplier_name}</p>
                <p><strong>Material:</strong> {quote.material_name}</p>
                <p><strong>Unit Price:</strong> ${quote.unit_price:.2f}</p>
                <p><strong>Quantity:</strong> {quote.quantity:,}</p>
                <p><strong>Total:</strong> ${quote.total_price:.2f}</p>
                <p><strong>Lead Time:</strong> {quote.lead_time_days} days</p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("📋 All Quotes Table", expanded=False):
            df = dataframe_from_items(quotes, {
                "Quote ID": "quote_id",
                "Supplier": "supplier_name",
                "Material": "material_name",
                "Unit Price": lambda x: f"${x.unit_price:.2f}",
                "Quantity": "quantity",
                "Total": lambda x: f"${x.total_price:.2f}",
                "Lead Time": lambda x: f"{x.lead_time_days} days",
                "Status": lambda x: x.status.value,
            })
            st.dataframe(df, width='stretch', hide_index=True)
        
        st.success("✅ Quotes extracted!")
    else:
        st.info("No quotes to extract.")
        return
    
    # ========================================================================
    # STEP 16: EVALUATE QUOTES
    # ========================================================================
    step_header(16, "Evaluate Quotes", "⚖️")
    
    with st.spinner("Evaluating quotes against current orders..."):
        quote_evaluator = BasicQuoteEvaluator()
        evaluations = []
        
        for quote in quotes:
            # Find matching order in schedule
            matching_orders = order_schedule.orders_by_material.get(quote.material_id, [])
            if matching_orders:
                current_order = matching_orders[0]
                # Get current price and lead time from order metadata or use defaults
                current_unit_price = float(current_order.metadata.get("unit_price", 10.0))
                current_lead_time = int(current_order.metadata.get("lead_time_days", 14))
                evaluation = quote_evaluator.evaluate(
                    quote, supplier_state_store, current_unit_price, current_lead_time
                )
                evaluations.append((quote, evaluation))
    
    st.metric("Evaluations Completed", len(evaluations))
    
    if evaluations:
        # Count recommendations based on is_better_than_current and recommendation text
        accept_count = sum(1 for _, e in evaluations if e.is_better_than_current)
        reject_count = sum(1 for _, e in evaluations if "NOT RECOMMENDED" in e.recommendation)
        review_count = len(evaluations) - accept_count - reject_count
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Better Than Current", accept_count)
        col2.metric("❌ Not Recommended", reject_count)
        col3.metric("🔍 Comparable", review_count)
        
        with st.expander("⚖️ Evaluation Results", expanded=True):
            data = []
            for quote, evaluation in evaluations:
                data.append({
                    "Quote ID": quote.quote_id,
                    "Supplier": quote.supplier_name,
                    "Material": quote.material_name,
                    "Overall Score": f"{evaluation.overall_score:.1f}",
                    "Price Score": f"{evaluation.price_score:.1f}",
                    "Lead Time Score": f"{evaluation.lead_time_score:.1f}",
                    "Reliability Score": f"{evaluation.reliability_score:.1f}",
                    "Better?": "✅ Yes" if evaluation.is_better_than_current else "❌ No",
                    "Recommendation": evaluation.recommendation,
                })
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch', hide_index=True)
        
        st.success("✅ Quotes evaluated!")
    else:
        st.info("No evaluations to perform.")
    
    # ========================================================================
    # STEP 17: UPDATE ORDER SCHEDULE
    # ========================================================================
    step_header(17, "Update Order Schedule", "📝")
    
    with st.spinner("Updating order schedule with accepted quotes..."):
        schedule_updater = BasicOrderScheduleUpdater()
        
        # Get quotes that are better than current suppliers
        accepted_pairs = [(q, e) for q, e in evaluations if e.is_better_than_current]
        
        if accepted_pairs:
            # Apply each accepted quote to update the schedule
            updated_schedule = order_schedule
            updates_made = 0
            
            for quote, evaluation in accepted_pairs:
                new_schedule = schedule_updater.update_if_better(updated_schedule, quote, evaluation)
                if new_schedule != updated_schedule:
                    updated_schedule = new_schedule
                    updates_made += 1
            
            st.metric("Orders Updated", updates_made)
            
            with st.expander("📋 Updated Order Schedule", expanded=True):
                df = dataframe_from_items(updated_schedule.orders, {
                    "Material ID": "material_id",
                    "Material": "material_name",
                    "Supplier": "supplier_name",
                    "Order Date": lambda x: x.order_date.strftime("%Y-%m-%d"),
                    "Delivery Date": lambda x: x.expected_delivery_date.strftime("%Y-%m-%d"),
                    "Quantity": "order_quantity",
                    "Status": lambda x: x.order_status.value,
                })
                st.dataframe(df, width='stretch', hide_index=True)
            
            st.success("✅ Order schedule updated!")
        else:
            st.info("No quotes accepted - order schedule unchanged.")
    
    # ========================================================================
    # WORKFLOW COMPLETE
    # ========================================================================
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #28a745 0%, #20c997 100%); padding: 20px; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0;">✅ Workflow Complete!</h2>
        <p style="color: white; margin: 10px 0 0 0;">All 17 procurement workflow steps have been executed successfully.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary
    st.subheader("📊 Workflow Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📈 Products Forecasted", len(sales_forecast.forecasts))
    col2.metric("🏭 Production Orders", len(internal_schedule.orders))
    col3.metric("🔩 Materials Forecasted", len(materials_forecast.forecasts))
    col4.metric("📦 External Orders", len(order_schedule.orders))
    col5.metric("💰 Quotes Received", len(quotes))


if __name__ == "__main__":
    main()
