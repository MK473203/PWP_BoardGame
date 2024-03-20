"""
SQLAlchemy models
"""

import os

import click
from flask import current_app
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from app import db
from app.utils import key_hash

GamePlayers = db.Table("GamePlayers",
    db.Column("gameId", db.Integer,
              db.ForeignKey("Game.id", ondelete="CASCADE"), primary_key=True),
    db.Column("playerId", db.Integer,
              db.ForeignKey("User.id", ondelete="CASCADE"), primary_key=True),
    db.Column("team", db.Integer)
)


class GameTypeConverter(BaseConverter):
    """Class for converting game type names to python objects and vice versa"""

    def to_python(self, value):
        db_game_type = GameType.query.filter_by(name=value).first()
        if db_game_type is None:
            raise NotFound
        return db_game_type

    def to_url(self, value):
        return value.name


class UserConverter(BaseConverter):
    """Class for converting user names to python objects and vice versa"""

    def to_python(self, value):
        db_user = User.query.filter_by(name=value).first()
        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, value):
        return value.name


class GameType(db.Model):
    """SQLAlchemy model class for game types"""
    __tablename__ = "GameType"

    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)
    defaultState = db.Column(db.String(256))

    @staticmethod
    def post_schema():
        """JSON schema for creating a game type"""
        schema = {
            "type": "object",
            "required": ["name", "defaultState"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        }
        props["defaultState"] = {
            "type": "string",
            "maxLength": 256
        }
        return schema

    @staticmethod
    def put_schema():
        """JSON schema for modifying a game type's information"""
        schema = {
            "type": "object",
            "anyOf": [{"required": ["name"]},
                      {"required": ["defaultState"]}]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        }
        props["defaultState"] = {
            "type": "string",
            "maxLength": 256
        }
        return schema


class User(db.Model):
    """SQLAlchemy model class for users"""
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))
    turnsPlayed = db.Column(db.Integer, default=0)
    totalTime = db.Column(db.Integer, default=0)

    games = db.relationship(
        "Game", secondary=GamePlayers, back_populates="players")

    @staticmethod
    def post_schema():
        """JSON schema for creating an user"""
        schema = {
            "type": "object",
            "required": ["name", "password"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        }
        props["password"] = {
            "type": "string"
        }
        return schema

    @staticmethod
    def put_schema():
        """JSON schema for modifying an user's information"""
        schema = {
            "type": "object",
            "anyOf": [{"required": ["name"]},
                      {"required": ["password"]}]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        }
        props["password"] = {
            "type": "string"
        }
        return schema

    @staticmethod
    def validate_password(password):
        """
        Check that a given password fulfills the following requirements:
            - 3-64 characters
            - At least one number
        """
        if not 3 <= len(password) <= 64:
            return "Password must have 3-64 characters.", 400

        if not any(char.isdigit() for char in password):
            return "Password must include at least one number.", 400

        return None


class Game(db.Model):
    """SQLAlchemy model class for game instances"""
    __tablename__ = "Game"

    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    type = db.Column(db.Integer, db.ForeignKey(
        "GameType.id", ondelete="CASCADE"))
    state = db.Column(db.Text)
    result = db.Column(db.Integer, default=-1)
    currentPlayer = db.Column(db.Integer, db.ForeignKey(
        "User.id", ondelete="SET NULL"), default=None, nullable=True)
    moveHistory = db.Column(db.BLOB, default=None, nullable=True)

    players = db.relationship(
        "User", secondary=GamePlayers, back_populates="games")

    @staticmethod
    def post_schema():
        """JSON schema for creating a game instance"""
        schema = {
            "type": "object",
            "required": ["type", "user"]
        }
        props = schema["properties"] = {}
        props["type"] = {
            "type": "string"
        }
        props["user"] = {
            "type": "string"
        }
        return schema

    @staticmethod
    def move_schema():
        """JSON schema for making a move in a game"""
        schema = {
            "type": "object",
            "required": ["move", "moveTime"]
        }
        props = schema["properties"] = {}
        props["moveTime"] = {
            "type": "integer"
        }
        return schema

    @staticmethod
    def admin_schema():
        """JSON schema for making admin privileged modifications"""
        schema = {
            "type": "object",
            "anyOf": [{"required": ["currentPlayer"]}]
        }
        props = schema["properties"] = {}
        props["currentPlayer"] = {
            "type": "integer",
            "enum": [row[0] for row in db.session.query(User.id).all()] + [None]
        }
        return schema


@click.command("init-db")
def init_db_command():
    """
    Initializes an empty database file.

    Usage: flask init-db
    """

    if os.path.isfile(current_app.config["SQLALCHEMY_DATABASE_URI"][10:]):
        click.confirm(
            "There already is an existing .db file. Do you want to delete it?", abort=True)
        os.remove(current_app.config["SQLALCHEMY_DATABASE_URI"][10:])

    db.create_all()


@click.command("populate-db")
def populate_db_command():
    """
    Initializes a small example database.

    Usage: flask populate-db
    """

    if os.path.isfile(current_app.config["SQLALCHEMY_DATABASE_URI"][10:]):
        click.confirm(
            "There already is an existing .db file. Do you want to delete it?", abort=True)
        os.remove(current_app.config["SQLALCHEMY_DATABASE_URI"][10:])

    db.create_all()

    game_type_1 = GameType(name="tictactoe", defaultState="1---------")
    db.session.add(game_type_1)
    db.session.commit()

    user1 = User(name="user1", password=key_hash("123456789"))
    user2 = User(name="user2", password=key_hash("salasana1"))
    user3 = User(name="user3", password=key_hash("aaa123"))
    db.session.add_all([user1, user2, user3])
    db.session.commit()

    game1 = Game(type=game_type_1.id, state=game_type_1.defaultState,
                 currentPlayer=user1.id)

    db.session.add(game1)
    db.session.commit()

    insert = GamePlayers.insert().values(
        gameId=game1.id, playerId=user1.id, team=None)

    db.session.execute(insert)
    db.session.commit()
