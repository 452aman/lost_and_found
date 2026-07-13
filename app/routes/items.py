from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Item
from app.database import db

items_bp = Blueprint("items", __name__)

@items_bp.route("/items", methods=["POST"])
@jwt_required()
def create_item():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    category = data.get("category")
    status = data.get("status")
    location = data.get("location")
    new_item = Item(title=title, description=description, category=category, status=status, location=location, user_id=user_id)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Item added successfully"})

@items_bp.route("/items", methods=["GET"])
@jwt_required()
def get_items():
    user_id = int(get_jwt_identity())
    items = Item.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": i.id, "title": i.title, "category": i.category, "status": i.status, "location": i.location} for i in items])

@items_bp.route("/items/<int:item_id>", methods=["GET"])
@jwt_required()
def get_item(item_id):
    user_id = int(get_jwt_identity())
    item = Item.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"id": item.id, "title": item.title, "description": item.description, "category": item.category, "status": item.status, "location": item.location, "is_resolved": item.is_resolved})

@items_bp.route("/items/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_item(item_id):
    user_id = int(get_jwt_identity())
    item = Item.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    data = request.get_json()
    item.title = data.get("title", item.title)
    item.description = data.get("description", item.description)
    item.category = data.get("category", item.category)
    item.status = data.get("status", item.status)
    item.location = data.get("location", item.location)
    db.session.commit()
    return jsonify({"message": "Item updated successfully"})

@items_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    user_id = int(get_jwt_identity())
    item = Item.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully"})

@items_bp.route("/items/<int:item_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_item(item_id):
    user_id = int(get_jwt_identity())
    item = Item.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    item.is_resolved = True
    db.session.commit()
    return jsonify({"message": "Item marked as resolved"})
