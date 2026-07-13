from flask import Blueprint, request, jsonify
from app.models import User
from app.database import db
from app import auth

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get('email')
    password = data.get("password")
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"Error" : "User already registered"}), 400
    hashed_password = auth.hash_password(password)
    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)
    return {"message" : "Account Created"}


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    existing_user = User.query.filter_by(email=email).first()
    if not existing_user:
        return jsonify({"error": "User not found"}), 400
    if not auth.verify_password(password, existing_user.password):
        return jsonify({"Error" : "Wrong Password"}), 400
    token = auth.create_token({"user_id": existing_user.id})
    return jsonify({"access_token" : token})