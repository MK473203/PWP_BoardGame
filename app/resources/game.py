from flask import Flask, request, Response, url_for
from flask_restful import Resource, Api
from app.models import GameType, User, Game
from app import db
from random import randint


class GameCollection(Resource):

	# Get a list of all games
	def get(self):
		games = []
		for game in Game.query.all():
			player = User.query.filter_by(id = game.currentPlayer).first()
			if player:
				player = player.name
			gametype = GameType.query.filter_by(id = game.type).first()
			if gametype:
				gametype = gametype.name
			games.append({
				"id" : game.id,
				#Replace 'gametype' with 'game.type' to get id instead
				"type" : gametype, 
				"isActive" : game.isActive,
				"state" : game.state,
				#Replace 'player' with 'game.currentPlayer' to get id instead
				"currentPlayer" : player
			})
		
		return games, 200
	
	# Create a new game instance
	def post(self):
		try:
			if not request.is_json:
				return "Request content type must be JSON", 415
			
			gametype = request.json["type"]
			if not GameType.query.filter_by(name = gametype).first():
					return "This GameType does not exist", 409
			else:
				gametypeobj = GameType.query.filter_by(name = gametype).first()
			typeid = gametypeobj.id
			state = gametypeobj.defaultState
			user = request.json["user"]
			userobj = User.query.filter_by(name=user).first()
			game = Game(type = typeid, state=state, currentPlayer = userobj.id)
			game.players=[userobj]
			db.session.add(game)
			db.session.commit()
			return Response(status = 201, headers={"location" : url_for("api.gameitem", game_id=game.id)})
		except KeyError:
			return "Incomplete request - missing fields", 400
		except ValueError:
			return "Weight and price must be numbers", 400

class GameItem(Resource):

	# Get information about a game instance
	def get(self, game_id):
		game = Game.query.filter_by(id = game_id).first()
		if not game:
			return "Game not found", 409
		player = User.query.filter_by(id = game.currentPlayer).first()
		if player:
			player = player.name
		players = []
		for p in game.players:
			# Replace 'p.name' with 'p.id' to make players list into id list instead
			players.append(p.name)
		info = {
				"id" : game.id,
				#Replace 'GameType.query.filter_by(id = game.type).first().name' with 'game.type' to get id instead
				"type" : GameType.query.filter_by(id = game.type).first().name, 
				"isActive" : game.isActive,
				"state" : game.state,
				"currentPlayer" : player,
				"moveHistory" : game.moveHistory,
				"players" : players
			}
		return info,  200

	# Update game instance information. (Tämä vai oma resurssinsa liikkeiden tekemiseen?)
	def put(self):
		pass

class RandomGame(Resource):
	

	"""
	Redirectaus random GameItemiin? Jos ei oo saatavilla avointa peliä nii tee uus.
	1. Hae random peli tietystä tyypistä
		(1b. Jos ei ole avointa peliä niin luo uus peli-instanssi GameCollection POSTilla?)
	2. Redirectaa peli-instanssin GETiin?

	Onko RESTissä sallittua tämmöne sattumanvarainen redirectaaminen (tilanteesta riippuen joko POSTiin tai GETiin)?
	"""
	def get(self, type):
		if not GameType.query.filter_by(id = type).first():
			return "This GameType does not exist", 409
		games = Game.query.filter_by(type = type, currentPlayer = None, isActive = True).all()
		if games:
			ind = randint(0, len(games)-1)
			return games[ind].id, 200
		else:
			typeobj = GameType.query.filter_by(id = type).first()
			game = Game(type = type, state = typeobj.defaultState)
			db.session.add(game)
			db.session.commit()
			return game.id, 200
		pass