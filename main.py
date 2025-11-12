import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI(title="Luxe Couture API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Models
# ----------------------------
class Product(BaseModel):
    id: str
    name: str
    price: float
    gender: str = Field(..., description="men|women|unisex")
    category: str
    sizes: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []
    featured: bool = False
    new_arrival: bool = False

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

class NewsletterSignup(BaseModel):
    email: EmailStr

class CartItem(BaseModel):
    id: str
    name: str
    price: float
    size: Optional[str] = None
    quantity: int = 1
    image: Optional[str] = None

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    email: Optional[EmailStr] = None
    shipping_address: Optional[str] = None

# ----------------------------
# Demo dataset (used if DB not configured)
# ----------------------------
SAMPLE_PRODUCTS: List[Product] = [
    Product(
        id="st-laurent-coat",
        name="Wool Cashmere Overcoat",
        price=2490.0,
        gender="men",
        category="outerwear",
        sizes=["S","M","L","XL"],
        images=[
            "https://images.unsplash.com/photo-1516826957135-700dedea698c?q=80&w=1400&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=1400&auto=format&fit=crop"
        ],
        description="Tailored Italian wool-cashmere blend with silk lining.",
        tags=["coat","cashmere","luxury"],
        featured=True
    ),
    Product(
        id="dior-heel-01",
        name="Patent Leather Stiletto",
        price=980.0,
        gender="women",
        category="shoes",
        sizes=["35","36","37","38","39","40"],
        images=[
            "https://images.unsplash.com/photo-1520975922215-c0495a1fd8ec?q=80&w=1400&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1561808843-7c3b1b4e6b8c?q=80&w=1400&auto=format&fit=crop"
        ],
        description="Glossy patent leather with gold accent heel.",
        tags=["heels","gold"],
        featured=True,
        new_arrival=True
    ),
    Product(
        id="gucci-bag-velvet",
        name="Velvet Chain Shoulder Bag",
        price=3150.0,
        gender="women",
        category="bags",
        sizes=[],
        images=[
            "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=1400&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1547949003-9792a18a2601?q=80&w=1400&auto=format&fit=crop"
        ],
        description="Signature velvet with brushed gold chain.",
        tags=["bag","chain","velvet"],
        new_arrival=True
    ),
    Product(
        id="balenciaga-tee",
        name="Logo Cotton T-Shirt",
        price=450.0,
        gender="unisex",
        category="tops",
        sizes=["XS","S","M","L","XL"],
        images=[
            "https://images.unsplash.com/photo-1544441893-675973e31985?q=80&w=1400&auto=format&fit=crop"
        ],
        description="Premium heavyweight cotton with subtle logo print.",
        tags=["t-shirt","cotton"],
    ),
    Product(
        id="ysl-boots-chelsea",
        name="Leather Chelsea Boots",
        price=1290.0,
        gender="men",
        category="shoes",
        sizes=["40","41","42","43","44"],
        images=[
            "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1400&auto=format&fit=crop"
        ],
        description="Polished calfskin with elastic side panels.",
        tags=["boots","leather"],
        featured=True
    ),
]

# Helper: try DB first, fallback to sample

def fetch_products_from_db_or_sample() -> List[Product]:
    try:
        from database import db, get_documents
        if db is not None:
            docs = get_documents("product")
            products: List[Product] = []
            for d in docs:
                d["id"] = str(d.get("_id", d.get("id")))
                products.append(Product(**{k: v for k, v in d.items() if k != "_id"}))
            if products:
                return products
    except Exception:
        pass
    return SAMPLE_PRODUCTS

# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def root():
    return {"name": "Luxe Couture API", "status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/products", response_model=List[Product])
def list_products(
    gender: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
):
    items = fetch_products_from_db_or_sample()

    if gender:
        items = [p for p in items if p.gender.lower() == gender.lower() or (gender == "unisex" and p.gender == "unisex")]
    if category:
        items = [p for p in items if p.category.lower() == category.lower()]
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p.name.lower() or any(ql in t.lower() for t in p.tags)]
    if sort == "price_asc":
        items = sorted(items, key=lambda p: p.price)
    if sort == "price_desc":
        items = sorted(items, key=lambda p: p.price, reverse=True)
    return items

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    items = fetch_products_from_db_or_sample()
    for p in items:
        if p.id == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/featured", response_model=List[Product])
def featured():
    return [p for p in fetch_products_from_db_or_sample() if p.featured]

@app.get("/new-arrivals", response_model=List[Product])
def new_arrivals():
    return [p for p in fetch_products_from_db_or_sample() if p.new_arrival]

@app.post("/newsletter")
def newsletter(signup: NewsletterSignup):
    # In a real app, save to DB or ESP
    return {"ok": True, "email": signup.email, "message": "Subscribed"}

@app.post("/contact")
def contact(msg: ContactMessage):
    # In a real app, persist and/or send email
    return {"ok": True, "received": msg.model_dump(), "message": "We will be in touch"}

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    total = sum(it.price * it.quantity for it in payload.items)
    return {"ok": True, "total": round(total, 2), "message": "Checkout initialized"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
