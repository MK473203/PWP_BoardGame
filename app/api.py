"""
API 👍
"""

import json
from flask import Blueprint, Response
from flask_restful import Api

from app.resources.game import GameCollection, GameItem, RandomGame
from app.resources.game_type import GameTypeCollection, GameTypeItem
from app.resources.user import UserCollection, UserItem
from app.utils import BoardGameBuilder, MASON

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

@api_bp.route("/")
def entrypoint():
    """ Entrypoint into the API. """
    body = BoardGameBuilder()
    body.add_board_game_namespace()
    body.add_control_all_game_types()
    body.add_control_all_users()
    return Response(json.dumps(body), 200, mimetype=MASON)

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>")

api.add_resource(GameCollection, "/games/")
api.add_resource(RandomGame, "/games/random/<game_type:game_type>")
api.add_resource(GameItem, "/games/<int:game_id>")

api.add_resource(GameTypeCollection, "/game_types/")
api.add_resource(GameTypeItem, "/game_types/<game_type:game_type>")
