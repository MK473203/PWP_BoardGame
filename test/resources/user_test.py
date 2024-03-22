import json
from test.test_utils import TEST_KEY, client, game_url

from werkzeug.datastructures import Headers

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
        assert isinstance(body["items"], list)
        assert len(body["items"]) > 0
        # check if each user has 'id' and 'name' fields
        for user in body["items"]:
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
        assert self.VALID_USER_DATA["name"] in [
            user["name"] for user in body["items"]]

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
        assert body["name"] == "testuser_1"
        assert body["turnsPlayed"] == 0
        assert body["totalTime"] == 0
        for game in body["games"]:
            assert 'id' in game
            assert 'type' in game
            assert 'result' in game

    def test_put(self, client):
        "Test UserItem PUT"

        VALID_USER = {
            "name": "extra-user-1",
            "password": "pass101"
        }

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=VALID_USER)
        assert resp.status_code == 404

        resp = client.put(self.RESOURCE_URL, json=VALID_USER, headers=Headers(
            {"username": "testuser_2", "password": "password2"}))
        assert resp.status_code == 403

        # test with another users's name
        VALID_USER["name"] = "testuser_2"
        resp = client.put(self.RESOURCE_URL, json=VALID_USER)
        assert resp.status_code == 400

        # Test with invalid password
        VALID_USER["name"] = "cool_name"
        VALID_USER["password"] = "a"
        resp = client.put(self.RESOURCE_URL, json=VALID_USER)
        assert resp.status_code == 400

        # test with valid
        VALID_USER["password"] = "cool_password1"
        resp = client.put(self.RESOURCE_URL, json=VALID_USER)
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
