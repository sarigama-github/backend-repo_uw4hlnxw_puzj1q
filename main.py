import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Vendor, Invoice, Activity, Rule, User

app = FastAPI(title="PaprFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities

def to_oid(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def serialize(doc: dict):
    if not doc:
        return doc
    doc = {**doc}
    _id = doc.get("_id")
    if _id is not None:
        doc["id"] = str(_id)
        del doc["_id"]
    return doc


@app.get("/")
def root():
    return {"message": "PaprFlow backend running"}


# Health + DB
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Minimal endpoints for MVP app

@app.post("/vendors", response_model=dict)
def create_vendor(vendor: Vendor):
    vid = create_document("vendor", vendor)
    return {"id": vid}


@app.get("/vendors", response_model=List[dict])
def list_vendors(q: Optional[str] = None, limit: int = 50):
    filt = {}
    if q:
        # simple substring search on name
        filt = {"name": {"$regex": q, "$options": "i"}}
    docs = get_documents("vendor", filt, limit)
    return [serialize(d) for d in docs]


class ApprovePayload(BaseModel):
    approved: bool
    comment: Optional[str] = None


@app.post("/invoices", response_model=dict)
def create_invoice(invoice: Invoice):
    iid = create_document("invoice", invoice)
    create_document("activity", Activity(type="upload", actor=None, invoice_id=iid, message="Invoice uploaded"))
    return {"id": iid}


@app.get("/invoices", response_model=List[dict])
def list_invoices(status: Optional[str] = None, vendor_id: Optional[str] = None, limit: int = 50):
    filt = {}
    if status:
        filt["status"] = status
    if vendor_id:
        try:
            filt["vendor_id"] = vendor_id
        except Exception:
            raise HTTPException(400, "Invalid vendor id")
    docs = get_documents("invoice", filt, limit)
    return [serialize(d) for d in docs]


@app.get("/activity", response_model=List[dict])
def get_activity(limit: int = 50):
    docs = get_documents("activity", {}, limit)
    return [serialize(d) for d in docs]


@app.post("/invoices/{invoice_id}/approve", response_model=dict)
def approve_invoice(invoice_id: str, payload: ApprovePayload):
    # Minimal stub: write activity record; full update would normally update invoice doc
    create_document(
        "activity",
        Activity(
            type="approved" if payload.approved else "rejected",
            actor=None,
            invoice_id=invoice_id,
            message=("Approved" if payload.approved else "Rejected") + (f": {payload.comment}" if payload.comment else "")
        )
    )
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
