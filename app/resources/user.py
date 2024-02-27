from flask import request, Response, url_for
from flask_restful import Resource
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from jsonschema import validate, ValidationError, draft7_format_checker
from app.utils import require_admin, require_login, key_hash
from app.models import User
from app import db


class UserCollection(Resource):
    """Resource for handling user creation. Admins can also get a list of all users."""

    @require_admin
    def get(self):
        """
        Get a list of all users.
        User passwords not included.
        """

        user_list = []
        users = User.query.all()

        for user in users:

            user_dict = {"id": user.id,
                         "name": user.name}

            user_list.append(user_dict)

        return user_list, 200

    def post(self):
        """Create a new user"""

        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema(),
                     format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if User.query.filter_by(name=request.json["name"]).first():
            return "User with the same name already exists", 409

        user = User(
            name=request.json["name"], password=key_hash(request.json["password"]))

        db.session.add(user)
        db.session.commit()

        return Response(status=201,
                        headers={"Location":
                                 url_for("api.useritem",
                                         user_id=user.id)})


class UserItem(Resource):

    @require_login
    def get(self, user_id):
        """Get an user's information. Requires user authentication"""
        pass

    @require_login
    def put(self, user_id):
        """Update user information. Requires user authentication"""
        pass
