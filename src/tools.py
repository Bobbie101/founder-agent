import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['founder_agent']
founders = db['founders']
notes = db['notes']
resources = db['resources']

# ─────────────────────────────────────────────
# TOOL 1 — Save a new founder profile
# ─────────────────────────────────────────────
def save_founder(
    name: str,
    idea: str,
    problem: str,
    target_customer: str,
    why_now: str,
    unfair_advantage: str
) -> dict:
    """
    Saves a founder's profile and business idea to MongoDB.
    Call this as soon as a founder shares their name and describes their idea.
    This creates their permanent profile so progress is never lost.

    Args:
        name: The founder's full name
        idea: Their business idea in one clear sentence
        problem: The specific problem their idea solves
        target_customer: Who their ideal customer is
        why_now: Why this idea is relevant right now
        unfair_advantage: What makes them uniquely positioned to build this

    Returns:
        Confirmation the profile was saved with their founder ID
    """
    existing = founders.find_one({"name": name})
    if existing:
        return {
            "status": "already_exists",
            "message": f"Profile already exists for {name}. Use get_founder to retrieve their progress."
        }

    founder_data = {
        "name": name,
        "idea": idea,
        "problem": problem,
        "target_customer": target_customer,
        "why_now": why_now,
        "unfair_advantage": unfair_advantage,
        "idea_documented_at": datetime.now(),
        "investor_score": 0,
        "milestones": {
            "idea_clarity": {"completed": False, "completed_at": None},
            "idea_protected": {"completed": False, "completed_at": None},
            "market_validated": {"completed": False, "completed_at": None},
            "customer_discovery": {"completed": False, "completed_at": None},
            "legal_setup": {"completed": False, "completed_at": None},
            "investor_ready": {"completed": False, "completed_at": None}
        },
        "created_at": datetime.now()
    }

    result = founders.insert_one(founder_data)

    return {
        "status": "saved",
        "founder_id": str(result.inserted_id),
        "message": f"Profile created for {name}! Your idea has been documented and timestamped — this protects you. I'll remember everything from here.",
        "idea_documented_at": founder_data["idea_documented_at"].strftime("%B %d, %Y at %I:%M %p")
    }


# ─────────────────────────────────────────────
# TOOL 2 — Get a returning founder's profile
# ─────────────────────────────────────────────
def get_founder(name: str) -> dict:
    """
    Retrieves a founder's full profile and progress from MongoDB.
    Call this when a founder says they've used this before or want to continue
    where they left off.

    Args:
        name: The founder's name to look up

    Returns:
        Their full profile, milestone progress, and what to work on next
    """
    founder = founders.find_one({"name": name}, sort=[("created_at", -1)])

    if not founder:
        return {
            "status": "not_found",
            "message": f"No profile found for {name}. Let's create one — tell me your business idea!"
        }

    completed = [k for k, v in founder['milestones'].items() if v['completed']]
    remaining = [k for k, v in founder['milestones'].items() if not v['completed']]
    next_step = remaining[0].replace("_", " ").title() if remaining else "All milestones complete!"

    return {
        "status": "found",
        "name": founder['name'],
        "idea": founder['idea'],
        "problem": founder['problem'],
        "target_customer": founder['target_customer'],
        "why_now": founder['why_now'],
        "unfair_advantage": founder['unfair_advantage'],
        "idea_documented_at": founder['idea_documented_at'].strftime("%B %d, %Y"),
        "investor_score": founder['investor_score'],
        "completed_milestones": completed,
        "remaining_milestones": remaining,
        "next_step": next_step,
        "message": f"Welcome back {name}! Your idea has been on record since {founder['idea_documented_at'].strftime('%B %d, %Y')}. You've completed {len(completed)} of 6 milestones. Next up: {next_step}."
    }


# ─────────────────────────────────────────────
# TOOL 3 — Update a milestone as complete
# ─────────────────────────────────────────────
def update_milestone(name: str, milestone: str) -> dict:
    """
    Marks a milestone as complete for a founder in MongoDB.
    Call this when a founder has genuinely completed a step in their journey.

    Available milestones:
    - idea_clarity
    - idea_protected
    - market_validated
    - customer_discovery
    - legal_setup
    - investor_ready

    Args:
        name: The founder's name
        milestone: The milestone name to mark complete

    Returns:
        Confirmation and encouragement with next step
    """
    valid_milestones = [
        "idea_clarity", "idea_protected", "market_validated",
        "customer_discovery", "legal_setup", "investor_ready"
    ]

    if milestone not in valid_milestones:
        return {
            "status": "error",
            "message": f"Invalid milestone. Choose from: {valid_milestones}"
        }

    result = founders.update_one(
        {"name": name},
        {"$set": {
            f"milestones.{milestone}.completed": True,
            f"milestones.{milestone}.completed_at": datetime.now()
        }}
    )

    if result.modified_count == 0:
        return {
            "status": "error",
            "message": f"Could not find founder {name}. Make sure their profile exists first."
        }

    milestone_display = milestone.replace("_", " ").title()

    return {
        "status": "updated",
        "milestone_completed": milestone_display,
        "completed_at": datetime.now().strftime("%B %d, %Y"),
        "message": f"Milestone complete: {milestone_display}! This is real progress. Keep going."
    }


# ─────────────────────────────────────────────
# TOOL 4 — Save a founder's own note
# ─────────────────────────────────────────────
def save_note(name: str, note: str) -> dict:
    """
    Saves a note written by the founder to MongoDB.
    Call this when a founder wants to save a thought, decision, or
    important insight from the conversation.

    Args:
        name: The founder's name
        note: The note content to save

    Returns:
        Confirmation the note was saved with timestamp
    """
    note_data = {
        "founder_name": name,
        "note": note,
        "type": "founder_note",
        "created_at": datetime.now()
    }

    notes.insert_one(note_data)

    return {
        "status": "saved",
        "message": f"Note saved! You can retrieve all your notes anytime.",
        "saved_at": note_data["created_at"].strftime("%B %d, %Y at %I:%M %p")
    }


# ─────────────────────────────────────────────
# TOOL 5 — Agent saves a resource it finds
# ─────────────────────────────────────────────
def save_resource(name: str, title: str, url: str, why_useful: str) -> dict:
    """
    Saves a resource or link the agent found that is useful for the founder.
    Call this automatically whenever you find a genuinely useful article,
    tool, template, or resource during a Google Search.

    Args:
        name: The founder's name
        title: The title of the resource
        url: The URL link to the resource
        why_useful: One sentence explaining why this is useful for them

    Returns:
        Confirmation the resource was saved
    """
    resource_data = {
        "founder_name": name,
        "title": title,
        "url": url,
        "why_useful": why_useful,
        "type": "agent_resource",
        "saved_at": datetime.now()
    }

    resources.insert_one(resource_data)

    return {
        "status": "saved",
        "message": f"Resource saved to your library: {title}",
        "saved_at": resource_data["saved_at"].strftime("%B %d, %Y")
    }


# ─────────────────────────────────────────────
# TOOL 6 — Get all notes and resources
# ─────────────────────────────────────────────
def get_notes_and_resources(name: str) -> dict:
    """
    Retrieves all saved notes and resources for a founder from MongoDB.
    Call this when a founder asks to see their notes, saved resources,
    or wants a summary of what they've collected.

    Args:
        name: The founder's name

    Returns:
        All their saved notes and resources in order
    """
    founder_notes = list(notes.find(
        {"founder_name": name},
        sort=[("created_at", -1)]
    ))

    founder_resources = list(resources.find(
        {"founder_name": name},
        sort=[("saved_at", -1)]
    ))

    formatted_notes = [{
        "note": n["note"],
        "saved_at": n["created_at"].strftime("%B %d, %Y at %I:%M %p")
    } for n in founder_notes]

    formatted_resources = [{
        "title": r["title"],
        "url": r["url"],
        "why_useful": r["why_useful"],
        "saved_at": r["saved_at"].strftime("%B %d, %Y")
    } for r in founder_resources]

    if not formatted_notes and not formatted_resources:
        return {
            "status": "empty",
            "message": f"No notes or resources saved yet for {name}. As we work together I'll save useful resources automatically."
        }

    return {
        "status": "found",
        "total_notes": len(formatted_notes),
        "total_resources": len(formatted_resources),
        "notes": formatted_notes,
        "resources": formatted_resources,
        "message": f"Here's everything saved for {name}: {len(formatted_notes)} notes and {len(formatted_resources)} resources."
    }