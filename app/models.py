from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime, timezone
from app import db, login_manager


# ── User ─────────────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, doc):
        self.id           = str(doc["_id"])
        self.display_name = doc.get("display_name", "User")
        self.email        = doc.get("email", "")
        self.password_hash= doc.get("password_hash", "")
        self.is_admin     = doc.get("is_admin", False)
        self.created_at   = doc.get("created_at", datetime.now(timezone.utc))
        self.analysis_count = doc.get("analysis_count", 0)


@login_manager.user_loader
def load_user(user_id):
    doc = db.users.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


def create_user(display_name, email, password_hash, is_admin=False):
    doc = {
        "display_name":   display_name,
        "email":          email,
        "password_hash":  password_hash,
        "is_admin":       is_admin,
        "created_at":     datetime.now(timezone.utc),
        "analysis_count": 0,
    }
    result = db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return User(doc)


def get_user_by_email(email):
    doc = db.users.find_one({"email": email})
    return User(doc) if doc else None


def get_user_by_id(user_id):
    doc = db.users.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


def get_all_users():
    return list(db.users.find().sort("created_at", -1))


def increment_analysis_count(user_id):
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"analysis_count": 1}}
    )


def delete_user_and_data(user_id):
    db.analyses.delete_many({"user_id": ObjectId(user_id)})
    db.users.delete_one({"_id": ObjectId(user_id)})


# ── Analysis ──────────────────────────────────────────────────────────────────

def create_analysis(user_id, file_name, file_size):
    doc = {
        "user_id":      ObjectId(user_id),
        "file_name":    file_name,
        "file_size":    file_size,
        "status":       "processing",
        "summary":      {},
        "ai_result":    {},
        "chart_configs":[],
        "charts_b64":   {},
        "cleaned_rows": [],
        "chat_history": [],
        "created_at":   datetime.now(timezone.utc),
        "updated_at":   datetime.now(timezone.utc),
    }
    result = db.analyses.insert_one(doc)
    return str(result.inserted_id)


def get_analysis(analysis_id, user_id=None):
    query = {"_id": ObjectId(analysis_id)}
    if user_id:
        query["user_id"] = ObjectId(user_id)
    return db.analyses.find_one(query)


def update_analysis(analysis_id, data):
    data["updated_at"] = datetime.now(timezone.utc)
    db.analyses.update_one(
        {"_id": ObjectId(analysis_id)},
        {"$set": data}
    )


def get_user_analyses(user_id):
    return list(
        db.analyses.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .limit(100)
    )


def delete_analysis(analysis_id, user_id):
    db.analyses.delete_one({
        "_id":     ObjectId(analysis_id),
        "user_id": ObjectId(user_id)
    })


def append_chat_message(analysis_id, role, content):
    db.analyses.update_one(
        {"_id": ObjectId(analysis_id)},
        {
            "$push": {"chat_history": {
                "role":      role,
                "content":   content,
                "timestamp": datetime.now(timezone.utc),
            }},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        }
    )


def get_all_analyses_admin():
    return list(db.analyses.find().sort("created_at", -1).limit(200))
