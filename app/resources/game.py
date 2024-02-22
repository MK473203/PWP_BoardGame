from flask_restful import Resource


class GameCollection(Resource):

	# Get a list of all games
	def get(self):
		pass

	# Create a new game instance
	def post(self):
		pass

class GameItem(Resource):

	# Get information about a game instance
	def get(self):
		pass

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
		pass