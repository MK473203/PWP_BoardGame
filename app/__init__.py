import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" +
        os.path.join(app.instance_path, "dev.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # CACHE_TYPE="FileSystemCache",
        # CACHE_DIR=os.path.join(app.instance_path, "cache"),
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
    # cache.init_app(app)

    from . import models
    from . import api

    app.register_blueprint(api.api_bp)
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.populate_db_command)
    app.cli.add_command(models.reset_db_command)

    return app
