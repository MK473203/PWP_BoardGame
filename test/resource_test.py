import json
import os
import pytest
import tempfile
import time
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

    def open(self, *args, **kwargs):
        auth_headers = Headers({
            "Api-key": ADMIN_KEY,
            "username": "testuser_1",
            "password": "password1"
        })
        headers = kwargs.pop('headers', Headers())
        headers.extend(auth_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
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

    os.close(db_fd)
    os.unlink(db_fname)


def _populate_db():

    tictactoe = GameType(name="tictactoe", defaultState="1---------")
    db.session.add(tictactoe)

    for i in range(1, 4):
        u = User(
            name="testuser_{}".format(i),
            password=key_hash("password{}".format(i))
        )
        db.session.add(u)

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


class TestUserCollection(object):

    RESOURCE_URL = "/api/users/"
    VALID_USER_DATA = {
        "name": "test-user-5",
        "password": "password1"
    }
    INVALID_USER_DATA = {
        "name": "test-user-y"
    }

    def test_get(self, client):

        # check if the wrong api key is denied
        # client.headers["Api-key"] = TEST_KEY
        # resp = client.get(self.RESOURCE_URL)
        # assert resp.status_code == 403

        # check if the correct key works
        # client.headers["Api-key"] = ADMIN_KEY
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
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson",
                           headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # test with invalid user data
        resp = client.post(self.RESOURCE_URL, json=self.INVALID_USER_DATA)
        assert resp.status_code == 400

        # test with valid user data
        resp = client.post(self.RESOURCE_URL, json=self.VALID_USER_DATA)
        assert resp.status_code == 201
        assert resp.headers["Location"] == "/api/users/test-user-5"
        # check if the user is created
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert self.VALID_USER_DATA["name"] in [user["name"] for user in body]


class TestUserItem(object):

    RESOURCE_URL = "/api/users/testuser_1"
    RESOURCE_URL_2 = "/api/users/testuser_2"
    INVALID_URL = "/api/users/x"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == 1
        assert body["name"] == "testuser_1"
        assert body["turnsPlayed"] == 0
        assert body["totalTime"] == 0
        assert body["games"] == []
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_user_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with another users's name
        valid["name"] = "testuser_2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test with valid
        valid["name"] = "cool_name"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 200

    def test_delete(self, client):
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
