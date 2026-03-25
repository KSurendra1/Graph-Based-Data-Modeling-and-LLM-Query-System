from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# -------------------------
# SQLAlchemy Database Models (Real Schema)
# -------------------------
class BusinessPartner(Base):
    __tablename__ = "business_partners"
    businessPartner = Column(String, primary_key=True, index=True)
    businessPartnerFullName = Column(String)
    businessPartnerCategory = Column(String)

class Product(Base):
    __tablename__ = "products"
    product = Column(String, primary_key=True, index=True)
    productType = Column(String)
    crossPlantStatus = Column(String)

class Plant(Base):
    __tablename__ = "plants"
    plant = Column(String, primary_key=True, index=True)
    plantName = Column(String)

class SalesOrderHeader(Base):
    __tablename__ = "sales_order_headers"
    salesOrder = Column(String, primary_key=True, index=True)
    soldToParty = Column(String, index=True) # maps to businessPartner
    creationDate = Column(String)
    totalNetAmount = Column(Float)
    transactionCurrency = Column(String)
    overallDeliveryStatus = Column(String)

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    salesOrder = Column(String, index=True)
    salesOrderItem = Column(String)
    material = Column(String, index=True) # maps to product
    requestedQuantity = Column(Float)
    netAmount = Column(Float)
    productionPlant = Column(String, index=True) # maps to plant

class OutboundDeliveryHeader(Base):
    __tablename__ = "outbound_delivery_headers"
    deliveryDocument = Column(String, primary_key=True, index=True)
    actualGoodsMovementDate = Column(String)

class OutboundDeliveryItem(Base):
    __tablename__ = "outbound_delivery_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deliveryDocument = Column(String, index=True)
    deliveryDocumentItem = Column(String)
    plant = Column(String, index=True)
    referenceSdDocument = Column(String, index=True) # maps to salesOrder
    referenceSdDocumentItem = Column(String)

class BillingDocumentHeader(Base):
    __tablename__ = "billing_document_headers"
    billingDocument = Column(String, primary_key=True, index=True)
    billingDocumentDate = Column(String)
    totalNetAmount = Column(Float)
    transactionCurrency = Column(String)
    soldToParty = Column(String, index=True)
    companyCode = Column(String)
    accountingDocument = Column(String, index=True)

class BillingDocumentItem(Base):
    __tablename__ = "billing_document_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    billingDocument = Column(String, index=True)
    billingDocumentItem = Column(String)
    material = Column(String)
    referenceSdDocument = Column(String, index=True)
    referenceSdDocumentItem = Column(String)
    netAmount = Column(Float)

class JournalEntryItem(Base):
    __tablename__ = "journal_entry_items_accounts_receivable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    companyCode = Column(String)
    fiscalYear = Column(String)
    accountingDocument = Column(String, index=True)
    referenceDocument = Column(String, index=True) # maps to billingDocument
    amountInTransactionCurrency = Column(Float)
    transactionCurrency = Column(String)
    clearingAccountingDocument = Column(String, index=True) # maps to payment

class PaymentAccountsReceivable(Base):
    __tablename__ = "payments_accounts_receivable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    companyCode = Column(String)
    fiscalYear = Column(String)
    accountingDocument = Column(String, index=True) # Payment document ID
    clearingAccountingDocument = Column(String, index=True) # The ID linking to the original Journal Entry
    amountInTransactionCurrency = Column(Float)
    transactionCurrency = Column(String)

# -------------------------
# Pydantic API Models
# -------------------------
class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    natural_response: str
    sql_query: Optional[str] = None
    structured_data: Optional[List[Dict[str, Any]]] = None
    affected_nodes: Optional[List[str]] = None
