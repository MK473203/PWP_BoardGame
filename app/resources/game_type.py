from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from app import db
from app.models import GameType
from app.utils import require_admin


class GameTypeCollection(Resource):
    """Resource for handling game types."""

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

        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, GameType.json_schema(),
                     format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        game_type = GameType(
            name=request.json["name"].lower(), defaultState=request.json["defaultState"])

        db.session.add(game_type)
        db.session.commit()

        return Response(status=201,
                        headers={"Location":
                                 url_for("api.gametypeitem",
                                         game_type_id=game_type.id)})


class GameTypeItem(Resource):
    """Resource for handling getting, updating and deleting existing game type information."""

    def get(self, game_type_id):
        """Get an game type's information
            Input: game type id in the address
            Output: Dictionary with all relevant information on the specified game type
        """

        game_type = GameType.query.get(game_type_id)

        game_type_dict = {
            "id": game_type.id,
            "name": game_type.name,
            "defaultState": game_type.defaultState,
        }

        return game_type_dict, 200

    @require_admin
    def put(self, game_type_id):
        """Update a game type's information. Requires admin privileges
            Input: Game type id in the address and json with the fields 'name' and/or 'defaultState'
            Output: Response with a header to the location of the updated game type
        """

        if not request.json:
            raise UnsupportedMediaType

        game_type_to_modify = GameType.query.get(game_type_id)

        if "name" in request.json:

            game_type_to_modify.name = request.json["name"].lower()

        if "defaultState" in request.json:
            game_type_to_modify.defaultState = request.json["defaultState"]

        db.session.commit()

        return Response(status=200,
                        headers={"Location":
                                 url_for("api.gametypeitem",
                                         game_type_id=game_type_to_modify.id)})

    @require_admin
    def delete(self, game_type_id):
        """Delete a game type. Requires admin privileges.
            Input: Game type id in the address
            Output: 
        """

        GameType.query.filter_by(id=game_type_id).delete()
        db.session.commit()

        return 200
