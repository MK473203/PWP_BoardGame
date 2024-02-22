from flask_restful import Resource


class UserCollection(Resource):

	# Get a list of all users. Requires admin privileges to be implemented
    # User passwords not included.
    def get(self):
        pass

	# Create a new user
    def post(self):
        pass


class UserItem(Resource):

	# Get an user's information. Requires user authentication
    def get(self):
        pass

	# Update user information. Requires user authentication
    def put(self):
        pass
