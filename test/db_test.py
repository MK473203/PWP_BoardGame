from app import app
from gameTypes import gameType, defaultStates
from models import User, Game
from flask.testing import FlaskClient

def create_test_user():
    return User(
        name = "testuser"
        password = "test123"
        turnsPlayed = User.turnsPlayed
        totalTime = User.totalTime
        gameHistory = User.gameHistory
    )
  
def create_test_game():
    return 0
  
# Voi varmaan olla myös create_instances ja luo sekä käyttäjän että pelin
# Kuten tehty db_test.py esimerkissä
def test_create_user(app):

    # Testi, että Userin luonti ja tallennus databaseen onnistuu, sekä databasesta Userin löytäminen onnistuu
    with app.app_context():
        
        User = create_test_user()
        db.session.add(User)
        db.session.commit()
        
        assert User.query.count() == 1
        db.User = User.query.first()
        
def test_user_ondelete():
    return 0
    
def test_player_ondelete():
    return 0
