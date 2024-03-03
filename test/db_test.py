import os
import pytest
import tempfile
import jsonschema
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from app import create_app, db
from app.game_logic import apply_move
from app.models import User, Game, GameType, GameTypeConverter


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
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
    game_type = GameType(name="tictactoe", defaultState="1---------")
    db.session.add(game_type)
    db.session.commit()
    return Game(type=game_type.id, state=game_type.defaultState)


def sample_game_type():
    return GameType(
        name="tictactoe",
        defaultState="1---------"
    )


class TestCreation:
    def test_create_instances(self, app):
        # Test for User and Game creation on saving them to database
        with app.app_context():
            user = create_test_user()
            game = create_test_game()
            db.session.add(user)
            db.session.add(game)
            db.session.commit()

            assert User.query.count() == 1
            assert Game.query.count() == 1


    # Test for game type creation and saving to database
    def test_game_type_creation(self, app):
        with app.app_context():
            game_type = sample_game_type()
            db.session.add(game_type)
            db.session.commit()
            assert game_type.id is not None


    # Test for game creation and saving to database
    def test_game_creation(self, app):
        with app.app_context():
            game = create_test_game()
            db.session.add(game)
            db.session.commit()
            assert game.id is not None


class TestUser:
    # Test for different userid when creating two users
    def test_userid(self, app):
        with app.app_context():
            # Create a test User
            user1 = User(name="test_user_1", password="password123")
            db.session.add(user1)
            db.session.commit()

            # Create another user with a different name
            user2 = User(name="test_user_2", password="password456")
            db.session.add(user2)
            db.session.commit()

            # Check that the user IDs are different
            assert user1.id != user2.id


    # Test for unique username
    def test_unique_username(self, app):
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


    # Test to delete an user from the database
    def test_delete_user(self, app):
        # Create User in the database
        with app.app_context():
            user = create_test_user()
            db.session.add(user)
            db.session.commit()

            # Check that the database has the user
            assert User.query.count() == 1

            # Record the user's ID and username
            user_id = user.id
            username = user.name

            # Delete the user
            db.session.delete(user)
            db.session.commit()

            # Check that the database is empty
            assert User.query.count() == 0

            # Check that the user's ID and username are released
            assert not User.query.filter_by(id=user_id).first()
            assert not User.query.filter_by(name=username).first()


class TestPassword:
    def test_valid_password(self):
        # Test a valid password
        assert User.validate_password("Password123") is None


    def test_short_password(self):
        # Test a password that is too short
        assert User.validate_password("ab") == ("Password must have 3-64 characters.", 400)


    def test_long_password(self):
        # Test a password that is too long
        assert User.validate_password("a" * 65) == ("Password must have 3-64 characters.", 400)


    def test_password_without_number(self):
        # Test a password without any number
        assert User.validate_password("Password") == ("Password must include at least one number.", 400)


class TestSchemas:
    def test_game_type_schema(self):
        # Get the JSON schema
        schema = GameType.json_schema()

        # Define a valid game type object
        valid_game_type = {
            "name": "tictactoe",
            "defaultState": "1---------"
        }

        # Validate the valid game type against the schema
        try:
            jsonschema.validate(instance=valid_game_type, schema=schema)
        except jsonschema.ValidationError:
            assert False, "Valid game type failed validation"

        # Define an invalid game type object
        invalid_game_type = {
            "name": "",
            "defaultState": ""
        }

        # Attempt to validate the invalid game type against the schema
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_game_type, schema=schema)


    def test_move_schema(self):
        # Test move schema
        schema = Game.move_schema()
        assert schema == {
            "type": "object",
            "required": ["move", "moveTime"],
            "properties": {
                "moveTime": {"type": "integer"}
            }
        }


    def test_admin_schema(self, app):
        # Test admin schema
        with app.app_context():
            # Generate enum values for currentPlayer
            user_ids = [user.id for user in User.query.all()]
            enum_values = user_ids + [None]

            schema = Game.admin_schema()
            assert schema == {
                "type": "object",
                "properties": {
                    "currentPlayer": {
                        "type": "integer",
                        "enum": enum_values
                    }
                }
            }


class TestGameTypeConverter:
    def test_to_python_existing_game_type(self, app):
        with app.app_context():
            # Test converting an existing game type name to a Python object
            converter = GameTypeConverter(BaseConverter)
            game_type_name = "ExampleGameType"
            game_type = GameType(name=game_type_name)
            db.session.add(game_type)
            db.session.commit()
            
            result = converter.to_python(game_type_name)
            assert result == game_type


    def test_to_python_nonexistent_game_type(self, app):
        with app.app_context():
            # Test converting a nonexistent game type name
            converter = GameTypeConverter(BaseConverter)
            game_type_name = "NonexistentGameType"
            
            with pytest.raises(NotFound):
                converter.to_python(game_type_name)


    def test_to_url(self, app):
        with app.app_context():
            # Test converting a game type object to a URL string
            converter = GameTypeConverter(BaseConverter)
            game_type_name = "ExampleGameType"
            game_type = GameType(name=game_type_name)
            
            result = converter.to_url(game_type)
            assert result == game_type_name


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


class TestTictactoe:
    def test_apply_single_move_tictactoe(self, app):
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


    def test_invalid_move_tictactoe(self, app):
        with app.app_context():

            # Create a test gamestate
            old_state = "2----X----"  # Team 2 turn
            move = 4  # Example move, invalid
            game_type = "tictactoe"

            # Complete a move
            result = apply_move(move, old_state, game_type)

            # Check that outcome of apply_move() should be None (Invalid move)
            assert result is None


    def test_gamewinning_move_tictactoe(self, app):
        with app.app_context():

            # Create a test gamestate
            old_state = "1XX-O--O-"  # Team 1 turn
            move = 2  # Example move, valid
            game_type = "tictactoe"

            # Complete a move
            new_state, move_result = apply_move(move, old_state, game_type)

            # Check that move_result (result = 1 or 2) is game winning one
            assert move_result in [1, 2]


    def test_game_draw_tictactoe(self, app):
        with app.app_context():

            # Create a test gamestate
            old_state = "1XXOOOXXO-"  # Team 1 turn
            move = 8  # Example move, valid
            game_type = "tictactoe"

            # Complete a move
            new_state, move_result = apply_move(move, old_state, game_type)

            # Check that move_result (result = 0) is draw
            assert move_result == 0


@pytest.mark.skip(reason="Tests not yet implemented")
class TestCheckers:
    def test_apply_move_checkers(self, app):
        pass

    def test_invalid_move_checkers(self, app):
        pass

    def test_gamewinning_move_checkers(self, app):
        pass
