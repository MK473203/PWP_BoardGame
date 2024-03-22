import pytest
import json

from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

from app import create_app, db
from app.models import User, Game, GameType
from app.utils import ADMIN_KEY, key_hash

TEST_KEY = "verysafetestkey"

class AuthHeaderClient(FlaskClient):
    """
    Flask testing client that will add
    applicable user login information and the admin api key
    to the client's request headers
    """

    def open(self, *args, **kwargs):
        headers = kwargs.pop('headers', Headers())

        if "Api-key" not in headers:
            headers.extend(Headers({"Api-key": ADMIN_KEY}))
        if "username" not in headers:
            headers.extend(Headers({"username": "testuser_1"}))
        if "password" not in headers:
            headers.extend(Headers({"password": "password1"}))

        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


@pytest.fixture
def client():
    """Pytest fixture for creating the flask app and populating the database"""

    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        _populate_db()

    app.test_client_class = AuthHeaderClient
    yield app.test_client()


@pytest.fixture
def game_url(client):
    body = json.loads(client.get("/api/games/").data)
    yield body["items"][0]["@controls"]["self"]["href"]


def _populate_db():
    """
    Helper function for populating the database
    with game users, game types and games
    """
    
    db.create_all()

    tictactoe = GameType(name="tictactoe", defaultState="1---------")
    tictactoe2 = GameType(name="tictactoe2", defaultState="1---------")
    db.session.add(tictactoe)
    db.session.add(tictactoe2)

    for i in range(1, 4):
        u = User(
            name="testuser_{}".format(i),
            password=key_hash("password{}".format(i))
        )
        db.session.add(u)

    db.session.commit()

    user_1 = User.query.filter_by(name="testuser_1").first()

    game = Game(type=tictactoe.id,
                state=tictactoe.defaultState,
                currentPlayer=user_1.id)
    db.session.add(game)

    game2 = Game(type=tictactoe.id,
                 state=tictactoe.defaultState, players=[user_1])
    db.session.add(game2)

    game3 = Game(type=tictactoe.id,
                 state=tictactoe.defaultState)
    db.session.add(game3)
    db.session.commit()
