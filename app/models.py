import click
from flask.cli import with_appcontext

from app import db


GamePlayers = db.Table("GamePlayers",
                       db.Column("gameId", db.Integer, db.ForeignKey(
                           "Game.id", ondelete="SET NULL"), primary_key=True),
                       db.Column("playerId", db.Integer, db.ForeignKey(
                           "User.id", ondelete="SET NULL"), primary_key=True),
                       db.Column("team", db.Integer)
                       )


class GameType(db.Model):
    __tablename__ = "GameType"
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    name = db.Column(db.String(64))
    defaultState = db.Column(db.String(64))


class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    name = db.Column(db.String(64))
    password = db.Column(db.String(64))  # Not encrypted
    turnsPlayed = db.Column(db.Integer, default=0)
    totalTime = db.Column(db.Integer, default=0)

    games = db.relationship(
        "Game", secondary=GamePlayers, back_populates="players")


class Game(db.Model):
    __tablename__ = "Game"
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, autoincrement=True)
    type = db.Column(db.Integer, db.ForeignKey(
        "GameType.id", ondelete="CASCADE"))
    isActive = db.Column(db.Boolean, default=True)
    state = db.Column(db.Text)
    currentPlayer = db.Column(db.Integer, db.ForeignKey(
        "User.id", ondelete="SET NULL"), default=None, nullable=True)
    moveHistory = db.Column(db.Blob, default=None, nullable=True)

    players = db.relationship(
        "User", secondary=GamePlayers, back_populates="games")


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()


@click.command("populate-db")
@with_appcontext
def populate_db_command():
    db.create_all()

    gameType1 = GameType(name="Tictactoe", defaultState="---------")

    user1 = User(name="user1", password="123456789")
    user2 = User(name="user2", password="salasana")
    user3 = User(name="user3", password="aaa")

    game1 = Game(type=gameType1.id, state=gameType1.defaultState,
                 currentPlayer=user1.id)

    db.session.add(gameType1)
    db.session.add_all([user1, user2, user3])
    db.session.add(game1)

    db.session.commit()


@click.command("reset-db")
@with_appcontext
def reset_db_command():
    db.drop_all()
