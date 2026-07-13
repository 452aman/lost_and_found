from flask import Flask
from app.database import db
import os

from flask_jwt_extended import JWTManager

def create_app():                                                                                                                
    app = Flask(__name__)                                                                                                        
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(                                                                           
        "DATABASE_URL",                                                                                                          
        "postgresql://amanparmar@localhost/lost_found_db"                                                                        
    )
    app.config["JWT_SECRET_KEY"] = "mysecretkey123"                                                                              
    db.init_app(app)
    JWTManager(app)
    from app.routes.auth import auth_bp                                                                                            
    app.register_blueprint(auth_bp) 
    from app.routes.items import (items_bp)
    app.register_blueprint(items_bp)                                                                                                     
    return app 
