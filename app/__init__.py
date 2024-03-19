import os

import click
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cache = Cache()


@click.command("clear-cache")
def clear_cache_command():
    """
    Clears the cache

    Usage: flask clear-cache
    """
    cache.clear()


def delete_cache_entry(url):
    url = "view/" + url
    if cache.has(url):
        cache.delete(url)


def create_app(test_config=None):
    """Create app instance"""

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" +
        os.path.join(app.instance_path, "dev.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE="FileSystemCache",
        CACHE_DIR=os.path.join(app.instance_path, "cache"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    cache.init_app(app)

    from . import api, models  # pylint: disable=import-outside-toplevel

    app.url_map.converters["game_type"] = models.GameTypeConverter
    app.url_map.converters["user"] = models.UserConverter
    app.register_blueprint(api.api_bp)
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.populate_db_command)
    app.cli.add_command(clear_cache_command)

    return app
