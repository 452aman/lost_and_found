from flask_jwt_extended import create_access_token
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password : str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):                                                                          
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict):                                                                                                    
    return create_access_token(identity=str(data["user_id"]))



