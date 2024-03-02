from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest, Forbidden, UnsupportedMediaType

from app import db, cache
from app.models import User
from app.utils import key_hash, require_admin, require_login


class UserCollection(Resource):
    """Resource for handling user creation. Admins can also get a list of all users."""

    @require_admin
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

        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema(),
                     format_checker=draft7_format_checker)
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

        collection_url = "view/" + url_for("api.usercollection")
        if cache.has(collection_url):
            cache.delete(collection_url)

        return Response(status=201,
                        headers={"Location":
                                 url_for("api.useritem",
                                         user=user)})


class UserItem(Resource):
    """Resource for handling getting, updating and deleting existing user information."""

    @require_login
    @cache.cached(timeout=300)
    def get(self, user, **kwargs):
        """Get an user's information. Requires user authentication
            Input: User id in the address
            Output: Dictionary of all relevant information on the specified user
        """

        if kwargs["login_user_id"] != user.id:
            raise Forbidden

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
    def put(self, user_to_modify, **kwargs):
        """Update user information. Requires user authentication
            Input: User id in the address and json with the fields 'name' and/or 'password'
            Output: Response with a header to the location of the updated user
        """

        if kwargs["login_user_id"] != user_to_modify.id:
            raise Forbidden

        if not request.json:
            raise UnsupportedMediaType

        if "name" in request.json:

            user_with_name = User.query.filter_by(
                name=request.json["name"]).first()

            if user_with_name and user_with_name.id != user_to_modify.id:
                return "User with the same name already exists. No changes were done.", 400

            user_to_modify.name = request.json["name"]

        if "password" in request.json:

            validation_result = User.validate_password(
                request.json["password"])

            if validation_result is not None:
                return validation_result

            user_to_modify.password = key_hash(request.json["password"])

        db.session.commit()

        item_url = "view/" + url_for("api.useritem", user=user_to_modify)
        collection_url = "view/" + url_for("api.usercollection")

        if cache.has(item_url):
            cache.delete(item_url)
        if cache.has(collection_url):
            cache.delete(collection_url)

        return Response(status=200,
                        headers={"Location":
                                 url_for("api.useritem",
                                         user=user_to_modify)})

    @require_login
    def delete(self, user, **kwargs):
        """Delete an user. Requires user authentication
            Input: User id in the address
            Output: 
        """

        if kwargs["login_user_id"] != user.id:
            raise Forbidden

        User.query.filter_by(id=user.id).delete()
        db.session.commit()

        item_url = "view/" + url_for("api.useritem", user=user)
        collection_url = "view/" + url_for("api.usercollection")

        if cache.has(item_url):
            cache.delete(item_url)
        if cache.has(collection_url):
            cache.delete(collection_url)

        return 200
