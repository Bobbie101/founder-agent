from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["founder_agent_db"]

def save_founder_profile(founder_id: str, idea: str, industry: str, country: str) -> str:
    """Save a new founder's idea intake to MongoDB."""
    doc = {
        "founder_id": founder_id,
        "idea": idea,
        "industry": industry,
        "country": country,
        "stage": "intake",
        "current_step": 1,
        "created_at": datetime.utcnow()
    }
    db.founders.insert_one(doc)
    return f"Founder profile saved with ID: {founder_id}"

def save_market_research(founder_id: str, summary: str) -> str:
    """Save market validation results to MongoDB."""
    db.market_research.insert_one({
        "founder_id": founder_id,
        "summary": summary,
        "created_at": datetime.utcnow()
    })
    db.founders.update_one(
        {"founder_id": founder_id},
        {"$set": {"current_step": 2, "stage": "market_validated"}}
    )
    return "Market research saved."

def get_founder(founder_id: str) -> dict:
    """Retrieve a founder profile by ID."""
    doc = db.founders.find_one({"founder_id": founder_id})
    if doc:
        doc.pop("_id", None)
    return doc or {}
