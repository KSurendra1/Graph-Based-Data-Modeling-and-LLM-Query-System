import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Base, BusinessPartner, Product, Plant, SalesOrderHeader, SalesOrderItem,
    OutboundDeliveryHeader, OutboundDeliveryItem, BillingDocumentHeader,
    BillingDocumentItem, JournalEntryItem, PaymentAccountsReceivable
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./graph_system_real.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
def safe_float(val):
    try:
        if val == "" or val is None:
            return 0.0
        return float(val)
    except:
        return 0.0

def generate_mock_data():
    """Loads REAL data from sap-o2c-data JSONL instead of mock."""
    db = SessionLocal()
    
    # Check if data already exists to avoid re-insertion
    if db.query(BusinessPartner).first():
        db.close()
        return
        
    base_dir = "../sap-o2c-data"
    if not os.path.exists(base_dir):
        print(f"Warning: Data directory {base_dir} not found. Skipping data load.")
        db.close()
        return

    # Mappings from folder name to the SQLAlchemy Model and logic for parsing
    # We only care about specific fields depending on the Model definition
    
    print("Loading data from JSONL into SQLite...")
    
    for root, _, files in os.walk(base_dir):
        folder = os.path.basename(root)
        for file in files:
            if file.endswith('.jsonl'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    batch = []
                    for line in f:
                        data = json.loads(line)
                        
                        if folder == "business_partners":
                            batch.append(BusinessPartner(
                                businessPartner=data.get("businessPartner"),
                                businessPartnerFullName=data.get("businessPartnerFullName"),
                                businessPartnerCategory=data.get("businessPartnerCategory")
                            ))
                        elif folder == "products":
                            batch.append(Product(
                                product=data.get("product"),
                                productType=data.get("productType"),
                                crossPlantStatus=data.get("crossPlantStatus")
                            ))
                        elif folder == "plants":
                            batch.append(Plant(
                                plant=data.get("plant"),
                                plantName=data.get("plantName")
                            ))
                        elif folder == "sales_order_headers":
                            batch.append(SalesOrderHeader(
                                salesOrder=data.get("salesOrder"),
                                soldToParty=data.get("soldToParty"),
                                creationDate=data.get("creationDate"),
                                totalNetAmount=safe_float(data.get("totalNetAmount")),
                                transactionCurrency=data.get("transactionCurrency"),
                                overallDeliveryStatus=data.get("overallDeliveryStatus")
                            ))
                        elif folder == "sales_order_items":
                            batch.append(SalesOrderItem(
                                salesOrder=data.get("salesOrder"),
                                salesOrderItem=data.get("salesOrderItem"),
                                material=data.get("material"),
                                requestedQuantity=safe_float(data.get("requestedQuantity")),
                                netAmount=safe_float(data.get("netAmount")),
                                productionPlant=data.get("productionPlant")
                            ))
                        elif folder == "outbound_delivery_headers":
                            batch.append(OutboundDeliveryHeader(
                                deliveryDocument=data.get("deliveryDocument"),
                                actualGoodsMovementDate=data.get("actualGoodsMovementDate")
                            ))
                        elif folder == "outbound_delivery_items":
                            batch.append(OutboundDeliveryItem(
                                deliveryDocument=data.get("deliveryDocument"),
                                deliveryDocumentItem=data.get("deliveryDocumentItem"),
                                plant=data.get("plant"),
                                referenceSdDocument=data.get("referenceSdDocument"),
                                referenceSdDocumentItem=data.get("referenceSdDocumentItem")
                            ))
                        elif folder == "billing_document_headers":
                            batch.append(BillingDocumentHeader(
                                billingDocument=data.get("billingDocument"),
                                billingDocumentDate=data.get("billingDocumentDate"),
                                totalNetAmount=safe_float(data.get("totalNetAmount")),
                                transactionCurrency=data.get("transactionCurrency"),
                                soldToParty=data.get("soldToParty"),
                                companyCode=data.get("companyCode"),
                                accountingDocument=data.get("accountingDocument")
                            ))
                        elif folder == "billing_document_items":
                            batch.append(BillingDocumentItem(
                                billingDocument=data.get("billingDocument"),
                                billingDocumentItem=data.get("billingDocumentItem"),
                                material=data.get("material"),
                                referenceSdDocument=data.get("referenceSdDocument"),
                                referenceSdDocumentItem=data.get("referenceSdDocumentItem"),
                                netAmount=safe_float(data.get("netAmount"))
                            ))
                        elif folder == "journal_entry_items_accounts_receivable":
                            batch.append(JournalEntryItem(
                                companyCode=data.get("companyCode"),
                                fiscalYear=data.get("fiscalYear"),
                                accountingDocument=data.get("accountingDocument"),
                                referenceDocument=data.get("referenceDocument"),
                                amountInTransactionCurrency=safe_float(data.get("amountInTransactionCurrency")),
                                transactionCurrency=data.get("transactionCurrency"),
                                clearingAccountingDocument=data.get("clearingAccountingDocument")
                            ))
                        elif folder == "payments_accounts_receivable":
                            batch.append(PaymentAccountsReceivable(
                                companyCode=data.get("companyCode"),
                                fiscalYear=data.get("fiscalYear"),
                                accountingDocument=data.get("accountingDocument"),
                                clearingAccountingDocument=data.get("clearingAccountingDocument"),
                                amountInTransactionCurrency=safe_float(data.get("amountInTransactionCurrency")),
                                transactionCurrency=data.get("transactionCurrency")
                            ))
                            
                    if batch:
                        try:
                            # Use add_all in smaller chunks if needed, but SQLite handles it fine usually
                            db.add_all(batch)
                            db.commit()
                        except Exception as e:
                            print(f"Error inserting batch for {folder}: {e}")
                            db.rollback()

    db.close()
    print("Finished loading JSONL data into SQLite.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
