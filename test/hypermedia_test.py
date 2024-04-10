import json
import pytest
from app.utils import ADMIN_KEY
from test.test_utils import client, game_url

from werkzeug.datastructures import Headers

USER_INFO = {
    "username": "tester1",
    "password": "tester1"
}

USER_POST_JSON = {
    "name": USER_INFO["username"],
    "password": USER_INFO["password"]
}

GAME_TYPE_POST_JSON = {
    "name": "game",
    "defaultState": "state"
}

GAME_TYPE_PUT_JSON = {
    "name": "game2",
    "defaultState": "state2"
}

MOVE_JSON = {
    "move": 1,
    "moveTime": 1
}


class TestHypermedia():
    """Test the hypermedia implementation by hopping between urls using hypermedia controls"""

    def go_through_control(self, resp, client, ctrl_name, **kwargs):
        ctrl = json.loads(resp)["@controls"][ctrl_name]
        method = ctrl["method"]

        if method == "GET":
            f = client.get
        elif method == "POST":
            f = client.post
        elif method == "PUT":
            f = client.put
        elif method == "DELETE":
            f = client.delete
        else:
            pytest.fail("Method was not valid")

        resp = f(ctrl["href"], **kwargs)
        assert resp.status_code < 400

        try:
            body = json.loads(resp.data)
            if "@controls" in body:
                return resp
        except json.JSONDecodeError:
            if "Location" not in resp.headers:
                pytest.fail("Nowhere to go from here")
            return client.get(resp.headers["Location"])

    def test_hypermedia(self, client):
        """
        Big test.
        Does a lap through UserCollection -> UserItem -> UserCollection -> GameTypeCollection -> GameTypeItem -> RandomGame -> JoinGame -> MoveCollection -> GameItem -> GameCollection
        Using hypermedia and the location header
        """

        h = Headers({
            "Api-key": ADMIN_KEY,
            "username": USER_INFO["username"],
            "password": USER_INFO["password"]
        })

        resp = client.get("/api/", headers=h)

        # Go to UserCollection
        resp = self.go_through_control(
            resp.data, client, "boardgame:users-all", headers=h)

        # Create an user and go to the created user's address
        resp = self.go_through_control(
            resp.data, client, "boardgame:add-user", json=USER_POST_JSON, headers=h)

        # Edit user information
        resp = self.go_through_control(
            resp.data, client, "edit", json=USER_POST_JSON, headers=h)

        # Go back to UserCollection
        resp = self.go_through_control(
            resp.data, client, "collection", headers=h)

        # Go to GameTypeCollection
        resp = self.go_through_control(
            resp.data, client, "boardgame:gametypes-all", headers=h)

        # Create a game type and go to the created game type's address
        resp = self.go_through_control(
            resp.data, client, "boardgame:add-gametype", json=GAME_TYPE_POST_JSON, headers=h)

        # Edit the game type's information
        resp = self.go_through_control(
            resp.data, client, "edit", json=GAME_TYPE_PUT_JSON, headers=h)

        # Go to GameTypeCollection
        resp = self.go_through_control(
            resp.data, client, "collection", headers=h)

        game_type_item = [item for item in json.loads(
            resp.data)["items"] if item["name"] == "tictactoe"][0]
        resp = json.dumps(game_type_item)

        # Go to tictactoe's GameTypeItem
        resp = self.go_through_control(
            resp, client, "self", headers=h)

        # Get a random tictactoe game instance through get-random
        resp = self.go_through_control(
            resp.data, client, "boardgame:get-random", headers=h)

        # Join the game instance
        resp = self.go_through_control(
            resp.data, client, "boardgame:join-game", headers=h)

        # Make a move
        resp = self.go_through_control(
            resp.data, client, "boardgame:make-move", json=MOVE_JSON, headers=h)

        # Go to GameCollection through GameItem
        resp = self.go_through_control(
            resp.data, client, "up", headers=h)

        resp = self.go_through_control(
            resp.data, client, "collection", headers=h)

        print(resp.data)
