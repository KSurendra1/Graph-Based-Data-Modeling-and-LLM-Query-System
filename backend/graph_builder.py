import networkx as nx
from database import SessionLocal
from models import (
    BusinessPartner, Product, Plant, SalesOrderHeader, SalesOrderItem,
    OutboundDeliveryHeader, OutboundDeliveryItem, BillingDocumentHeader,
    BillingDocumentItem, JournalEntryItem, PaymentAccountsReceivable
)

def build_graph():
    """Builds a NetworkX Directed Graph from real SQLite sap-o2c tables."""
    G = nx.DiGraph()
    db = SessionLocal()
    
    # 1. Business Partners (Customers)
    bps = db.query(BusinessPartner).all()
    for bp in bps:
        node_id = f"BP_{bp.businessPartner}"
        G.add_node(node_id, label="Customer", type="Customer", properties={
            "Name": bp.businessPartnerFullName,
            "Category": bp.businessPartnerCategory
        })
        
    # 2. Products
    prods = db.query(Product).all()
    for p in prods:
        node_id = f"PR_{p.product}"
        G.add_node(node_id, label="Product", type="Product", properties={
            "Type": p.productType,
            "Status": p.crossPlantStatus
        })
        
    # 3. Plants
    plants = db.query(Plant).all()
    for pl in plants:
        node_id = f"PL_{pl.plant}"
        G.add_node(node_id, label="Plant", type="Plant", properties={
            "Name": pl.plantName
        })
        
    # 4. Sales Orders
    orders = db.query(SalesOrderHeader).all()
    for o in orders:
        node_id = f"SO_{o.salesOrder}"
        G.add_node(node_id, label="SalesOrder", type="Order", properties={
            "Date": o.creationDate,
            "Amount": o.totalNetAmount,
            "Currency": o.transactionCurrency,
            "Status": o.overallDeliveryStatus
        })
        # Customer -> Sales Order
        if o.soldToParty:
            G.add_edge(f"BP_{o.soldToParty}", node_id, type="PLACES_ORDER", label="PLACES_ORDER")
            
    # 5. Sales Order Items
    order_items = db.query(SalesOrderItem).all()
    for oi in order_items:
        node_id = f"SOI_{oi.salesOrder}_{oi.salesOrderItem}"
        G.add_node(node_id, label="OrderItem", type="OrderItem", properties={
            "Quantity": oi.requestedQuantity,
            "Amount": oi.netAmount
        })
        # Order -> Order Item
        if oi.salesOrder:
            G.add_edge(f"SO_{oi.salesOrder}", node_id, type="HAS_ITEM", label="HAS_ITEM")
        # Order Item -> Product
        if oi.material:
            G.add_edge(node_id, f"PR_{oi.material}", type="IS_PRODUCT", label="IS_PRODUCT")
        # Order Item -> Plant
        if oi.productionPlant:
            G.add_edge(node_id, f"PL_{oi.productionPlant}", type="SHIPS_FROM", label="SHIPS_FROM")

    # 6. Deliveries (Headers and Items)
    delivs = db.query(OutboundDeliveryHeader).all()
    for d in delivs:
        node_id = f"OD_{d.deliveryDocument}"
        G.add_node(node_id, label="Delivery", type="Delivery", properties={
            "Date": d.actualGoodsMovementDate
        })
        
    deliv_items = db.query(OutboundDeliveryItem).all()
    for di in deliv_items:
        deliv_id = f"OD_{di.deliveryDocument}"
        # Delivery Item just connects Order to Delivery. 
        # For simplicity, we create an edge Sales Order -> Delivery
        if di.referenceSdDocument and di.deliveryDocument:
            so_node = f"SO_{di.referenceSdDocument}"
            G.add_edge(so_node, deliv_id, type="DELIVERED_IN", label="DELIVERED_IN")

    # 7. Billing Documents (Invoices)
    bills = db.query(BillingDocumentHeader).all()
    for b in bills:
        node_id = f"BD_{b.billingDocument}"
        G.add_node(node_id, label="BillingDoc", type="Invoice", properties={
            "Date": b.billingDocumentDate,
            "Amount": b.totalNetAmount,
            "Currency": b.transactionCurrency
        })
        # Customer (soldToParty) implicitly linked, but we can link via Billing Items -> Sales Order
        
    bill_items = db.query(BillingDocumentItem).all()
    for bi in bill_items:
        bill_id = f"BD_{bi.billingDocument}"
        if bi.referenceSdDocument and bi.billingDocument:
            so_node = f"SO_{bi.referenceSdDocument}" # Often Sales Order or Delivery
            # Create edge from Order -> Invoice
            G.add_edge(so_node, bill_id, type="BILLED_IN", label="BILLED_IN")
            
    # 8. Journal Entries
    jrnls = db.query(JournalEntryItem).all()
    for je in jrnls:
        node_id = f"JE_{je.accountingDocument}"
        G.add_node(node_id, label="JournalEntry", type="JournalEntry", properties={
            "Amount": je.amountInTransactionCurrency,
            "Currency": je.transactionCurrency,
            "CompanyCode": je.companyCode,
            "FiscalYear": je.fiscalYear
        })
        # Billing Doc -> Journal Entry
        if je.referenceDocument:
            G.add_edge(f"BD_{je.referenceDocument}", node_id, type="POSTED_TO", label="POSTED_TO")
            
    # 9. Payments
    payments = db.query(PaymentAccountsReceivable).all()
    for pay in payments:
        node_id = f"PAY_{pay.accountingDocument}"
        G.add_node(node_id, label="Payment", type="Payment", properties={
            "Amount": pay.amountInTransactionCurrency,
            "Currency": pay.transactionCurrency,
            "CompanyCode": pay.companyCode,
            "FiscalYear": pay.fiscalYear
        })
        # Journal Entry -> Payment
        # clearingAccountingDocument on the Journal Entry matches the payment accountingDocument
        # Or payment clearingAccountingDocument matches the journal entry accountingDocument?
        # Actually standard SAP: payment clears invoice JE. We link Invoice JE -> Payment
        if pay.clearingAccountingDocument:
            G.add_edge(f"JE_{pay.clearingAccountingDocument}", node_id, type="CLEARED_BY", label="CLEARED_BY")
            
    db.close()
    return G

def get_graph_data(G):
    """Converts NetworkX graph to frontend-friendly Cytoscape format."""
    nodes = []
    edges = []
    
    # Cytoscape rendering optimizations: handle orphaned nodes gracefully
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": str(node),
            "label": data.get("label", ""),
            "type": data.get("type", ""),
            "properties": data.get("properties", {})
        })
        
    for u, v, data in G.edges(data=True):
        if G.has_node(u) and G.has_node(v):
            edges.append({
                "id": f"e_{u}_{v}_{data.get('type', '')}",
                "source": str(u),
                "target": str(v),
                "type": data.get("type", "")
            })
        
    return {"nodes": nodes, "edges": edges}
