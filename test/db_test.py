import os
import pytest
import tempfile
from sqlalchemy.engine import Engine
from sqlalchemy import event

from app import create_app, db
from app.game_logic import apply_move
from app.models import User, Game, GameType


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_fname)


def create_test_user():
    return User(
        name="testuser",
        password="test123"
    )
    

def create_test_game():
    game_type = GameType(name="Tictactoe", defaultState="---------")
    db.session.add(game_type)
    db.session.commit()
    return Game(type=game_type.id)


@pytest.fixture
def sample_game_type_data():
    return {
        "name": "tictactoe",
        "defaultState": "---------"
    }


@pytest.fixture
def sample_game_data():
    return {
        "type": 1,
        "state": "---------",
        "result": -1
    }


def test_unique_username(app):
    with app.app_context():
        # Create a test User
        user1 = User(name="test_user", password="password123")
        db.session.add(user1)
        db.session.commit()

        # Create another user with the same name
        user2 = User(name="test_user", password="password456")
        db.session.add(user2)

        # Errorhandling
        with pytest.raises(Exception) as excinfo:
            db.session.commit()

        assert "IntegrityError" in str(excinfo.value)


def test_create_instances(app):
    # Test for User and Game creation on saving them to database
    with app.app_context():
        user = create_test_user()
        game = create_test_game()
        db.session.add(user)
        db.session.add(game)
        db.session.commit()

        assert User.query.count() == 1
        assert Game.query.count() == 1


def test_user_playing_game(app):
    # Test to find the User from a game
    with app.app_context():
        # Create User and Game
        user = create_test_user()
        game = create_test_game()
        db.session.add(user)
        db.session.add(game)
        db.session.commit()

        # Add User to the game playerlist
        game.players.append(user)
        db.session.commit()

        db_user = User.query.first()
        db_game = Game.query.first()

        # Check that User is in the game playerlist
        assert db_user in db_game.players
        assert db_game in db_user.games


def test_delete_user(app):
    # Create User to database
    with app.app_context():
        user = create_test_user()
        db.session.add(user)
        db.session.commit()

        # Check that database has an user
        assert User.query.count() == 1

        # Delete user
        db.session.delete(user)
        db.session.commit()

        # Check that database is empty
        assert User.query.count() == 0


@pytest.mark.skip(reason="Need to check how player removal from game after the move is done in code")
def test_player_removed_after_move(app):
    # Create User and Game
    with app.app_context():
        user = create_test_user()
        game = create_test_game()

        # Add User to the game
        game.players.append(user)
        db.session.add(game)
        db.session.commit()

        # Set current player
        game.currentPlayer = user.id
        db.session.commit()

        # Player should be removed after making their move
        assert user not in game.players


# Check for game type creation and saving to database
def test_game_type_creation(app, sample_game_type_data):
    with app.app_context():
        game_type = GameType(**sample_game_type_data)
        db.session.add(game_type)
        db.session.commit()
        assert game_type.id is not None


# Check for game creation and saving to database
def test_game_creation(app, sample_game_data):
    with app.app_context():
        game = Game(**sample_game_data)
        db.session.add(game)
        db.session.commit()
        assert game.id is not None


def test_apply_single_move_tictactoe(app):
    with app.app_context():

        # Create a test gamestate
        old_state = "1---------"  # Team 1 turn
        move = 4  # Example move, valid
        game_type = "tictactoe"

        # Complete a move
        new_state, game_result = apply_move(move, old_state, game_type)

        # Check that gamestate is correct after the move
        assert new_state == "2----X----"  # Assume team 1 makes a move to index 4
        # Check that game doesn't end
        assert game_result == -1


def test_invalid_move_tictactoe(app):
    with app.app_context():

        # Create a test gamestate
        old_state = "2----X----"  # Team 2 turn
        move = 4  # Example move, invalid
        game_type = "tictactoe"

        # Complete a move
        result = apply_move(move, old_state, game_type)

        # Check that outcome of apply_move() should be None (Invalid move)
        assert result is None


def test_gamewinning_move_tictactoe(app):
    with app.app_context():

        # Create a test gamestate
        old_state = "1XX-O--O-"  # Team 1 turn
        move = 2  # Example move, valid
        game_type = "tictactoe"

        # Complete a move
        new_state, move_result = apply_move(move, old_state, game_type)

        # Check that move_result (result = 1 or 2) is game winning one
        assert move_result in [1, 2]


def test_game_draw_tictactoe(app):
    with app.app_context():

        # Create a test gamestate
        old_state = "1XXOOOXXO-"  # Team 1 turn
        move = 8  # Example move, valid
        game_type = "tictactoe"

        # Complete a move
        new_state, move_result = apply_move(move, old_state, game_type)

        # Check that move_result (result = 0) is draw
        assert move_result == 0
