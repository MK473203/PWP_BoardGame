"""
Flask resources for interacting with user information
"""

from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from jsonschema.validators import Draft7Validator
from werkzeug.exceptions import BadRequest, Forbidden

from app import db, cache, delete_cache_entry
from app.models import User
from app.utils import key_hash, require_login


class UserCollection(Resource):
    """Resource for handling user creation. Admins can also get a list of all users."""

    @cache.cached(timeout=900)
    def get(self):
        """
        Get a list of all users.
        User passwords not included.
        Input:
        Output: A list of all users
        """

        user_list = []
        users = User.query.all()

        for user in users:
            user_dict = {"id": user.id,
                         "name": user.name}
            user_list.append(user_dict)

        return user_list, 200

    def post(self):
        """Create a new user
            Input:Json with the fields 'name' and 'password'
            Output: Response with a header to the location of the new user
        """

        try:
            validate(request.json, User.post_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if User.query.filter_by(name=request.json["name"]).first():
            return "User with the same name already exists", 400

        validation_result = User.validate_password(
            request.json["password"])

        if validation_result is not None:
            return validation_result

        user = User(
            name=request.json["name"], password=key_hash(request.json["password"]))

        db.session.add(user)
        db.session.commit()

        delete_cache_entry(url_for("api.usercollection"))

        return Response(status=201,
                        headers={"Location":
                                 url_for("api.useritem",
                                         user=user)})


class UserItem(Resource):
    """Resource for handling getting, updating and deleting existing user information."""

    @require_login
    @cache.cached(timeout=300)
    def get(self, user, **kwargs):
        """Get an user's information. Requires an user to be logged in.
            Input: User id in the address
            Output: Dictionary of all relevant information on the specified user
        """

        game_list = []

        for game in user.games:
            game_list.append({"id": game.id,
                              "type": game.type,
                              "result": game.result})

        user_dict = {
            "id": user.id,
            "name": user.name,
            "turnsPlayed": user.turnsPlayed,
            "totalTime": user.totalTime,
            "games": game_list
        }

        return user_dict, 200

    @require_login
    def put(self, user, **kwargs):
        """Update user information. Requires user authentication
            Input: User id in the address and json with the fields 'name' and/or 'password'
            Output: Response with a header to the location of the updated user
        """

        if kwargs["login_user_id"] != user.id:
            raise Forbidden

        try:
            validate(request.json, User.put_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if "name" in request.json:

            user_with_name = User.query.filter_by(
                name=request.json["name"]).first()

            if user_with_name and user_with_name.id != user.id:
                return "User with the same name already exists. No changes were done.", 400

            user.name = request.json["name"]

        if "password" in request.json:

            validation_result = User.validate_password(
                request.json["password"])

            if validation_result is not None:
                return validation_result

            user.password = key_hash(request.json["password"])

        db.session.commit()

        delete_cache_entry(url_for("api.usercollection"))
        delete_cache_entry(url_for("api.useritem", user=user))

        return Response(status=200,
                        headers={"Location":
                                 url_for("api.useritem",
                                         user=user)})

    @require_login
    def delete(self, user, **kwargs):
        """Delete an user. Requires user authentication
            Input: User id in the address
            Output: 
        """

        if kwargs["login_user_id"] != user.id:
            raise Forbidden

        db_user = User.query.filter_by(id=user.id).first()
        db.session.delete(db_user)
        db.session.commit()

        delete_cache_entry(url_for("api.usercollection"))
        delete_cache_entry(url_for("api.useritem", user=user))

        return 200
