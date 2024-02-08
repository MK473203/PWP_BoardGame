from flask_sqlalchemy import SQLAlchemy
from app import app
from gameTypes import gameType, defaultStates

db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	name = db.Column(db.String(64))
	password = db.Column(db.String(64)) # In a real product this would be encrypted, but not here
	turnsPlayed = db.Column(db.Integer, default=0)
	totalTime = db.Column(db.Integer, default=0)
	gameHistory = db.Column(db.Text, default="")

class Game(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	type = db.Column(db.Integer)
	isActive = db.Column(db.Boolean, default=True)
	state = db.Column(db.Text)
	currentPlayer = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), default=None, nullable=True)
	history = db.Column(db.Text, default="")
	

if __name__ == "__main__":
	# Populate db
	ctx = app.app_context()
	ctx.push()
	db.create_all()
	
	user1 = User(name="user1", password="123456789")
	user2 = User(name="user2", password="salasana")
	user3 = User(name="user3", password="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

	game1 = Game(type=1, state=defaultStates[gameType.TICTACTOE], currentPlayer=user1.id)

	db.session.add_all([user1, user2, user3])
	db.session.add(game1)

	db.session.commit()

	ctx.pop()

	print("Populated db")