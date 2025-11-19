import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Doctor, Article, AppointmentRequest, NewsletterSubscriber, SCHEMA_REGISTRY

app = FastAPI(title="Medicinal Cannabis Portal API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Medicinal Cannabis Portal API is running"}


@app.get("/test")
def test_database():
    """Check database connectivity and list available collections"""
    status = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            status["database"] = "✅ Available"
            status["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            status["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                status["collections"] = db.list_collection_names()
                status["database"] = "✅ Connected & Working"
                status["connection_status"] = "Connected"
            except Exception as e:
                status["database"] = f"⚠️ Connected but error: {str(e)[:100]}"
        else:
            status["database"] = "❌ db not initialized"
    except Exception as e:
        status["database"] = f"❌ Error: {str(e)[:100]}"

    return status


# -----------------------------
# Schema discovery (for admin tools)
# -----------------------------
class SchemaField(BaseModel):
    name: str
    type: str

class CollectionSchema(BaseModel):
    collection: str
    fields: List[SchemaField]

@app.get("/schema", response_model=List[CollectionSchema])
def get_schema():
    out: List[CollectionSchema] = []
    for name, model in SCHEMA_REGISTRY.items():
        fields = [SchemaField(name=k, type=str(v.annotation)) for k, v in model.model_fields.items()]
        out.append(CollectionSchema(collection=name.lower(), fields=fields))
    return out


# -----------------------------
# Public content endpoints
# -----------------------------
@app.get("/articles")
def list_articles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    filt = {}
    if q:
        # naive text search across title/summary
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filt["category"] = category
    if tag:
        filt["tags"] = {"$in": [tag]}
    return get_documents("article", filt, limit)


@app.get("/articles/{slug}")
def get_article(slug: str):
    docs = get_documents("article", {"slug": slug}, limit=1)
    if not docs:
        raise HTTPException(status_code=404, detail="Article not found")
    return docs[0]


@app.get("/doctors")
def list_doctors(
    specialty: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    pathology: Optional[str] = None,
    consultation_type: Optional[str] = None,
    price_max: Optional[float] = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    filt = {}
    if specialty:
        filt["specialties"] = {"$in": [specialty]}
    if state:
        filt["states"] = {"$in": [state]}
    if city:
        filt["cities"] = {"$in": [city]}
    if pathology:
        filt["pathologies"] = {"$in": [pathology]}
    if consultation_type:
        filt["consultation_types"] = {"$in": [consultation_type]}
    if price_max is not None:
        filt["price_from"] = {"$lte": price_max}

    return get_documents("doctor", filt, limit)


# -----------------------------
# Lead capture endpoints
# -----------------------------
@app.post("/appointment")
def create_appointment(req: AppointmentRequest):
    doc_id = create_document("appointmentrequest", req)
    return {"status": "ok", "id": doc_id}


@app.post("/newsletter")
def subscribe_newsletter(sub: NewsletterSubscriber):
    doc_id = create_document("newslettersubscriber", sub)
    return {"status": "ok", "id": doc_id}


# -----------------------------
# SEO endpoints
# -----------------------------
@app.get("/sitemap.xml", response_class=PlainTextResponse)
def sitemap():
    base_frontend = os.getenv("FRONTEND_URL", "https://example.com")
    static_paths = ["/", "/articles", "/about", "/press", "/contact", "/privacy", "/terms", "/lgpd"]
    urls = [f"  <url><loc>{base_frontend}{p}</loc></url>" for p in static_paths]
    try:
        articles = get_documents("article", {}, limit=500)
        for a in articles:
            slug = a.get("slug")
            if slug:
                urls.append(f"  <url><loc>{base_frontend}/articles/{slug}</loc></url>")
    except Exception:
        pass
    xml = "\n".join([
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
        *urls,
        "</urlset>",
    ])
    return xml


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    base_frontend = os.getenv("FRONTEND_URL", "https://example.com")
    return f"User-agent: *\nAllow: /\nSitemap: {base_frontend}/sitemap.xml\n"


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
