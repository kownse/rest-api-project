import os
import requests

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import or_

from db import db
from blocklist import BLOCKLIST
from models import UserModel
from schemas import UserSchema, UserRegisterSchema

blp = Blueprint("users", __name__, description="Operations on users")

def send_simple_message(to, subject, body):
    domain = os.getenv('MAILGUN_DOMAIN', 'sandbox2300fb912b5548369c86d173d52974c3.mailgun.org')
    return requests.post(
  		f"https://api.mailgun.net/v3/{domain}/messages",
  		auth=("api", os.getenv('MAILGUN_API_KEY', 'f181fd16760bf4ccdd061e9c3f17219b-623424ea-4eff06ac')),
  		data={"from": "Yunfei Duan <postmaster@sandbox2300fb912b5548369c86d173d52974c3.mailgun.org>",
			"to": [to],
  			"subject": subject,
  			"text": body})

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
        if UserModel.query.filter_by(
            or_(
                username=user_data['username'],
                email=user_data['email']
            )
        ).first():
            abort(409, message="User already exists")

        user = UserModel(
            username=user_data['username'],
            password=pbkdf2_sha256.hash(user_data['password']),
            email=user_data['email']
        )

        db.session.add(user)
        db.session.commit()

        send_simple_message(
            to=user.email,
            subject="Successfully signed up",
            body=f"Hi {user.username}! You have successfully signed up to our service."
        )

        return {"message": "User created successfully."}, 201
    
@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter_by(username=user_data['username']).first()

        if user and pbkdf2_sha256.verify(user_data['password'], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        abort(401, message="Invalid credentials")

@blp.route("/refresh")
class UserRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user, fresh=False)
        # jti = get_jwt()['jti']
        # BLOCKLIST.add(jti)
        return {"access_token": access_token}, 200

@blp.route("/user/<int:user_id>")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    @jwt_required()
    @blp.response(202, description="Deletes a user.")
    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}, 200