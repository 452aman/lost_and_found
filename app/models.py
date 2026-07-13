from app.database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    phone = db.Column(db.String)

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    category = db.Column(db.String)
    status = db.Column(db.String)
    location = db.Column(db.String)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)    
    is_resolved = db.Column(db.Boolean, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

