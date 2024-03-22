import json
import re
from test.test_utils import TEST_KEY, client, game_url

from werkzeug.datastructures import Headers

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
        assert isinstance(body["items"], list)
        assert len(body) > 0
        # check if each game has proper fields
        for game in body["items"]:
            assert 'id' in game
            assert 'type' in game
            assert 'result' in game
            assert 'state' in game
            assert 'currentPlayer' in game
        assert body["items"][0]['state'] == '1---------'

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
        assert re.fullmatch(r"/api/games/\w{32}", resp.headers["Location"])
        # check if the game is created
        resp = client.get(self.RESOURCE_URL)
        body = json.loads(resp.data)
        assert self.VALID_GAME_DATA["type"] in [
            game_type["type"] for game_type in body["items"]]


class TestGameItem():
    """Tests for the /api/games/<game:game>/ endpoint"""

    INVALID_URL = "/api/games/123"

    VALID_ADMIN_PUT_DATA = {
        "currentPlayer": "testuser_2"
    }

    def test_get(self, client, game_url):
        """Test GameItem GET"""

        # Test non-existent game type
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

        resp = client.get(game_url)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == game_url[11:]
        assert body["type"] == "tictactoe"
        assert body["result"] == -1
        assert body["state"] == "1---------"
        assert body["currentPlayer"] == "testuser_1"
        assert body["moveHistory"] == "None"
        assert body["players"] == []

    def test_put(self, client, game_url):
        """Test GameItem PUT"""

        # test with wrong content type
        resp = client.put(game_url, data="notjson",
                          headers=Headers({"Content-Type": "text"}))
        assert resp.status_code == 415

        # Test setting current player with wrong api key
        resp = client.put(game_url,
                          json=self.VALID_ADMIN_PUT_DATA, headers=Headers({"Api-key": TEST_KEY}))
        assert resp.status_code == 403

        resp = client.put(game_url,
                          json={"somerandomfield": "somerandomvalue"})
        assert resp.status_code == 400

        # Test setting current player with admin privileges
        resp = client.put(game_url,
                          json=self.VALID_ADMIN_PUT_DATA)
        assert resp.status_code == 200

    def test_delete(self, client, game_url):

        # Game should be deleted successfully
        resp = client.delete(game_url)
        assert resp.status_code == 200

        # Trying to delete the same game should lead to 404
        resp = client.delete(game_url)
        assert resp.status_code == 404

        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestMoveCollection():
    """Tests for the /api/games/<game:game>/moves endpoint"""

    INVALID_URL = "/api/games/123/moves"

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

    def test_get(self, client, game_url):
        pass

    def test_post(self, client, game_url):

        game_url = game_url + "/moves"

        # Test with invalid url
        resp = client.post(self.INVALID_URL, json=self.VALID_MOVE_DATA)
        assert resp.status_code == 404

        # Test with invalid move json
        resp = client.post(game_url,
                           json=self.INVALID_MOVE_DATA)
        assert resp.status_code == 400

        # Test with invalid move
        resp = client.post(game_url,
                           json=self.INVALID_TICTACTOE_MOVE_DATA)
        assert resp.status_code == 400

        # Test with valid move
        resp = client.post(game_url,
                           json=self.VALID_MOVE_DATA)
        assert resp.data.decode() == "2------X-- result:-1"
        assert resp.status_code == 200

        # Test with valid move again
        resp = client.post(game_url,
                           json=self.VALID_MOVE_DATA, headers=Headers({"Api-key": ""}))
        assert resp.status_code == 403

        resp = client.put(game_url[:-6],
                          json={"currentPlayer": "testuser_2"})

        # Test leaving the game
        resp = client.post(game_url,
                           json=self.LEAVE_GAME_DATA,
                           headers=Headers({
                               "username": "testuser_2",
                               "password": "password2",
                               "Api-key": ""
                           }))
        assert resp.status_code == 200


class TestJoinGame():
    """Tests for the /api/games/<game:game>/join endpoint"""

    INVALID_URL = "/api/games/123/join"

    def test_post(self, client):

        body = json.loads(client.get("/api/games/").data)
        empty_game_url = body["items"][2]["@controls"]["self"]["href"] + "/join"

        # Test with invalid url
        resp = client.post(self.INVALID_URL)
        assert resp.status_code == 404

        # Test with an empty game
        resp = client.post(empty_game_url)
        assert resp.status_code == 200

        # Try again with the same user. Should work
        resp = client.post(empty_game_url)
        assert resp.status_code == 200

        # Test if the current player was actually set
        resp = client.get(empty_game_url[:-5])
        body = json.loads(resp.data)
        print(body)
        assert body["currentPlayer"] == "testuser_1"

        # Test with another user. Should not work
        resp = client.post(empty_game_url, headers=Headers({
            "username": "testuser_2",
            "password": "password2"
        }))
        assert resp.status_code == 409


class TestRandomGame():
    """Tests for the /api/games/random/<game_type:game_type> endpoint"""

    RESOURCE_URL = "/api/games/random/tictactoe"
    INVALID_URL = "/api/games/random/epicgame"

    def test_get(self, client):
        """Test RandomGame GET"""

        # Test with invalid game type
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

        # Test with valid game type
        resp = client.get(self.RESOURCE_URL)
        location = resp.headers["Location"]
        assert resp.status_code == 200

        # Test if game id we got points to the correct game
        resp = client.get(location)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["currentPlayer"] is None
        assert body["players"] == []

        # Join the game
        resp = client.post(location + "/join")
        assert resp.status_code == 200

        # Try again. This time a new game should be created
        resp = client.get(self.RESOURCE_URL)
        location = resp.headers["Location"]
        assert resp.status_code == 200

        resp = client.get(location)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["currentPlayer"] is None
        assert body["players"] == []
