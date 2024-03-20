"""
Flask resources for interacting with game types
"""

import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from jsonschema.validators import Draft7Validator
from werkzeug.exceptions import BadRequest

from app import db, cache, delete_cache_entry
from app.models import GameType
from app.utils import MASON, BoardGameBuilder, require_admin


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
            game_type_obj = BoardGameBuilder(
                id=game_type.id,
                name=game_type.name,
                defaultState=game_type.defaultState
            )
            game_type_obj.add_control("self", url_for("api.gametypeitem", game_type=game_type))
            game_type_list.append(game_type_obj)

        body = BoardGameBuilder(items=game_type_list)
        body.add_board_game_namespace()
        body.add_control_all_users()
        body.add_control_all_games()
        body.add_control_add_game_type()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_admin
    def post(self):
        """
        Create a new game type
            Input: json with the fields 'name' and 'defaultState'
            
            Output: Response with a header to the location of the new game type
        """

        try:
            validate(request.json, GameType.post_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if GameType.query.filter_by(name=request.json["name"]).first():
            return "Game type with the same name already exists", 400

        game_type = GameType(
            name=request.json["name"].lower(), defaultState=request.json["defaultState"])

        db.session.add(game_type)
        db.session.commit()

        delete_cache_entry(url_for("api.gametypecollection"))

        return Response(
            status=201,
            headers={"Location":url_for("api.gametypeitem", game_type=game_type)}
        )


class GameTypeItem(Resource):
    """Resource for handling getting, updating and deleting existing game type information."""

    @cache.cached(timeout=0)
    def get(self, game_type):
        """
        Get a game_type's information
            Input: Game_type name in the address
            
            Output: Dictionary with all relevant information on the specified game type
        """

        body = BoardGameBuilder(
            id=game_type.id,
            name=game_type.name,
            defaultState=game_type.defaultState,
        )
        body.add_board_game_namespace()
        body.add_control_all_game_types()
        body.add_control_edit_game_type(game_type)
        body.add_control_delete_game_type(game_type)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_admin
    def put(self, game_type):
        """
        Update a game type's information. Requires admin privileges
            Input: Game_type in the address and json with the fields 'name' and/or 'defaultState'
            
            Output: Response with a header to the location of the updated game type
        """

        try:
            validate(request.json, GameType.put_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if "name" in request.json:

            game_type_with_name = GameType.query.filter_by(
                name=request.json["name"]).first()

            if game_type_with_name and game_type_with_name.id != game_type.id:
                return "Game type with the same name already exists. No changes were done.", 400

            game_type.name = request.json["name"].lower()

        if "defaultState" in request.json:
            game_type.defaultState = request.json["defaultState"]

        db.session.commit()

        delete_cache_entry(url_for("api.gametypecollection"))
        delete_cache_entry(url_for("api.gametypeitem", game_type=game_type))

        return Response(
            status=200,
            headers={"Location": url_for("api.gametypeitem", game_type=game_type)}
        )

    @require_admin
    def delete(self, game_type):
        """
        Delete a game type. Requires admin privileges.
            Input: Game type in the address
            
            Output: 
        """

        db_game_type = GameType.query.filter_by(id=game_type.id).first()
        db.session.delete(db_game_type)
        db.session.commit()

        delete_cache_entry(url_for("api.gametypecollection"))
        delete_cache_entry(url_for("api.gametypeitem", game_type=game_type))

        return 200
