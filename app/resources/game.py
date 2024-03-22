"""
Flask resources for interacting with game instances.
Also allows users to join a random game instance of a wanted game type.
"""

import json
import pickle
from random import randint

from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from jsonschema.validators import Draft7Validator
from sqlalchemy.sql import select
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from app import db
from app.game_logic import apply_move
from app.models import Game, GamePlayers, GameType, User
from app.utils import MASON, BoardGameBuilder, require_admin, require_login


class GameCollection(Resource):
    """Resource for handling games"""

    def get(self):
        """Get a list of all games
            Input:
            Output: A list of all games

        """
        games = []
        for game in Game.query.all():
            player = User.query.filter_by(id=game.currentPlayer).first()
            if player:
                player = player.name

            gametype = GameType.query.filter_by(id=game.type).first()
            if gametype:
                gametype = gametype.name

            game_obj = BoardGameBuilder(
                id=game.uuid,
                type=gametype,
                result=game.result,
                state=game.state,
                currentPlayer=player
            )
            game_obj.add_control("self", url_for("api.gameitem", game=game))
            games.append(game_obj)

        body = BoardGameBuilder(items=games)
        body.add_board_game_namespace()
        body.add_control_add_game()
        body.add_control_all_users()
        body.add_control_all_game_types()
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_admin
    def post(self):
        """Create a new game instance
            Input: Json with the fields 'type' and 'user'
            Output: A Response with a header to the url of the created game
            ---
            description: Create a new game instance
            requestBody:
                description: JSON document that contains basic data for a new game
                content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/PostGame'
                        example:
                            type: tictactoe
                            user: user1
            responses:
                '201':
                    description: The game instance was created successfully
                    headers:
                        Location:
                            description: URI of the new sensor
                            schema:
                                type: string
                '409':
                    description: This GameType does not exist
                '415':
                    description: Request content type must be JSON

        """
        if not request.is_json:
            return "Request content type must be JSON", 415

        try:
            validate(request.json, Game.post_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        gametype = request.json["type"]
        if not GameType.query.filter_by(name=gametype).first():
            return "This GameType does not exist", 409
        else:
            gametypeobj = GameType.query.filter_by(name=gametype).first()
        typeid = gametypeobj.id
        state = gametypeobj.defaultState
        user = request.json["user"]
        userobj = User.query.filter_by(name=user).first()
        if userobj is not None:
            userid = None
        else:
            userid = userobj.id

        game = Game(type=typeid,
                    state=state,
                    currentPlayer=userid)
        if userobj is not None:
            game.players = [userobj]
        db.session.add(game)
        db.session.commit()

        return Response(status=201, headers={"Location": url_for("api.gameitem", game=game)})


class GameItem(Resource):
    """Resource for handling getting, updating and deleting existing game information."""

    def get(self, game):
        """
        Get information about a game instance

        Input: id of the game in the address
        Output: Dictionary of all relevant information on the specified game

        """
        if game is None:
            raise NotFound

        current_player = User.query.filter_by(id=game.currentPlayer).first()
        if current_player:
            current_player = current_player.name

        players = []
        for p in game.players:
            players.append(p.name)

        body = BoardGameBuilder(
            id=game.uuid,
            type=GameType.query.filter_by(id=game.type).first().name,
            result=game.result,
            state=game.state,
            currentPlayer=current_player,
            moveHistory="",
            players=players
        )

        if game.moveHistory is not None:
            body["moveHistory"] = str(pickle.loads(game.moveHistory))

        body.add_board_game_namespace()
        body.add_control_all_games()
        body.add_control_join_game(game)
        body.add_control_make_move(game)
        body.add_control_edit_game(game)
        body.add_control_delete_game(game)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_admin
    def put(self, game):
        """
        Update game instance information. 

        Input: JSON with the field 'currentPlayer'
        Output: 
        ---
        description: Update game instance information
        parameters:
        - $ref: '#/components/schemas/game
        requestBody:
            description: JSON document that contains a new current player
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/PutGame'
                    example:
                        currentPlayer: user2
        responses:
            '200':
                description: The game instance was modified successfully
            '400':
                description: Request body was not valid
            '404':
                description: Given user wasn't found
        """
        if game is None:
            raise NotFound

        try:
            validate(request.json, Game.put_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        db_user = User.query.filter_by(
            name=request.json["currentPlayer"]).first()
        if db_user is None:
            raise NotFound

        game.currentPlayer = db_user.id
        insert = GamePlayers.insert().values(gameId=game.id,
                                             playerId=db_user.id,
                                             team=None)
        db.session.execute(insert)

        # More options can be added if needed

        db.session.commit()

        return 200

    @require_admin
    def delete(self, game):
        """Delete a game instance. Requires admin privileges.
            Input: Id of desired game
            Output:
            ---
            description: Delete the game instance Admin required
            parameters:
            - $ref: '#/components/schemas/game
            responses:
                '200':
                    description: The game instance was removed successfully
        """
        if game is None:
            raise NotFound

        db_game = Game.query.filter_by(id=game.id).first()
        db.session.delete(db_game)
        db.session.commit()
        return 200


class MoveCollection(Resource):
    """
    Resource for making moves in a game instance.
    Also allows getting a game's move history.
    """

    def get(self, game):
        """Get the move history of a given game instance
            Input: uuid of the game in the address
            Output: List of moves made in this game. Format depends on game type.

        """

        if game is None:
            raise NotFound

        body = BoardGameBuilder(moveHistory="")

        if game.moveHistory is not None:
            body["moveHistory"] = str(pickle.loads(game.moveHistory))

        body.add_control("up", url_for("api.gameitem", game=game))

        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_login
    def post(self, game, **kwargs):
        """
        The current player can make moves, after which the current player is set to none.

        Move JSON format (for tictactoe):

        {
            "move": 6,
            "moveTime": 1
        }

        move: game type specific integer or list of tuples signifying the move(s) to play
        moveTime: Time in seconds that the player took to make the move (integer)
        Output: new game state
        ---
        description: The current player can make moves, after which the current player is set to none.
        parameters:
        - $ref: '#/components/schemas/game
        requestBody:
            description: JSON document that contains the next move and movetime of the move. Example move is for tictactoe.
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/MoveGame'
                    example:
                        move: 4
                        moveTime: 5
        responses:
            '200':
                description: Move has been made succesfully new state returned. Example given with tictactoe
                content:
                    application/json:
                        example: 
                            -state: 2X--------
            '400':
                description: Invalid JSON
            '403':
                description: Must log in before making a move
            '409':
                description: This GameType does not exist
            '415':
                description: Request content type must be JSON
        """
        if game is None:
            raise NotFound

        game_type = GameType.query.filter_by(id=game.type).first().name

        if not kwargs["login_user_id"] == game.currentPlayer:
            raise Forbidden

        # Allow the current player to make a move or leave the game without making a move
        try:
            validate(request.json, Game.move_schema(),
                     format_checker=Draft7Validator.FORMAT_CHECKER)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if request.json["move"] == "":
            game.currentPlayer = None
            db.session.commit()
            return Response(game.state + " result:" + str(game.result), 200)

        move_result = apply_move(
            request.json["move"], game.state, game_type)
        if move_result is None:
            return Response("Requested move is invalid. " +
                            "Try again or leave the game with an empty move \"\"", 400)

        User.query.get(
            game.currentPlayer).totalTime += request.json["moveTime"]
        User.query.get(game.currentPlayer).turnsPlayed += 1

        query = GamePlayers.select().where((GamePlayers.c.gameId == game.id) &
                                           (GamePlayers.c.playerId == game.currentPlayer))
        query_result = db.session.execute(query).first()
        if not query_result:
            ins = GamePlayers.insert().values(
                gameId=game.id,
                playerId=game.currentPlayer,
                team=int(game.state[0])
            )
            db.session.execute(ins)
        else:
            update = GamePlayers.update().where(
                (GamePlayers.c.gameId == game.id) &
                (GamePlayers.c.playerId == game.currentPlayer)
            ).values(team=int(game.state[0]))
            db.session.execute(update)

        move_history_list = []

        if game.moveHistory is not None:
            move_history_list = pickle.loads(game.moveHistory)

        move_history_list.append(request.json["move"])

        game.moveHistory = pickle.dumps(move_history_list)
        game.currentPlayer = None
        game.state = move_result[0]
        game.result = move_result[1]

        db.session.commit()
        return Response(game.state + " result:" + str(move_result[1]), 200)


class JoinGame(Resource):
    """
    Resource for joining an empty game
    """

    @require_login
    def post(self, game, **kwargs):
        """
        Try to join a game instance. Returns an error if the game already has a player

        """
        if game is None:
            raise NotFound

        if game.currentPlayer is None or game.currentPlayer == kwargs["login_user_id"]:
            game.currentPlayer = kwargs["login_user_id"]
            db.session.commit()
            body = BoardGameBuilder(ok="Ok")
            body.add_board_game_namespace()
            body.add_control_make_move(game)
            return Response(response=json.dumps(body),
                            status=200,
                            headers={"Location": url_for(
                                "api.gameitem", game=game)},
                            mimetype=MASON)
        else:
            body = BoardGameBuilder(error="Game already has a player")
            body.add_board_game_namespace()
            body.add_control_all_games()
            return Response(response=json.dumps(body),
                            status=409,
                            mimetype=MASON)


class RandomGame(Resource):
    """
    Resource for getting a random game instance of a given game type. 
    """
    @require_login
    def get(self, game_type, **kwargs):
        """
        Redirects to the id of an random game with no current player.
        Should not be spammed!!! Creates a bunch of new games.
            Input: Game type in the address
            Output: Redirect to the url of chosen/created game

        """
        empty_games = Game.query.filter_by(
            type=game_type.id, currentPlayer=None, result=-1).all()
        user_id = kwargs["login_user_id"]

        user_played_games = [
            game.id for game in empty_games
            if user_id in [user.id for user in game.players]
        ]

        query = select(GamePlayers.c.gameId, GamePlayers.c.team).where(
            GamePlayers.c.gameId.in_(user_played_games))
        game_id_and_team_list = db.session.execute(query).all()

        available_games = []
        for game in empty_games:
            if game.id in user_played_games:
                # User has played in this game already
                games_on_the_same_team = [
                    game_id for game_id, team in game_id_and_team_list
                    if team == int(game.state[0])]
                if game.id in games_on_the_same_team:
                    # User has not played on the opponent side for this game
                    available_games.append(game)
            else:
                available_games.append(game)

        game = None
        if available_games:
            # At least 1 available game was found
            ind = randint(0, len(available_games) - 1)
            game = available_games[ind]
        else:
            # No games available, create new game
            typeobj = GameType.query.filter_by(id=game_type.id).first()
            game = Game(type=game_type.id,
                        state=typeobj.defaultState)
            db.session.add(game)
            db.session.commit()

        body = BoardGameBuilder()
        body.add_board_game_namespace()
        body.add_control_join_game(game)
        return Response(response=json.dumps(body),
                        status=200,
                        headers={"Location": url_for(
                            "api.gameitem", game=game)},
                        mimetype=MASON)
