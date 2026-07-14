from flask import Flask
from app.database import db
import os
from dotenv import load_dotenv

from flask_jwt_extended import JWTManager

load_dotenv()

def create_app():                                                                                                                
    app = Flask(__name__)                                                                                                        
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(                                                                           
        "DATABASE_URL",                                                                                                          
        "postgresql://amanparmar@localhost/lost_found_db"                                                                        
    )
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")                                                                             
    db.init_app(app)
    JWTManager(app)
    from app.routes.auth import auth_bp                                                                                            
    app.register_blueprint(auth_bp) 
    from app.routes.items import (items_bp)
    app.register_blueprint(items_bp)                                                                                                     
    return app 
