import json
from test.test_utils import TEST_KEY, client, game_url

from werkzeug.datastructures import Headers


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
        assert isinstance(body["items"], list)
        assert len(body["items"]) > 0
        # check if each game type has 'id', 'name' and 'defaultState' fields
        for game_type in body["items"]:
            assert 'name' in game_type
            assert 'defaultState' in game_type
        assert body["items"][0]['name'] == 'tictactoe'

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
            game_type["name"] for game_type in body["items"]]

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

    INVALID_GAME_TYPE_DATA = {
        "name": "checkers"
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

        # Test with an invalid JSON
        resp = client.put(self.RESOURCE_URL,
                          json=self.INVALID_GAME_TYPE_DATA)
        assert resp.status_code == 400

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
