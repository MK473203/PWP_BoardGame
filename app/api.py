"""
API 👍
"""

import json
from flask import Blueprint, Response, send_from_directory
from flask_restful import Api

from app.resources.game import GameCollection, GameItem, RandomGame, MoveCollection, JoinGame
from app.resources.game_type import GameTypeCollection, GameTypeItem
from app.resources.user import UserCollection, UserItem
from app.utils import BoardGameBuilder, MASON, PROFILES, LINK_RELATIONS

api_bp = Blueprint("api", __name__, url_prefix="/api", static_folder="static")
api = Api(api_bp)


@api_bp.route("/")
def entrypoint():
    """ Entrypoint into the API. """
    body = BoardGameBuilder()
    body.add_board_game_namespace()
    body.add_control_all_games()
    body.add_control_all_game_types()
    body.add_control_all_users()
    return Response(json.dumps(body), 200, mimetype=MASON)


@api_bp.route(PROFILES)
@api_bp.route(PROFILES + "<resource>/")
def send_profile_html(resource=""):
    return send_from_directory(api_bp.static_folder, "profiles.html")


@api_bp.route(LINK_RELATIONS)
def send_link_relation_html():
    return send_from_directory(api_bp.static_folder, "link-relations.html")


api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>")

api.add_resource(GameCollection, "/games/")
api.add_resource(GameItem, "/games/<game:game>")
api.add_resource(MoveCollection, "/games/<game:game>/moves")
api.add_resource(JoinGame, "/games/<game:game>/join")
api.add_resource(RandomGame, "/games/random/<game_type:game_type>")

api.add_resource(GameTypeCollection, "/game_types/")
api.add_resource(GameTypeItem, "/game_types/<game_type:game_type>")
