"""
Flask resources for interacting with game instances.
Also allows users to join a random game instance of a wanted game type.
"""

import json
import secrets
import pickle
from random import randint

from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.sql import select
from jsonschema import ValidationError, validate
from jsonschema.validators import Draft7Validator
from werkzeug.exceptions import BadRequest, Forbidden

from app import db
from app.game_logic import apply_move
from app.models import Game, GamePlayers, GameType, User, key_hash
from app.utils import ADMIN_KEY_HASH, MASON, BoardGameBuilder, require_admin, require_login


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
                uuid=game.uuid,
                type=gametype,
                result=game.result,
                state=game.state,
                currentPlayer=player
            )
            game_obj.add_control("self", url_for("api.gameitem", game_id=game.id))
            games.append(game_obj)

        body = BoardGameBuilder(items=games)
        body.add_board_game_namespace()
        body.add_control_add_game()
        body.add_control_all_users()
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
                            $ref: '#/components/schemas/Sensor'
                        example:
                            type: tictactoe
                            user: user1
            responses:
                '201':
                    description: The game instance was created successfully
                    headers:
                        Location:
                            description: URI of the new sensor:
                            schema:
                                type: string
                '415':
                    description: Request content type must be JSON
                '409':
                    description: This GameType does not exist
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

        game = Game(type=typeid, state=state,
                    currentPlayer=userid)
        if userobj is not None:
            game.players = [userobj]
        db.session.add(game)
        db.session.commit()

        return Response(status=201, headers={"Location": url_for("api.gameitem", game_id=game.id)})


class GameItem(Resource):
    """Resource for handling getting, updating and deleting existing game information."""

    def get(self, game_id):
        """Get information about a game instance
            Input: id of the game in the address
            Output: Dictionary of all relevant information on the specified game
        """
        game = Game.query.filter_by(id=game_id).first()
        if not game:
            return Response("Game not found", 409)

        current_player = User.query.filter_by(id=game.currentPlayer).first()
        if current_player:
            current_player = current_player.name

        players = []
        for p in game.players:
            players.append(p.name)

        body = BoardGameBuilder(
            id=game.id,
            type=GameType.query.filter_by(id=game.type).first().name,
            result=game.result,
            state=game.state,
            currentPlayer=current_player,
            moveHistory=str(game.moveHistory),
            players=players
        )
        body.add_board_game_namespace()
        body.add_control_all_games()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_login
    def put(self, game_id, **kwargs):
        """
        Update game instance information. 
        The current player can make moves, after which the current player is set to none.
        Admins can update other information fields.

        Move JSON format (for tictactoe):

        {
            "move": 6,
            "moveTime": 1
        }

        move: game type specific integer or list of tuples signifying the move(s) to play
        moveTime: Time in seconds that the player took to make the move (integer)
        Output: new game state or nothing
        """

        db_game = Game.query.get(game_id)
        if not db_game:
            return Response("Game instance not found", 404)

        game_type = GameType.query.filter_by(id=db_game.type).first().name

        hashed_key = key_hash(request.headers.get("Api_key", "").strip())
        admin = secrets.compare_digest(hashed_key, ADMIN_KEY_HASH)

        is_correct_user = kwargs["login_user_id"] == db_game.currentPlayer
        if is_correct_user:
            # Allow the current player to make a move or leave the game without making a move
            try:
                validate(request.json, Game.move_schema(),
                         format_checker=Draft7Validator.FORMAT_CHECKER)
            except ValidationError as e:
                raise BadRequest(description=str(e)) from e

            if request.json["move"] == "":
                db_game.currentPlayer = None
                db.session.commit()
                return Response("Current player left the game", 200)

            move_result = apply_move(request.json["move"], db_game.state, game_type)
            if move_result is None:
                return Response("Requested move is invalid. " +
                    "Try again or leave the game with an empty move \"\"", 400)

            User.query.get(db_game.currentPlayer).totalTime += request.json["moveTime"]
            User.query.get(db_game.currentPlayer).turnsPlayed += 1

            query = GamePlayers.select().where((GamePlayers.c.gameId == db_game.id) &
                                               (GamePlayers.c.playerId == db_game.currentPlayer))
            query_result = db.session.execute(query).first()
            if not query_result:
                ins = GamePlayers.insert().values(
                    gameId=db_game.id,
                    playerId=db_game.currentPlayer,
                    team=int(db_game.state[0])
                )
                db.session.execute(ins)
            else:
                update = GamePlayers.update().where(
                    (GamePlayers.c.gameId == db_game.id) &
                    (GamePlayers.c.playerId == db_game.currentPlayer)
                ).values(team=int(db_game.state[0]))
                db.session.execute(update)

            move_history_list = []

            if db_game.moveHistory is not None:
                move_history_list = pickle.loads(db_game.moveHistory)

            move_history_list.append(request.json["move"])

            db_game.moveHistory = pickle.dumps(move_history_list)
            db_game.currentPlayer = None
            db_game.state = move_result[0]
            db_game.result = move_result[1]

            db.session.commit()
            return Response(db_game.state + " result:" + str(move_result[1]), 200)

        if admin:
            try:
                validate(request.json, Game.admin_schema(),
                         format_checker=Draft7Validator.FORMAT_CHECKER)
            except ValidationError as e:
                raise BadRequest(description=str(e)) from e

            game_to_modify = Game.query.get(game_id)

            if "currentPlayer" in request.json:
                game_to_modify.currentPlayer = request.json["currentPlayer"]
                insert = GamePlayers.insert().values(
                    gameId=game_to_modify.id,
                    playerId=request.json["currentPlayer"],
                    team=None
                )
                db.session.execute(insert)

            # More options can be added if needed

            db.session.commit()

            return 200

        print("ää")
        raise Forbidden

    @require_admin
    def delete(self, game_id):
        """Delete a game instance. Requires admin privileges.
            Input: Id of desired game
            Output:
        """

        db_game = Game.query.filter_by(id=game_id).first()
        if db_game:
            db.session.delete(db_game)
            db.session.commit()
            return 200
        else:
            return Response("Specified game id not found", 404)


class RandomGame(Resource):
    """
    Resource for getting a random game instance of a given game type. 
    """
    @require_login
    def post(self, game_type, **kwargs):
        """
        Redirects to the id of an random game with no current player and assigns the player to it.
        Should not be spammed!!! Creates a bunch of new games.
            Input: Game type in the address
            Output: Redirect to the url of chosen/created game
        """
        empty_games = Game.query.filter_by(type=game_type.id, currentPlayer=None, result=-1).all()
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

        user = User.query.get(user_id)
        game_id = None
        if available_games:
            # At least 1 available game was found
            ind = randint(0, len(available_games) - 1)
            available_games[ind].currentPlayer = user_id
            if user_id not in [user.id for user in available_games[ind].players]:
                available_games[ind].players += [user]
            db.session.commit()

            game_id = available_games[ind].id
        else:
            # No games available, create new game
            typeobj = GameType.query.filter_by(id=game_type.id).first()
            game = Game(
                type=game_type.id,
                state=typeobj.defaultState,
                currentPlayer=user_id,
                moveHistory=None,
                players=[user]
            )
            db.session.add(game)
            db.session.commit()
            game_id = game.id

        body = BoardGameBuilder()
        body.add_control("self", url_for("api.gameitem", game_id=game_id))
        return Response(json.dumps(body), 200, mimetype=MASON)
