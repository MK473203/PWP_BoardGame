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
    
@pytest.fixture
def create_test_game():
    game_type = GameType(name="Tictactoe", defaultState="_________")
    db.session.add(game_type)
    db.session.commit()
    return Game(type=game_type.id)

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
        "result": -1
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

def test_user_playing_game(app):
    # Testi, että User löytyy pelistä
    with app.app_context():
        # Luo User ja Game
        user = create_test_user()
        game = create_test_game()
        db.session.add(user)
        db.session.add(game)
        db.session.commit()

        # Lisää User Gamen pelaajalistaan
        game.players.append(user)
        db.session.commit()

        db_user = User.query.first()
        db_game = Game.query.first()

        # Onko pelaaja pelin listassa
        assert db_user in db_game.players
        assert db_game in db_user.games


def test_delete_user(app):
    # Luo käyttäjä databaseen
    with app.app_context():
        user = create_test_user()
        db.session.add(user)
        db.session.commit()

        # Tarkista, että käyttäjä on databasessa
        assert User.query.count() == 1

        # Poista käyttäjä
        db.session.delete(user)
        db.session.commit()

        # Tarkista, että database on tyhjä
        assert User.query.count() == 0


def test_player_removed_after_move(app):
    # Luo User ja Game
    with app.app_context():
        user = create_test_user()
        game = create_test_game()

        # Lisää User Gameen
        game.players.append(user)
        db.session.add(game)
        db.session.commit()

        # Tämänhetkinen pelaaja
        game.currentPlayer = user.id
        db.session.commit()
        
        # Tarkista, että pelaaja ei ole enää pelissä siirron jälkeen
        assert user not in game.players


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
