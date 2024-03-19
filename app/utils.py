"""
Utilities and helpers
"""

import hashlib
import secrets

from flask import request
from werkzeug.exceptions import Forbidden

from app.models import User, Game, GameType
from app.api import api

from app.resources.game import GameCollection, GameItem
from app.resources.game_type import GameTypeCollection, GameTypeItem
from app.resources.user import UserCollection, UserItem

def key_hash(key):
    """Used for api key and user password hashing"""
    return hashlib.sha256(key.encode()).digest()

ADMIN_KEY = "3CK1fq9levikwyj5WxueFdtvDmNlKeiz7zK09erDXg8"
ADMIN_KEY_HASH = key_hash(ADMIN_KEY)

MASON = "application/vnd.mason+json"
LINK_RELATIONS = "/boardgame/"


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
            request.headers.get("Api_key", "").strip())
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

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

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
        self.add_namespace("boardgame", LINK_RELATIONS)

    def add_control_all_games(self):
        """
        Add the games-all control to the object
        """
        self.add_control("boardgame:games-all",
                         api.url_for(GameCollection), method="GET")

    def add_control_all_users(self):
        """
        Add the users-all control to the object
        """
        self.add_control("boardgame:users-all",
                         api.url_for(UserCollection), method="GET")

    def add_control_all_game_types(self):
        """
        Add the gametypes-all control to the object
        """
        self.add_control("boardgame:gametypes-all", api.url_for(GameTypeCollection), method="GET")

    def add_control_add_game(self):
        """
        Add the add-game control to the object
        """
        self.add_control("boardgame:add-game", api.url_for(GameCollection), method="POST",
                         encoding="json", schema=Game.json_schema())

    def add_control_add_user(self):
        """
        Add the add-user control to the object
        """
        self.add_control("boardgame:add-user", api.url_for(UserCollection), method="POST",
                         encoding="json", schema=User.json_schema())

    def add_control_add_game_type(self):
        """
        Add the add-gametype control to the object
        """
        self.add_control("boardgame:add-gametype", api.url_for(GameTypeCollection), method="POST",
                         encoding="json", schema=GameType.json_schema())

    def add_control_delete_game(self, game_id):
        """
        Add the GameItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         api.url_for(GameItem, game_id=game_id), method="DELETE")

    def add_control_delete_user(self, user):
        """
        Add the UserItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         api.url_for(UserItem, user=user), method="DELETE")

    def add_control_delete_game_type(self, game_type):
        """
        Add the GameTypeItem delete control to the object
        """
        self.add_control("boardgame:delete",
                         api.url_for(GameTypeItem, game_type=game_type), method="DELETE")

    def add_control_edit_game(self, game_id):
        """
        Add the GameItem edit control to the object
        """
        self.add_control("edit", api.url_for(GameItem, game_id=game_id), method="PUT",
                         encoding="json", schema=Game.admin_schema())

    def add_control_edit_user(self, user):
        """
        Add the UserItem edit control to the object
        """
        self.add_control("edit", api.url_for(UserItem, user=user), method="PUT", encoding="json")

    def add_control_edit_game_type(self, game_type):
        """
        Add the GameTypeItem edit control to the object
        """
        self.add_control("edit", api.url_for(GameTypeItem, game_type=game_type), method="PUT",
                         encoding="json")

    def add_control_make_move(self, game_id):
        """
        Add the make-move control to the object
        """
        self.add_control("boardgame:make-move", api.url_for(GameItem, game_id=game_id),
                         method="PUT", encoding="json", schema=Game.move_schema())
