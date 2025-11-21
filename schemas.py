"""
Database Schemas for PaprFlow

Each Pydantic model maps to a MongoDB collection with the lowercase class name.
Example: class Vendor -> collection "vendor"
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Core domain models

class Vendor(BaseModel):
    name: str = Field(..., description="Vendor display name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    tin: Optional[str] = Field(None, description="Tax Identification Number")
    address: Optional[str] = Field(None, description="Street address")
    flagged: bool = Field(False, description="Risk/compliance flag")

class LineItem(BaseModel):
    description: str
    quantity: float = Field(1, ge=0)
    unit_price: float = Field(0, ge=0)
    total: float = Field(0, ge=0)

class Invoice(BaseModel):
    number: Optional[str] = Field(None, description="Invoice number")
    vendor_id: Optional[str] = Field(None, description="Reference to vendor _id string")
    vendor_name: Optional[str] = None
    date: Optional[datetime] = None
    currency: str = Field("GHS", description="Currency code")
    subtotal: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    line_items: List[LineItem] = Field(default_factory=list)

    # OCR + processing
    source_type: Literal["scan","upload"] = "upload"
    source_uri: Optional[str] = Field(None, description="Where the file is stored")
    ocr_status: Literal["queued","processing","done","failed"] = "queued"
    confidence: Optional[float] = Field(None, ge=0, le=1)
    field_confidence: Optional[dict] = Field(default_factory=dict)

    # Workflow
    status: Literal["draft","needs_review","pending_approval","approved","rejected"] = "needs_review"
    assigned_to: Optional[str] = None
    approved_by: Optional[str] = None
    approval_comment: Optional[str] = None

class Activity(BaseModel):
    type: Literal["upload","ocr_complete","approved","rejected","assigned","comment","rule_trigger"]
    actor: Optional[str] = Field(None, description="User performing the action")
    invoice_id: Optional[str] = None
    vendor_id: Optional[str] = None
    message: str

class Rule(BaseModel):
    name: str
    if_field: Literal["total","vendor","currency"] = "total"
    operator: Literal[">","<","=","!=",">=","<=","contains"] = ">"
    value: str = Field(..., description="Comparison value in string form")
    then_action: Literal["require_supervisor","auto_approve","flag_vendor","notify"] = "require_supervisor"
    active: bool = True

class User(BaseModel):
    name: str
    email: EmailStr
    role: Literal["admin","supervisor","staff"] = "staff"
    is_active: bool = True
