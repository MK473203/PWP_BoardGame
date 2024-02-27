import secrets
import hashlib
from flask import request
from werkzeug.exceptions import Forbidden
from app.models import User

# 3CK1fq9levikwyj5WxueFdtvDmNlKeiz7zK09erDXg8
ADMIN_KEY_HASH = b'\xa5)\x0f\xe1\xee\xc0\xe3\x91o\x0c\x07\x11\xf1q\x9bgG\xc7\xb4s\n\xbb\xc8@\xb0\x02\x96!\xb7\xc4k1'

@staticmethod
def key_hash(key):
	return hashlib.sha256(key.encode()).digest()

def require_login(func):
    def wrapper(*args, **kwargs):
        hashed_key = key_hash(
            request.headers.get("password", "").strip())
        name = request.headers.get("username", "").strip()

        db_user = User.query.filter_by(name=name).first()

        if name is not None and db_user is not None:
            if secrets.compare_digest(hashed_key, db_user.password):
                return func(*args, **kwargs)
            raise Forbidden
        else:
            raise Forbidden
    return wrapper


def require_admin(func):
    def wrapper(*args, **kwargs):
        hashed_key = key_hash(
            request.headers.get("Api_key", "").strip())
        if secrets.compare_digest(hashed_key, ADMIN_KEY_HASH):
            return func(*args, **kwargs)
        raise Forbidden
    return wrapper
