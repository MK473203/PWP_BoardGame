from flask import Blueprint
from flask_restful import Api

from app.resources.user import UserCollection, UserItem
from app.resources.game import GameCollection, GameItem, RandomGame

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Routing luonnos. Muuttakaa jos keksitte jotain parempaa.
api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<int:user_id>")

api.add_resource(GameCollection, "/games/")
api.add_resource(RandomGame, "/games/random/<int:type>")
api.add_resource(GameItem, "/games/<int:game_id>")
