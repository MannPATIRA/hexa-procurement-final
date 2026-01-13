"""Display supplier datasets and metrics."""

import sys
from pathlib import Path

# Add src and tests to path for imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
tests_path = project_root / "tests"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(tests_path))

from datetime import datetime
from order_builder.test_supplier_data import (
    create_test_suppliers,
    create_test_supplier_states,
    create_test_quotes,
)
from models.quote import QuoteStatus


def display_suppliers(suppliers):
    """Display supplier information."""
    print("\n" + "="*100)
    print("SUPPLIER DATASET")
    print("="*100)
    print(f"\nTotal Suppliers: {len(suppliers.suppliers)}\n")
    
    for i, supplier in enumerate(suppliers.suppliers, 1):
        print(f"{i}. {supplier.supplier_name} ({supplier.supplier_id})")
        print(f"   Status: {supplier.status.value.upper()}")
        print(f"   Rating: {supplier.rating if supplier.rating else 'N/A'}/5.0")
        print(f"   Email: {supplier.contact_email}")
        print(f"   Phone: {supplier.contact_phone if supplier.contact_phone else 'N/A'}")
        print(f"   Categories: {', '.join(supplier.categories)}")
        print(f"   Approved: {(datetime.now() - supplier.approved_date).days} days ago")
        if supplier.notes:
            print(f"   Notes: {supplier.notes}")
        print()


def display_supplier_states(states):
    """Display supplier state metrics."""
    print("\n" + "="*100)
    print("SUPPLIER STATE METRICS")
    print("="*100)
    print(f"\nTotal Supplier-Product States: {len(states.states)}\n")
    
    # Header
    print(f"{'Supplier':<35} {'Product':<30} {'Deliveries':<12} {'Success %':<12} "
          f"{'Lead Time':<12} {'Defect %':<12} {'Status':<15}")
    print("-"*100)
    
    for state in states.states:
        lead_time = f"{state.average_lead_time_days:.1f}d" if state.average_lead_time_days else "N/A"
        defect_rate = f"{state.average_defect_rate*100:.1f}%" if state.average_defect_rate else "N/A"
        last_delivery = f"{(datetime.now() - state.last_delivery_date).days}d ago" if state.last_delivery_date else "Never"
        
        print(f"{state.supplier_name[:34]:<35} {state.product_name[:29]:<30} "
              f"{state.total_deliveries:<12} {state.success_rate:.1f}%{'':<7} "
              f"{lead_time:<12} {defect_rate:<12} {state.supplier_status.value:<15}")
    
    # Summary statistics
    print("\n" + "-"*100)
    print("SUMMARY STATISTICS:")
    print("-"*100)
    
    total_deliveries = sum(s.total_deliveries for s in states.states)
    total_successful = sum(s.successful_deliveries for s in states.states)
    avg_success_rate = sum(s.success_rate for s in states.states) / len(states.states) if states.states else 0
    
    states_with_lead_time = [s for s in states.states if s.average_lead_time_days is not None]
    avg_lead_time = sum(s.average_lead_time_days for s in states_with_lead_time) / len(states_with_lead_time) if states_with_lead_time else 0
    
    states_with_defect_rate = [s for s in states.states if s.average_defect_rate is not None]
    avg_defect_rate = sum(s.average_defect_rate for s in states_with_defect_rate) / len(states_with_defect_rate) if states_with_defect_rate else 0
    
    active_states = [s for s in states.states if s.supplier_status.value == 'active']
    total_bpos = sum(s.active_blanket_pos_count for s in states.states)
    
    print(f"Total Deliveries: {total_deliveries}")
    print(f"Total Successful: {total_successful}")
    print(f"Average Success Rate: {avg_success_rate:.1f}%")
    print(f"Average Lead Time: {avg_lead_time:.1f} days ({len(states_with_lead_time)} suppliers with data)")
    print(f"Average Defect Rate: {avg_defect_rate*100:.2f}% ({len(states_with_defect_rate)} suppliers with data)")
    print(f"Active Suppliers: {len(active_states)}")
    print(f"Total Active Blanket POs: {total_bpos}")


def display_quotes(quotes):
    """Display quote information."""
    print("\n" + "="*100)
    print("QUOTES DATASET")
    print("="*100)
    print(f"\nTotal Quotes: {len(quotes)}\n")
    
    # Header
    print(f"{'Quote ID':<10} {'Supplier':<35} {'Material':<25} {'Price':<10} {'Qty':<6} "
          f"{'Total':<12} {'Lead Time':<12} {'Status':<15}")
    print("-"*100)
    
    for quote in quotes:
        print(f"{quote.quote_id:<10} {quote.supplier_name[:34]:<35} {quote.material_name[:24]:<25} "
              f"${quote.unit_price:<9.2f} {quote.quantity:<6} ${quote.total_price:<11.2f} "
              f"{quote.lead_time_days}d{'':<8} {quote.status.value:<15}")
    
    # Summary
    print("\n" + "-"*100)
    print("QUOTE SUMMARY:")
    print("-"*100)
    
    accepted = [q for q in quotes if q.status == QuoteStatus.ACCEPTED]
    under_review = [q for q in quotes if q.status == QuoteStatus.UNDER_REVIEW]
    received = [q for q in quotes if q.status == QuoteStatus.RECEIVED]
    
    total_value = sum(q.total_price for q in quotes)
    accepted_value = sum(q.total_price for q in accepted)
    
    print(f"Accepted: {len(accepted)} quotes (${accepted_value:,.2f})")
    print(f"Under Review: {len(under_review)} quotes")
    print(f"Received: {len(received)} quotes")
    print(f"Total Quote Value: ${total_value:,.2f}")
    
    avg_lead_time = sum(q.lead_time_days for q in quotes) / len(quotes) if quotes else 0
    print(f"Average Lead Time: {avg_lead_time:.1f} days")


def display_data_completeness(suppliers, states):
    """Display data completeness analysis."""
    print("\n" + "="*100)
    print("DATA COMPLETENESS ANALYSIS")
    print("="*100)
    
    # Supplier completeness
    complete_suppliers = [s for s in suppliers.suppliers 
                         if s.rating is not None and s.contact_phone is not None and s.notes is not None]
    incomplete_suppliers = [s for s in suppliers.suppliers 
                           if s.rating is None or s.contact_phone is None or s.notes is None]
    
    print(f"\nSuppliers:")
    print(f"  Complete data: {len(complete_suppliers)} ({len(complete_suppliers)/len(suppliers.suppliers)*100:.0f}%)")
    print(f"  Incomplete data: {len(incomplete_suppliers)} ({len(incomplete_suppliers)/len(suppliers.suppliers)*100:.0f}%)")
    
    # State completeness
    complete_states = [s for s in states.states 
                      if s.average_lead_time_days is not None 
                      and s.average_defect_rate is not None 
                      and s.last_delivery_date is not None]
    incomplete_states = [s for s in states.states 
                        if s.average_lead_time_days is None 
                        or s.average_defect_rate is None 
                        or s.last_delivery_date is None]
    
    print(f"\nSupplier States:")
    print(f"  Complete data: {len(complete_states)} ({len(complete_states)/len(states.states)*100:.0f}%)")
    print(f"  Incomplete data: {len(incomplete_states)} ({len(incomplete_states)/len(states.states)*100:.0f}%)")
    
    # Missing fields breakdown
    missing_lead_time = [s for s in states.states if s.average_lead_time_days is None]
    missing_defect_rate = [s for s in states.states if s.average_defect_rate is None]
    missing_delivery_date = [s for s in states.states if s.last_delivery_date is None]
    
    print(f"\nMissing Fields in States:")
    print(f"  Lead Time: {len(missing_lead_time)} suppliers")
    print(f"  Defect Rate: {len(missing_defect_rate)} suppliers")
    print(f"  Last Delivery Date: {len(missing_delivery_date)} suppliers")


def main():
    """Display all supplier data and metrics."""
    print("\n" + "="*100)
    print("FAKE SUPPLIER DATASETS AND METRICS")
    print("="*100)
    
    # Load data
    suppliers = create_test_suppliers()
    states = create_test_supplier_states()
    quotes = create_test_quotes()
    
    # Display
    display_suppliers(suppliers)
    display_supplier_states(states)
    display_quotes(quotes)
    display_data_completeness(suppliers, states)
    
    print("\n" + "="*100)
    print("END OF REPORT")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
