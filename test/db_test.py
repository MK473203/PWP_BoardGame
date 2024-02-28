import os
import pytest
import tempfile
from sqlalchemy.engine import Engine
from sqlalchemy import event

from app import create_app, db
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


@pytest.fixture
def create_test_user():
    return User(
        name="testuser",
        password="test123"
    )
    
@pytest.mark.skip
def create_test_game():
    pass

# Voi varmaan olla myös create_instances ja luo sekä käyttäjän että pelin
# Kuten tehty db_test.py esimerkissä


@pytest.fixture
def sample_game_type_data():
    return {
        "name": "Tictactoe",
        "defaultState": "Initial"
    }


@pytest.fixture
def sample_game_data():
    return {
        "type": 1,
        "state": "Initial",
        "isActive": True
    }


def test_unique_username(app):
    # Luo User
    user1 = User(name="test_user", password="password123")
    db.session.add(user1)
    db.session.commit()

    # Luo User samalla nimellä
    user2 = User(name="test_user", password="password456")
    db.session.add(user2)

    # Errorhandling
    with pytest.raises(Exception) as excinfo:
        db.session.commit()

    assert "IntegrityError" in str(excinfo.value)


def test_create_instances(app):
    # Testi, että Userin ja Gamen luonti ja tallennus databaseen onnistuu, sekä databasesta löytäminen onnistuu
    with app.app_context():
        user = create_test_user()
        game = create_test_game()
        db.session.add(user)
        db.session.add(game)
        db.session.commit()

        assert User.query.count() == 1
        assert Game.query.count() == 1

        db_user = User.query.first()
        db_game = Game.query.first()

        assert db_user.games == db_game
        assert db_game.players == db_user


@pytest.mark.skip
def test_user_ondelete():
    pass


@pytest.mark.skip
def test_player_ondelete():
    pass


# Testi pelityypin luonnille ja tallennukselle databaseen
def test_game_type_creation(db_session, sample_game_type_data):
    game_type = GameType(**sample_game_type_data)
    db_session.add(game_type)
    db_session.commit()
    assert game_type.id is not None


# Testi pelin luonnille ja tallennukselle databaseen
def test_game_creation(db_session, sample_game_data):
    game = Game(**sample_game_data)
    db_session.add(game)
    db_session.commit()
    assert game.id is not None
