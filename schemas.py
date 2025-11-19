"""
Database Schemas for Medicinal Cannabis Portal

Each Pydantic model maps to a MongoDB collection (lowercased class name).
These models are used for validating input and documenting the data layer.
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List
from datetime import datetime

# -----------------------------
# Core domain models (collections)
# -----------------------------

class Doctor(BaseModel):
    """
    Prescribing physicians directory
    Collection: "doctor"
    """
    name: str = Field(..., description="Doctor full name")
    crm: Optional[str] = Field(None, description="Medical license / CRM")
    photo_url: Optional[HttpUrl] = Field(None, description="Profile photo URL")
    specialties: List[str] = Field(default_factory=list, description="Medical specialties")
    pathologies: List[str] = Field(default_factory=list, description="Conditions treated")
    consultation_types: List[str] = Field(default_factory=list, description="telemedicine | in-person")
    price_from: Optional[float] = Field(None, ge=0, description="Starting consultation price (BRL)")
    states: List[str] = Field(default_factory=list, description="States where operates")
    cities: List[str] = Field(default_factory=list, description="Cities served")
    clinic_name: Optional[str] = Field(None, description="Clinic/Institution name")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    education: Optional[str] = Field(None, description="Education and specializations")
    bio: Optional[str] = Field(None, description="Short biography")
    whatsapp: Optional[str] = Field(None, description="WhatsApp number")
    email: Optional[EmailStr] = Field(None, description="Contact email")


class Article(BaseModel):
    """
    Editorial content (news, guides, research)
    Collection: "article"
    """
    title: str
    slug: str = Field(..., description="SEO-friendly slug")
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = Field(None, description="e.g., Treatments, Research, Regulation, Patient Cases")
    tags: List[str] = Field(default_factory=list)
    cover_image: Optional[HttpUrl] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    related_slugs: List[str] = Field(default_factory=list)


class AppointmentRequest(BaseModel):
    """
    Pre-scheduling requests from patients
    Collection: "appointmentrequest"
    """
    patient_name: str
    email: EmailStr
    phone: str
    pathology: str
    consultation_type: Optional[str] = Field(None, description="telemedicine | in-person")
    preferred_dates: List[str] = Field(default_factory=list)
    state: Optional[str] = None
    city: Optional[str] = None
    doctor_id: Optional[str] = Field(None, description="Target doctor ObjectId as string")
    notes: Optional[str] = None


class NewsletterSubscriber(BaseModel):
    """
    Newsletter subscribers and interest segmentation
    Collection: "newslettersubscriber"
    """
    email: EmailStr
    interests: List[str] = Field(default_factory=list, description="e.g., Treatments, Research, Doctors, Events")


# Convenience export for /schema endpoint
SCHEMA_REGISTRY = {
    "Doctor": Doctor,
    "Article": Article,
    "AppointmentRequest": AppointmentRequest,
    "NewsletterSubscriber": NewsletterSubscriber,
}
