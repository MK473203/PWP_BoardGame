from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest, Forbidden, UnsupportedMediaType

from app import db
from app.models import User
from app.utils import key_hash, require_admin, require_login


class UserCollection(Resource):
    """Resource for handling user creation. Admins can also get a list of all users."""

    @require_admin
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

        return Response(status=201,
                  headers={"Location":
                           url_for("api.useritem",
                                   user_id=user.id)})


class UserItem(Resource):
    """Resource for handling getting, updating and deleting existing user information."""

    @require_login
    def get(self, user_id, **kwargs):
        """Get an user's information. Requires user authentication
            Input: User id in the address
            Output: Dictionary of all relevant information on the specified user
        """

        if kwargs["login_user_id"] != user_id:
            raise Forbidden

        user = User.query.get(user_id)

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
    def put(self, user_id, **kwargs):
        """Update user information. Requires user authentication
            Input: User id in the address and json with the fields 'name' and/or 'password'
            Output: Response with a header to the location of the updated user
        """

        if kwargs["login_user_id"] != user_id:
            raise Forbidden

        if not request.json:
            raise UnsupportedMediaType

        user_to_modify = User.query.get(user_id)

        if "name" in request.json:

            user_with_name = User.query.filter_by(
                name=request.json["name"]).first()

            if user_with_name and user_with_name.id is not user_to_modify.id:
                return "User with the same name already exists. No changes were done.", 400

            user_to_modify.name = request.json["name"]

        if "password" in request.json:

            validation_result = User.validate_password(
                request.json["password"])

            if validation_result is not None:
                return validation_result

            user_to_modify.password = key_hash(request.json["password"])

        db.session.commit()

        return Response(status=200,
                  headers={"Location":
                           url_for("api.useritem",
                                   user_id=user_to_modify.id)})

    @require_login
    def delete(self, user_id, **kwargs):
        """Delete an user. Requires user authentication
            Input: User id in the address
            Output: 
        """

        if kwargs["login_user_id"] != user_id:
            raise Forbidden

        User.query.filter_by(id=user_id).delete()
        db.session.commit()

        return 200
