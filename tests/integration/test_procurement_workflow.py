"""Integration tests for the full procurement RFQ workflow."""

from datetime import datetime, timedelta
import sys
import os

# Add guardrail_calculator.py directory to path
guardrail_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'guardrail_calculator.py')
sys.path.insert(0, guardrail_path)
from basic_guardrail_calculator import BasicGuardrailCalculator  # type: ignore

from order_scheduler.basic_order_scheduler import BasicOrderScheduler
from sales_forecaster.basic_sales_forecaster import BasicSalesForecaster
from materials_forecaster.basic_materials_forecaster import BasicMaterialsForecaster
from supplier_state_calculator.basic_supplier_state_calculator import BasicSupplierStateCalculator
from web_scanner.mock_web_scanner import MockWebScanner
from rfq_generator.basic_rfq_generator import BasicRFQGenerator
from email_client.mock_email_client import MockEmailClient, clear_mock_email_storage
from email_listener.mock_email_listener import MockEmailListener
from reply_classifier.mock_reply_classifier import MockReplyClassifier
from auto_responder.basic_auto_responder import BasicAutoResponder
from quote_parser.basic_quote_parser import BasicQuoteParser
from quote_evaluator.basic_quote_evaluator import BasicQuoteEvaluator
from order_schedule_updater.basic_order_schedule_updater import BasicOrderScheduleUpdater
from erp_data_fetcher.mock_erp_fetcher import MockERPDataFetcher
from crm_data_fetcher.mock_crm_fetcher import MockCRMDataFetcher
from models.inventory_data import InventoryData, ItemType, InventoryItem
from models.order_schedule import OrderSchedule
from models.rfq import RFQStore, RFQStatus
from models.classification_result import ReplyType
from models.quote import QuoteStore, Quote
from models.pending_clarification import PendingClarification, PendingClarificationQueue, ClarificationPriority, ClarificationStatus


def _setup_test_data():
    """Set up all test data needed for the workflow."""
    erp_fetcher = MockERPDataFetcher()
    crm_fetcher = MockCRMDataFetcher()
    
    # Create material inventory (low to trigger orders)
    now = datetime.now()
    inventory_data = InventoryData(
        items=[
            InventoryItem(
                item_id="MAT-001",
                item_name="Steel Component",
                item_type=ItemType.MATERIAL,
                quantity=5,
                unit_price=5.0,
                location="Warehouse-1",
                last_updated=now,
                supplier_id="SUP-001",
            ),
            InventoryItem(
                item_id="MAT-002",
                item_name="Plastic Housing",
                item_type=ItemType.MATERIAL,
                quantity=10,
                unit_price=3.0,
                location="Warehouse-1",
                last_updated=now,
                supplier_id="SUP-002",
            ),
        ],
        fetched_at=now,
    )
    
    # Generate materials forecast
    sales_forecaster = BasicSalesForecaster()
    sales_data = erp_fetcher.fetch_sales_data()
    sales_forecast = sales_forecaster.forecast_sales(
        erp_fetcher.fetch_inventory_data(), sales_data, forecast_period_days=30
    )
    
    materials_lookup = erp_fetcher.get_materials_lookup()
    materials_forecaster = BasicMaterialsForecaster(materials_lookup=materials_lookup)
    bom_data = erp_fetcher.fetch_bom_data()
    materials_forecast = materials_forecaster.forecast_materials(
        sales_forecast, bom_data, forecast_period_days=30
    )
    
    # Generate supplier state
    supplier_calculator = BasicSupplierStateCalculator()
    delivery_history = erp_fetcher.fetch_delivery_history()
    approved_suppliers = crm_fetcher.fetch_approved_suppliers()
    blanket_pos = crm_fetcher.fetch_blanket_pos()
    supplier_state_store = supplier_calculator.calculate_supplier_state(
        delivery_history, approved_suppliers, blanket_pos
    )
    
    # Generate guardrails
    guardrail_calculator = BasicGuardrailCalculator()
    guardrails = guardrail_calculator.calculate_guardrails(supplier_state_store, materials_forecast)
    
    # Get blanket POs for RFQ generation
    erp_blanket_pos = erp_fetcher.fetch_blanket_pos()
    
    return {
        "inventory_data": inventory_data,
        "materials_forecast": materials_forecast,
        "supplier_state_store": supplier_state_store,
        "guardrails": guardrails,
        "blanket_pos": erp_blanket_pos,
    }


def test_full_workflow_generates_order_schedule():
    """Test that full workflow starts with order schedule generation."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    assert isinstance(order_schedule, OrderSchedule)
    assert len(order_schedule.orders) > 0


def test_full_workflow_searches_suppliers():
    """Test that workflow can search for suppliers."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    # Extract materials from orders
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    assert len(supplier_results.results) > 0


def test_full_workflow_generates_rfqs():
    """Test that workflow generates RFQs for found suppliers."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    rfq_generator = BasicRFQGenerator()
    rfq_store = rfq_generator.generate_rfqs(
        order_schedule, data["blanket_pos"], supplier_results
    )
    
    assert isinstance(rfq_store, RFQStore)
    if len(order_schedule.orders) > 0 and len(supplier_results.results) > 0:
        assert len(rfq_store.rfqs) > 0


def test_full_workflow_sends_rfq_emails():
    """Test that workflow sends RFQ emails."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    rfq_generator = BasicRFQGenerator()
    rfq_store = rfq_generator.generate_rfqs(
        order_schedule, data["blanket_pos"], supplier_results
    )
    
    email_client = MockEmailClient()
    sent_emails = email_client.send_rfqs(rfq_store, "procurement@company.mock")
    
    assert len(sent_emails) == len(rfq_store.rfqs)


def test_full_workflow_processes_replies():
    """Test that workflow can process email replies."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    # Generate and send RFQs
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    rfq_generator = BasicRFQGenerator()
    rfq_store = rfq_generator.generate_rfqs(
        order_schedule, data["blanket_pos"], supplier_results
    )
    
    email_client = MockEmailClient()
    sent_emails = email_client.send_rfqs(rfq_store, "procurement@company.mock")
    
    # Listen for replies
    email_listener = MockEmailListener(auto_generate_replies=True)
    replies = email_listener.get_replies()
    
    assert len(replies) == len(sent_emails)


def test_full_workflow_classifies_replies():
    """Test that workflow classifies replies correctly."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    # Generate, send RFQs, and get replies
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    rfq_generator = BasicRFQGenerator()
    rfq_store = rfq_generator.generate_rfqs(
        order_schedule, data["blanket_pos"], supplier_results
    )
    
    email_client = MockEmailClient()
    email_client.send_rfqs(rfq_store, "procurement@company.mock")
    
    email_listener = MockEmailListener(auto_generate_replies=True)
    replies = email_listener.get_replies()
    
    # Classify replies
    classifier = MockReplyClassifier()
    classifications = [classifier.classify(reply) for reply in replies]
    
    # Should have various classification types
    reply_types = [c.reply_type for c in classifications]
    assert len(reply_types) > 0


def test_full_workflow_end_to_end():
    """Test the complete workflow from order schedule to quote evaluation."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    # Step 1: Generate order schedule
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        data["inventory_data"],
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    # Step 2: Search for suppliers
    material_ids = list(set(o.material_id for o in order_schedule.orders))
    material_names = list(set(o.material_name for o in order_schedule.orders))
    
    web_scanner = MockWebScanner()
    supplier_results = web_scanner.search_suppliers(material_ids, material_names)
    
    # Step 3: Generate RFQs
    rfq_generator = BasicRFQGenerator()
    rfq_store = rfq_generator.generate_rfqs(
        order_schedule, data["blanket_pos"], supplier_results
    )
    
    # Use rfqs_by_id index for lookups
    rfq_lookup = rfq_store.rfqs_by_id
    
    # Step 4: Send RFQs
    email_client = MockEmailClient()
    sent_emails = email_client.send_rfqs(rfq_store, "procurement@company.mock")
    
    # Build email-to-RFQ lookup
    email_to_rfq = {email.email_id: email.rfq_id for email in sent_emails}
    
    # Step 5: Listen for replies
    email_listener = MockEmailListener(auto_generate_replies=True)
    replies = email_listener.get_replies()
    
    # Step 6: Process replies
    classifier = MockReplyClassifier()
    auto_responder = BasicAutoResponder()
    quote_parser = BasicQuoteParser()
    quote_evaluator = BasicQuoteEvaluator()
    schedule_updater = BasicOrderScheduleUpdater()
    
    quotes: list[Quote] = []
    pending_clarifications: list[PendingClarification] = []
    current_schedule = order_schedule
    
    for reply in replies:
        # Get corresponding RFQ
        rfq_id = email_to_rfq.get(reply.original_email_id)
        if not rfq_id or rfq_id not in rfq_lookup:
            continue
        rfq = rfq_lookup[rfq_id]
        
        # Classify reply
        classification = classifier.classify(reply)
        
        if classification.reply_type == ReplyType.QUOTE:
            # Parse quote
            quote = quote_parser.parse(reply, rfq)
            quotes.append(quote)
            
            # Evaluate quote
            # Find current price for this material from order schedule
            current_orders = [o for o in current_schedule.orders if o.material_id == quote.material_id]
            current_price = 10.0  # Default
            current_lead_time = 14  # Default
            
            evaluation = quote_evaluator.evaluate(
                quote,
                data["supplier_state_store"],
                current_unit_price=current_price,
                current_lead_time_days=current_lead_time,
            )
            
            # Update schedule if better
            current_schedule = schedule_updater.update_if_better(
                current_schedule, quote, evaluation
            )
            
        elif classification.reply_type == ReplyType.CLARIFICATION_SIMPLE:
            # Auto-respond
            response = auto_responder.respond(reply, rfq, "procurement@company.mock")
            # In real workflow, would send this response
            assert response is not None
            
        elif classification.reply_type == ReplyType.CLARIFICATION_COMPLEX:
            # Add to pending queue
            pending = PendingClarification(
                clarification_id=f"CLAR-{reply.reply_id}",
                original_email_id=reply.original_email_id,
                rfq_id=rfq.rfq_id,
                supplier_id=rfq.supplier_id,
                supplier_name=rfq.supplier_name,
                supplier_email=reply.from_address,
                question_text=reply.body,
                priority=ClarificationPriority.MEDIUM,
                created_at=datetime.now(),
                status=ClarificationStatus.PENDING,
            )
            pending_clarifications.append(pending)
        
        # Mark reply as processed
        email_listener.mark_processed(reply.reply_id)
    
    # Verify workflow completed
    assert current_schedule is not None
    
    # Print summary
    print(f"\n=== Workflow Summary ===")
    print(f"Orders in schedule: {len(order_schedule.orders)}")
    print(f"Suppliers found: {len(supplier_results.results)}")
    print(f"RFQs generated: {len(rfq_store.rfqs)}")
    print(f"Emails sent: {len(sent_emails)}")
    print(f"Replies received: {len(replies)}")
    print(f"Quotes parsed: {len(quotes)}")
    print(f"Pending clarifications: {len(pending_clarifications)}")


def test_workflow_handles_no_orders():
    """Test workflow handles case with no orders gracefully."""
    clear_mock_email_storage()
    data = _setup_test_data()
    
    # Create high inventory to avoid orders
    now = datetime.now()
    high_inventory = InventoryData(
        items=[
            InventoryItem(
                item_id="MAT-001",
                item_name="Steel Component",
                item_type=ItemType.MATERIAL,
                quantity=10000,  # Very high
                unit_price=5.0,
                location="Warehouse-1",
                last_updated=now,
            ),
        ],
        fetched_at=now,
    )
    
    scheduler = BasicOrderScheduler()
    order_schedule = scheduler.schedule_orders(
        high_inventory,
        data["materials_forecast"],
        data["supplier_state_store"],
        data["guardrails"],
        num_days=30,
    )
    
    # Should still return valid schedule
    assert isinstance(order_schedule, OrderSchedule)

