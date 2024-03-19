"""
Flask resources for interacting with game types
"""

from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from jsonschema.validators import Draft7Validator
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from app import db, cache
from app.models import GameType
from app.utils import require_admin


class GameTypeCollection(Resource):
    """Resource for handling game types."""

    @cache.cached(timeout=0)
    def get(self):
        """
        Get a list of all game types.
        Input:
        Output: List of all game types
        """

        game_type_list = []
        game_types = GameType.query.all()

        for game_type in game_types:

            game_type_dict = {"id": game_type.id,
                              "name": game_type.name,
                              "defaultState": game_type.defaultState}

            game_type_list.append(game_type_dict)

        return game_type_list, 200

    @require_admin
    def post(self):
        """Create a new game type
            Input: json with the fields 'name' and 'defaultState'
            Output: Response with a header to the location of the new game type
        """

        try:
            validate(request.json, GameType.json_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if GameType.query.filter_by(name=request.json["name"]).first():
            return "Game type with the same name already exists", 400

        game_type = GameType(
            name=request.json["name"].lower(), defaultState=request.json["defaultState"])

        db.session.add(game_type)
        db.session.commit()

        collection_url = "view/" + url_for("api.gametypecollection")
        if cache.has(collection_url):
            cache.delete(collection_url)

        return Response(status=201,
                        headers={"Location":
                                 url_for("api.gametypeitem",
                                         game_type=game_type)})


class GameTypeItem(Resource):
    """Resource for handling getting, updating and deleting existing game type information."""

    @cache.cached(timeout=0)
    def get(self, game_type):
        """Get an game type's information
            Input: game type in the address
            Output: Dictionary with all relevant information on the specified game type
        """

        game_type_dict = {
            "id": game_type.id,
            "name": game_type.name,
            "defaultState": game_type.defaultState,
        }

        return game_type_dict, 200

    @require_admin
    def put(self, game_type):
        """Update a game type's information. Requires admin privileges
            Input: Game type in the address and json with the fields 'name' and/or 'defaultState'
            Output: Response with a header to the location of the updated game type
        """

        if "name" in request.json:

            game_type_with_name = GameType.query.filter_by(
                name=request.json["name"]).first()

            if game_type_with_name and game_type_with_name.id != game_type.id:
                return "Game type with the same name already exists. No changes were done.", 400

            game_type.name = request.json["name"].lower()

        if "defaultState" in request.json:
            game_type.defaultState = request.json["defaultState"]

        db.session.commit()

        item_url = "view/" + \
            url_for("api.gametypeitem", game_type=game_type)
        collection_url = "view/" + url_for("api.gametypecollection")

        if cache.has(item_url):
            cache.delete(item_url)
        if cache.has(collection_url):
            cache.delete(collection_url)

        return Response(status=200,
                        headers={"Location":
                                 url_for("api.gametypeitem",
                                         game_type=game_type)})

    @require_admin
    def delete(self, game_type):
        """Delete a game type. Requires admin privileges.
            Input: Game type in the address
            Output: 
        """

        db_game_type = GameType.query.filter_by(id=game_type.id).first()
        db.session.delete(db_game_type)
        db.session.commit()

        item_url = "view/" + url_for("api.gametypeitem", game_type=game_type)
        collection_url = "view/" + url_for("api.gametypecollection")

        if cache.has(item_url):
            cache.delete(item_url)
        if cache.has(collection_url):
            cache.delete(collection_url)

        return 200
