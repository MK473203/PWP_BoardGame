"""
Utilities and helpers
"""

import secrets

from flask import request
from werkzeug.exceptions import Forbidden

from app.models import User, key_hash

ADMIN_KEY = "3CK1fq9levikwyj5WxueFdtvDmNlKeiz7zK09erDXg8"
ADMIN_KEY_HASH = key_hash(ADMIN_KEY)

def require_login(func):
    """
    Checks whether the incoming request has the login information of an existing user.

    DOES NOT CHECK WHICH USER IT IS. 
    The user's username and id are supplied to the wrapped function in kwargs.
    """

    def wrapper(*args, **kwargs):
        hashed_password = key_hash(
            request.headers.get("password", "").strip())
        name = request.headers.get("username", "").strip()

        db_user = User.query.filter_by(name=name).first()

        if name is not None and db_user is not None:
            if secrets.compare_digest(hashed_password, db_user.password):
                kwargs["login_username"] = name
                kwargs["login_user_id"] = db_user.id
                return func(*args, **kwargs)
            raise Forbidden
        raise Forbidden
    return wrapper


def require_admin(func):
    """Checks the incoming request for the admin api key"""

    def wrapper(*args, **kwargs):
        hashed_key = key_hash(
            request.headers.get("Api_key", "").strip())
        if secrets.compare_digest(hashed_key, ADMIN_KEY_HASH):
            return func(*args, **kwargs)
        raise Forbidden
    return wrapper
