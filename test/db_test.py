import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event

from app import create_app, db
from app.game_logic import apply_move
from app.models import User, Game, GameType


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()

    yield app


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
        """Test for User and Game creation on saving them to database"""

        with app.app_context():
            user = create_test_user()
            game = create_test_game()
            db.session.add(user)
            db.session.add(game)
            db.session.commit()

            assert User.query.count() == 1
            assert Game.query.count() == 1

    def test_game_type_creation(self, app):
        """Test for game type creation and saving to database"""

        with app.app_context():
            game_type = sample_game_type()
            db.session.add(game_type)
            db.session.commit()
            assert game_type.id is not None

    def test_game_creation(self, app):
        """Test for game creation and saving to database"""

        with app.app_context():
            game = create_test_game()
            db.session.add(game)
            db.session.commit()
            assert game.id is not None


class TestUser:
    def test_userid(self, app):
        """Test for different userid when creating two users"""

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

    def test_unique_username(self, app):
        """Test for unique username"""

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

    def test_delete_user(self, app):
        """Test to delete an user from the database"""

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


def test_user_playing_game(app):
    """Test to find the User from a game"""

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
            _, move_result = apply_move(move, old_state, game_type)

            # Check that move_result (result = 1 or 2) is game winning one
            assert move_result in [1, 2]

    def test_game_draw_tictactoe(self, app):
        with app.app_context():

            # Create a test gamestate
            old_state = "1XXOOOXXO-"  # Team 1 turn
            move = 8  # Example move, valid
            game_type = "tictactoe"

            # Complete a move
            _, move_result = apply_move(move, old_state, game_type)

            # Check that move_result (result = 0) is draw
            assert move_result == 0