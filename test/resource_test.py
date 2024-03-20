import json
import pytest
from flask.testing import FlaskClient
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.datastructures import Headers

from app import create_app, db
from app.models import User, Game, GameType, key_hash
from app.utils import ADMIN_KEY

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


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    """Enable foreign keys in sqlite"""

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def client():
    """Pytest fixture for creating the flask app and populating the database"""

    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_db()

    app.test_client_class = AuthHeaderClient
    yield app.test_client()


def _populate_db():
    """
    Helper function for populating the database
    with game users, game types and games
    """

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

    game = Game(type=tictactoe.id, state=tictactoe.defaultState,
                currentPlayer=user_1.id)
    db.session.add(game)

    game2 = Game(type=tictactoe.id,
                 state=tictactoe.defaultState, players=[user_1])
    db.session.add(game2)

    game3 = Game(type=tictactoe.id,
                 state=tictactoe.defaultState)
    db.session.add(game3)
    db.session.commit()


def _get_user_json(number=1):
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """

    return {"name": "extra-user-{}".format(number), "password": "pass10{}".format(number)}


def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200


def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


def _check_control_put_method(ctrl, client, obj):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_user_json()
    body["name"] = obj["name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204


def _check_control_post_method(ctrl, client, obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_user_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201


class TestUserCollection():
    """Tests for the /api/users/ endpoint"""

    RESOURCE_URL = "/api/users/"
    VALID_USER_DATA = {
        "name": "test-user-5",
        "password": "password1"
    }
    INVALID_USER_DATA = {
        "name": "test-user-x"
    }
    INVALID_USER_DATA_PW1 = {
        "name": "test-user-y",
        "password": "a"
    }
    INVALID_USER_DATA_PW2 = {
        "name": "test-user-z",
        "password": "salasana"
    }

    def test_get(self, client):
        "Test UserCollection GET"

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        # check if response contains a list of users
        assert isinstance(body, list)
        assert len(body) > 0
        # check if each user has 'id' and 'name' fields
        for user in body:
            assert 'id' in user
            assert 'name' in user

    def test_post(self, client):
        "Test UserCollection POST"

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson",
                           headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # test with invalid user data: Missing password field
        resp = client.post(self.RESOURCE_URL, json=self.INVALID_USER_DATA)
        assert resp.status_code == 400

        # test with invalid user data: Password too short
        resp = client.post(self.RESOURCE_URL, json=self.INVALID_USER_DATA_PW1)
        assert resp.status_code == 400

        # test with invalid user data: Password missing number
        resp = client.post(self.RESOURCE_URL, json=self.INVALID_USER_DATA_PW2)
        assert resp.status_code == 400

        # test with valid user data
        resp = client.post(self.RESOURCE_URL, json=self.VALID_USER_DATA)
        assert resp.status_code == 201
        assert resp.headers["Location"] == "/api/users/test-user-5"
        # check if the user is created
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert self.VALID_USER_DATA["name"] in [user["name"] for user in body]

        # Try creating an user with the same information
        resp = client.post(self.RESOURCE_URL, json=self.VALID_USER_DATA)
        assert resp.status_code == 400


class TestUserItem():
    """Tests for the /api/users/<user:user>/ endpoint"""

    RESOURCE_URL = "/api/users/testuser_1"
    RESOURCE_URL_2 = "/api/users/testuser_2"
    INVALID_URL = "/api/users/x"

    def test_get(self, client):
        "Test UserItem GET"

        # Test wrong password
        resp = client.get(self.RESOURCE_URL, headers=Headers(
            {"password": "wrongpassword2"}))
        assert resp.status_code == 403

        # Test non-existent user
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

        # Test with correct authorization
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == 1
        assert body["name"] == "testuser_1"
        assert body["turnsPlayed"] == 0
        assert body["totalTime"] == 0
        assert body["games"] == [{'id': 2, 'type': 1, 'result': -1}]

    def test_put(self, client):
        "Test UserItem PUT"

        valid = _get_user_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        resp = client.put(self.RESOURCE_URL, json=valid, headers=Headers(
            {"username": "testuser_2", "password": "password2"}))
        assert resp.status_code == 403

        # test with another users's name
        valid["name"] = "testuser_2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # Test with invalid password
        valid["name"] = "cool_name"
        valid["password"] = "a"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test with valid
        valid["password"] = "cool_password1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 200

    def test_delete(self, client):
        "Test UserItem DELETE"

        # Unauthorized user
        resp = client.delete(self.RESOURCE_URL, headers=Headers(
            {"username": "testuser_2", "password": "password2"}))
        assert resp.status_code == 403

        # User should be deleted successfully
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 200

        # Trying to delete the same user should lead to 404
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

        # Trying to delete an user we're not logged in as should be forbidden
        resp = client.delete(self.RESOURCE_URL_2)
        assert resp.status_code == 403

        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestGameTypeCollection():
    """Tests for the /api/game_types/ endpoint"""

    RESOURCE_URL = "/api/game_types/"

    TICTACTOE_GAME_TYPE_DATA = {
        "name": "tictactoe",
        "defaultState": "1---------"
    }

    VALID_GAME_TYPE_DATA = {
        "name": "checkers",
        "defaultState": "state"
    }

    INVALID_GAME_TYPE_DATA_1 = {
        "name": "veryepicgame"
    }

    INVALID_GAME_TYPE_DATA_2 = {
        "name": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "defaultState": "state"
    }

    def test_get(self, client):
        "Test GameTypeCollection GET"

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        # check if response contains a list of game types
        assert isinstance(body, list)
        assert len(body) > 0
        # check if each game type has 'id', 'name' and 'defaultState' fields
        for game_type in body:
            assert 'id' in game_type
            assert 'name' in game_type
            assert 'defaultState' in game_type
        assert body[0]['name'] == 'tictactoe'

    def test_post(self, client):
        "Test GameTypeCollection POST"

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson",
                           headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # check if the wrong api key is denied
        resp = client.post(self.RESOURCE_URL,
                           headers=Headers({"Api-key": TEST_KEY}))
        assert resp.status_code == 403

        # test with invalid game type data: Missing defaultState field
        resp = client.post(self.RESOURCE_URL,
                           json=self.INVALID_GAME_TYPE_DATA_1)
        assert resp.status_code == 400

        # test with invalid game type data: Name too long
        resp = client.post(self.RESOURCE_URL,
                           json=self.INVALID_GAME_TYPE_DATA_2)
        assert resp.status_code == 400

        # test with valid game type data
        resp = client.post(self.RESOURCE_URL, json=self.VALID_GAME_TYPE_DATA)
        assert resp.status_code == 201
        assert resp.headers["Location"] == "/api/game_types/checkers"
        # check if the game type is created
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert self.VALID_GAME_TYPE_DATA["name"] in [
            game_type["name"] for game_type in body]

        # Test creating a game type with the same name
        resp = client.post(self.RESOURCE_URL, json=self.VALID_GAME_TYPE_DATA)
        assert resp.status_code == 400


class TestGameTypeItem():
    """Tests for the /api/game_types/<game_type:game_type>/ endpoint"""

    RESOURCE_URL = "/api/game_types/tictactoe"
    INVALID_URL = "/api/game_types/x"

    VALID_NEW_GAME_TYPE_DATA = {
        "name": "checkers",
        "defaultState": "state"
    }

    VALID_EXISTING_GAME_TYPE_DATA = {
        "name": "tictactoe2",
        "defaultState": "state"
    }

    def test_get(self, client):
        "Test GameTypeItem GET"

        # Test non-existent game type
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == 1
        assert body["name"] == "tictactoe"
        assert body["defaultState"] == "1---------"

    def test_put(self, client):
        "Test GameTypeItem PUT"

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # Test with invalid url
        resp = client.put(self.INVALID_URL, json=self.VALID_NEW_GAME_TYPE_DATA)
        assert resp.status_code == 404

        # Test with another game type's name
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_EXISTING_GAME_TYPE_DATA)
        assert resp.status_code == 400

        # Test with valid
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_NEW_GAME_TYPE_DATA)
        assert resp.status_code == 200

    def test_delete(self, client):
        "Test GameTypeItem DELETE"

        # Game type should be deleted successfully
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 200

        # Trying to delete the same game type should lead to 404
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestGameCollection():
    """Tests for the /api/games/ endpoint"""

    RESOURCE_URL = "/api/games/"

    VALID_GAME_DATA = {
        "type": "tictactoe",
        "user": "testuser_1"
    }

    INVALID_GAME_DATA_1 = {
        "type": "veryepicbutnonexistentgame",
        "user": "testuser_1"
    }

    INVALID_GAME_DATA_2 = {
        "type": "tictactoe"
    }

    def test_get(self, client):
        """Test GameCollection GET"""

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        # check if response contains a list of game instances
        assert isinstance(body, list)
        assert len(body) > 0
        # check if each game has proper fields
        for game_type in body:
            assert 'id' in game_type
            assert 'type' in game_type
            assert 'result' in game_type
            assert 'state' in game_type
            assert 'currentPlayer' in game_type
        assert body[0]['state'] == '1---------'

    def test_post(self, client):
        """Test GameCollection POST"""

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson",
                           headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # check if the wrong api key is denied
        resp = client.post(self.RESOURCE_URL,
                           headers=Headers({"Api-key": TEST_KEY}))
        assert resp.status_code == 403

        # test with invalid game data: Non-existent game type
        resp = client.post(self.RESOURCE_URL,
                           json=self.INVALID_GAME_DATA_1)
        assert resp.status_code == 409

        # test with invalid game data: Missing user field
        resp = client.post(self.RESOURCE_URL,
                           json=self.INVALID_GAME_DATA_2)
        assert resp.status_code == 400

        # test with valid game data
        resp = client.post(self.RESOURCE_URL, json=self.VALID_GAME_DATA)
        assert resp.status_code == 201
        assert resp.headers["Location"] == "/api/games/4"
        # check if the game is created
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert self.VALID_GAME_DATA["type"] in [
            game_type["type"] for game_type in body]


class TestGameItem():
    """Tests for the /api/games/<int:game_id>/ endpoint"""

    RESOURCE_URL = "/api/games/1"
    INVALID_URL = "/api/games/123"

    VALID_MOVE_DATA = {
        "move": 6,
        "moveTime": 1
    }

    LEAVE_GAME_DATA = {
        "move": "",
        "moveTime": 1
    }

    INVALID_MOVE_DATA = {
        "moveTime": 1
    }

    INVALID_TICTACTOE_MOVE_DATA = {
        "move": 10,
        "moveTime": 1
    }

    VALID_ADMIN_PUT_DATA = {
        "currentPlayer": 2
    }

    def test_get(self, client):
        """Test GameItem POST"""

        # Test non-existent game type
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 409

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == 1
        assert body["type"] == "tictactoe"
        assert body["result"] == -1
        assert body["state"] == "1---------"
        assert body["currentPlayer"] == "testuser_1"
        assert body["moveHistory"] == "None"
        assert body["players"] == []

    def test_put(self, client):
        """Test GameItem PUT"""

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # Test with invalid url
        resp = client.put(self.INVALID_URL, json=self.VALID_MOVE_DATA)
        assert resp.status_code == 404

        # Test with invalid move json
        resp = client.put(self.RESOURCE_URL,
                          json=self.INVALID_MOVE_DATA)
        assert resp.status_code == 400

        # Test with invalid move
        resp = client.put(self.RESOURCE_URL,
                          json=self.INVALID_TICTACTOE_MOVE_DATA)
        assert resp.status_code == 400

        # Test with valid move
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_MOVE_DATA)
        assert resp.data.decode() == "2------X-- result:-1"
        assert resp.status_code == 200

        # Test with valid move again
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_MOVE_DATA, headers=Headers({"Api-key": ""}))
        assert resp.status_code == 403

        # Test setting current player with wrong api key
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_ADMIN_PUT_DATA, headers=Headers({"Api-key": TEST_KEY}))
        assert resp.status_code == 403

        resp = client.put(self.RESOURCE_URL,
                          json={"somerandomfield": "somerandomvalue"})
        assert resp.status_code == 400

        # Test setting current player with admin privileges
        resp = client.put(self.RESOURCE_URL,
                          json=self.VALID_ADMIN_PUT_DATA)
        assert resp.status_code == 200

        print(client.get(self.RESOURCE_URL).data)

        # Test leaving the game
        resp = client.put(self.RESOURCE_URL,
                          json=self.LEAVE_GAME_DATA,
                          headers=Headers({
                              "username": "testuser_2",
                              "password": "password2",
                              "Api-key": ""
                          }))
        assert resp.status_code == 200

    def test_delete(self, client):
        """Test GameItem DELETE"""

        resp = client.get("/api/games/")
        print(json.loads(resp.data))

        # Game should be deleted successfully
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 200

        resp = client.get("/api/games/")
        print(json.loads(resp.data))

        # Trying to delete the same game should lead to 404
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestRandomGame():
    """Tests for the /api/games/random/<game_type:game_type>/ endpoint"""

    RESOURCE_URL = "/api/games/random/tictactoe"
    INVALID_URL = "/api/games/random/epicgame"

    def test_post(self, client):
        """Test RandomGame POST"""

        # Test with invalid game type
        resp = client.post(self.INVALID_URL)
        assert resp.status_code == 404

        # Test with valid game type
        resp = client.post(self.RESOURCE_URL)
        location = resp.headers["Location"]
        assert resp.status_code == 302

        # Test if game id we got points to the correct game
        resp = client.get(location)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["currentPlayer"] == "testuser_1"
        assert body["players"] == ["testuser_1"]

        # Try again. This time a new game should be created
        resp = client.post(self.RESOURCE_URL)
        location = resp.headers["Location"]
        assert resp.status_code == 302

        resp = client.get(location)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["currentPlayer"] == "testuser_1"
        assert body["players"] == ["testuser_1"]
