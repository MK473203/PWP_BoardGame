"""
Utilities and helpers
"""

import hashlib
import secrets

from flask import request, url_for
from werkzeug.exceptions import Forbidden

from app.models import User, Game, GameType


def key_hash(key):
    """Used for api key and user password hashing"""
    return hashlib.sha256(key.encode()).digest()


ADMIN_KEY = "3CK1fq9levikwyj5WxueFdtvDmNlKeiz7zK09erDXg8"
ADMIN_KEY_HASH = key_hash(ADMIN_KEY)

MASON = "application/vnd.mason+json"
PROFILES = "/profiles/"
LINK_RELATIONS = "/link-relations/"

# Change this to the correct address if not localhost:5001
SPECTATE_API_URL = "http://localhost:5001/spectate"

def require_login(func):
    """
    Checks whether the incoming request has the login information of an existing user.

    DOES NOT CHECK WHICH USER IT IS. 
    The user's username and id are supplied to the wrapped function in kwargs.
    These can then be used to do further identification.
    """

    def wrapper(*args, **kwargs):
        hashed_password = key_hash(
            request.headers.get("password", "").strip())
        name = request.headers.get("username", "").strip()

        db_user = User.query.filter_by(name=name).first()

        if name is not None and db_user is not None:
            if secrets.compare_digest(hashed_password, db_user.password):
                kwargs["login_username"] = name
                kwargs["login_user_id"] = db_user.id
                return func(*args, **kwargs)
            raise Forbidden
        raise Forbidden
    return wrapper


def require_admin(func):
    """Checks the incoming request for the admin api key"""

    def wrapper(*args, **kwargs):
        hashed_key = key_hash(
            request.headers.get("Api-key", "").strip())
        if secrets.compare_digest(hashed_key, ADMIN_KEY_HASH):
            return func(*args, **kwargs)
        raise Forbidden
    return wrapper


class BoardGameBuilder(dict):

    """
    Taken from:
    https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py

    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object and ready-made functions for adding boardgame controls.
    """

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_board_game_namespace(self):
        """
        Add the 'boardgame' namespace to the object
        """
        self.add_namespace("boardgame", "/api" + LINK_RELATIONS)

    def add_control_profiles(self, profile):
        """
        Add the 'profile' control to the object
        """
        self.add_control("profile", "/api" + PROFILES + profile + "/")

    def add_control_all_games(self):
        """
        Add the games-all control to the object
        """
        self.add_control("boardgame:games-all",
                         url_for("api.gamecollection"), method="GET")

    def add_control_all_users(self):
        """
        Add the users-all control to the object
        """
        self.add_control("boardgame:users-all",
                         url_for("api.usercollection"), method="GET")

    def add_control_all_game_types(self):
        """
        Add the gametypes-all control to the object
        """
        self.add_control("boardgame:gametypes-all",
                         url_for("api.gametypecollection"), method="GET")

    def add_control_add_game(self):
        """
        Add the add-game control to the object
        """
        self.add_control("boardgame:add-game", url_for("api.gamecollection"), method="POST",
                         encoding="json", schema=Game.post_schema())

    def add_control_add_user(self):
        """
        Add the add-user control to the object
        """
        self.add_control("boardgame:add-user", url_for("api.usercollection"), method="POST",
                         encoding="json", schema=User.json_schema())

    def add_control_add_game_type(self):
        """
        Add the add-gametype control to the object
        """
        self.add_control("boardgame:add-gametype", url_for("api.gametypecollection"), method="POST",
                         encoding="json", schema=GameType.json_schema())

    def add_control_delete_game(self, game):
        """
        Add the GameItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         url_for("api.gameitem", game=game), method="DELETE")

    def add_control_delete_user(self, user):
        """
        Add the UserItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         url_for("api.useritem", user=user), method="DELETE")

    def add_control_delete_game_type(self, game_type):
        """
        Add the GameTypeItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         url_for("api.gametypeitem", game_type=game_type), method="DELETE")

    def add_control_edit_game(self, game):
        """
        Add the GameItem edit control to the object
        """
        self.add_control("edit", url_for("api.gameitem", game=game), method="PUT",
                         encoding="json", schema=Game.put_schema())

    def add_control_edit_user(self, user):
        """
        Add the UserItem edit control to the object
        """
        self.add_control("edit", url_for(
            "api.useritem", user=user), method="PUT", encoding="json", schema=User.json_schema())

    def add_control_edit_game_type(self, game_type):
        """
        Add the GameTypeItem edit control to the object
        """
        self.add_control("edit", url_for("api.gametypeitem", game_type=game_type), method="PUT",
                         encoding="json", schema=GameType.json_schema())

    def add_control_join_game(self, game):
        """
        Add the join-game control to the object
        """
        self.add_control("boardgame:join-game", url_for(
            "api.joingame", game=game), method="POST")

    def add_control_make_move(self, game):
        """
        Add the make-move control to the object
        """
        self.add_control("boardgame:make-move", url_for("api.movecollection", game=game),
                         method="POST", encoding="json", schema=Game.move_schema())
        
    def add_control_spectate(self, game):
        """
        Add the spectate control to the object
        """
        self.add_control("boardgame:spectate", SPECTATE_API_URL + game.uuid,
                         method="GET")
