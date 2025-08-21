"""
Simple mock server for testing invoice functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import uuid

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
invoices_db = {}
companies_db = {
    "1": {
        "id": "1",
        "name": "Test Company",
        "address": "123 Main St",
        "city": "Test City",
        "state": "TS",
        "zip": "12345",
        "phone": "555-1234",
        "email": "test@company.com"
    }
}

# Models
class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit: str
    rate: float
    amount: float

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: str
    due_date: Optional[str]
    company_id: str
    client_name: str
    client_address: Optional[str]
    client_phone: Optional[str]
    client_email: Optional[str]
    items: List[InvoiceItem]
    subtotal: float
    tax_rate: Optional[float] = 0
    tax_amount: Optional[float] = 0
    total: float
    notes: Optional[str]
    insurance_company: Optional[str]
    claim_number: Optional[str]
    policy_number: Optional[str]
    deductible: Optional[float]

# Routes
@app.get("/api/companies")
async def get_companies():
    return {"data": list(companies_db.values())}

@app.get("/api/companies/{company_id}")
async def get_company(company_id: str):
    if company_id not in companies_db:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"data": companies_db[company_id]}

@app.post("/api/invoices")
async def create_invoice(invoice: Invoice):
    invoice_id = str(uuid.uuid4())
    invoice_data = invoice.dict()
    invoice_data["id"] = invoice_id
    invoice_data["created_at"] = datetime.now().isoformat()
    invoice_data["updated_at"] = datetime.now().isoformat()
    invoice_data["status"] = "draft"
    invoices_db[invoice_id] = invoice_data
    return invoice_data

@app.get("/api/invoices")
async def get_invoices():
    return list(invoices_db.values())

@app.get("/api/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoices_db[invoice_id]

@app.put("/api/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, invoice: Invoice):
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice_data = invoice.dict()
    invoice_data["id"] = invoice_id
    invoice_data["updated_at"] = datetime.now().isoformat()
    invoices_db[invoice_id] = {**invoices_db[invoice_id], **invoice_data}
    return invoices_db[invoice_id]

@app.delete("/api/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    del invoices_db[invoice_id]
    return {"message": "Invoice deleted successfully"}

@app.post("/api/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str):
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # For testing, return a mock response
    return {
        "message": "PDF generated successfully",
        "filename": f"invoice_{invoice_id}.pdf",
        "path": f"/tmp/invoice_{invoice_id}.pdf"
    }

@app.post("/api/invoices/preview-pdf")
async def preview_invoice_pdf(invoice: Invoice):
    # For testing, return a mock response
    return {
        "message": "PDF preview generated",
        "filename": "preview.pdf",
        "path": "/tmp/preview.pdf"
    }

@app.get("/")
async def root():
    return {"message": "Invoice API Mock Server", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)