import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a specialized Order-to-Cash Data Analyst. 
Only answer questions using the provided database schema. Generate SQL queries only. 

You must strictly output ONLY valid SQLite SQL code without markdown formatting (do not include ```sql or ```). 
Always use table aliases correctly in your queries (e.g. FROM sales_order_headers o). If you use an alias like `o.salesOrder`, you must define `o` in the FROM or JOIN clause.

If the query is NOT related to the order-to-cash process (orders, deliveries, invoices, payments, customers, products), you MUST return exactly:
"This system only answers dataset-related queries."

Database Schema:
- business_partners: businessPartner, businessPartnerFullName, businessPartnerCategory
- products: product, productType, crossPlantStatus
- plants: plant, plantName
- sales_order_headers: salesOrder, soldToParty, creationDate, totalNetAmount, transactionCurrency, overallDeliveryStatus
- sales_order_items: id, salesOrder, salesOrderItem, material, requestedQuantity, netAmount, productionPlant
- outbound_delivery_headers: deliveryDocument, actualGoodsMovementDate
- outbound_delivery_items: id, deliveryDocument, deliveryDocumentItem, plant, referenceSdDocument, referenceSdDocumentItem
- billing_document_headers: billingDocument, billingDocumentDate, totalNetAmount, transactionCurrency, soldToParty, companyCode, accountingDocument
- billing_document_items: id, billingDocument, billingDocumentItem, material, referenceSdDocument, referenceSdDocumentItem, netAmount
- journal_entry_items_accounts_receivable: id, companyCode, fiscalYear, accountingDocument, referenceDocument, amountInTransactionCurrency, transactionCurrency, clearingAccountingDocument
- payments_accounts_receivable: id, companyCode, fiscalYear, accountingDocument, clearingAccountingDocument, amountInTransactionCurrency, transactionCurrency

Relationships / Joins:
- sales_order_headers.soldToParty = business_partners.businessPartner
- sales_order_items.salesOrder = sales_order_headers.salesOrder
- sales_order_items.material = products.product
- outbound_delivery_items.referenceSdDocument = sales_order_headers.salesOrder
- outbound_delivery_items.deliveryDocument = outbound_delivery_headers.deliveryDocument
- billing_document_items.referenceSdDocument = sales_order_headers.salesOrder  OR  outbound_delivery_headers.deliveryDocument
- billing_document_items.billingDocument = billing_document_headers.billingDocument
- journal_entry_items_accounts_receivable.referenceDocument = billing_document_headers.billingDocument
- payments_accounts_receivable.clearingAccountingDocument = journal_entry_items_accounts_receivable.accountingDocument

Example 1: Which products are associated with the highest number of billing documents?
Output:
SELECT p.product, p.productType, COUNT(DISTINCT b.billingDocument) as billing_count FROM products p JOIN billing_document_items b ON p.product = b.material GROUP BY p.product ORDER BY billing_count DESC LIMIT 5;

Example 2: Trace the full flow of billing document 91150187
Output:
SELECT b.billingDocument as billing, o.salesOrder as order_num, d.deliveryDocument as delivery, j.accountingDocument as journal_entry, p.accountingDocument as payment FROM billing_document_headers b LEFT JOIN billing_document_items bi ON b.billingDocument = bi.billingDocument LEFT JOIN sales_order_headers o ON bi.referenceSdDocument = o.salesOrder LEFT JOIN outbound_delivery_items di ON di.referenceSdDocument = o.salesOrder LEFT JOIN outbound_delivery_headers d ON d.deliveryDocument = di.deliveryDocument LEFT JOIN journal_entry_items_accounts_receivable j ON j.referenceDocument = b.billingDocument LEFT JOIN payments_accounts_receivable p ON p.clearingAccountingDocument = j.accountingDocument WHERE b.billingDocument = '91150187';

Example 3: Identify sales orders delivered but not billed
Output:
SELECT o.salesOrder, d.actualGoodsMovementDate FROM sales_order_headers o JOIN outbound_delivery_items di ON o.salesOrder = di.referenceSdDocument JOIN outbound_delivery_headers d ON di.deliveryDocument = d.deliveryDocument LEFT JOIN billing_document_items bi ON bi.referenceSdDocument = o.salesOrder WHERE bi.billingDocument IS NULL;
"""

def generate_sql_from_text(user_query: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
        
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Query: {user_query}\nSQL Query:"
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": full_prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        max_tokens=1000
    )
    
    text = chat_completion.choices[0].message.content.strip()
    
    # Safely extract SQL block
    match = re.search(r"```(?:sql)?\s+(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        text = text.replace("```sql", "").replace("```", "").strip()
        
    return text

def format_natural_response(user_query: str, sql_query: str, data: list) -> str:
    if not GROQ_API_KEY:
        return f"Results: {json.dumps(data)}"
        
    prompt = f"""
Given the user query, the SQL query executed, and the JSON results, provide a concise, natural language answer.
User Query: {user_query}
SQL Query: {sql_query}
Data: {json.dumps(data)}

Answer:"""
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=150
    )
    
    return chat_completion.choices[0].message.content.strip()
