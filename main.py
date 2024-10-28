# from enum import Enum

# from fastapi import Body, FastAPI, Query, Path
# from pydantic import BaseModel, Field

# app = FastAPI()


# @app.get("/")
# async def root():
#     return {"message": "hello world"}


import os
import sentry_sdk

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from sentry_sdk.integrations.flask import FlaskIntegration

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)  # Load env before run powerpaint

from system.exceptions import register_error_handlers
from system.model_encoder import AlchemyEncoder
from system.model_base import Session

SWAGGER_CONFIG = {
    "swagger": "2.0",
    "info": {
        "title": "API",
        "description": "API",
        "contact": {},
        "termsOfService": "http://rockship.co/#",
        "version": "0.1.0",
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
}

def create_app():
    app = Flask(__name__)

    from system.blue_print import register_blueprint
    from system.exceptions import register_error_handlers

    register_blueprint(app)
    register_error_handlers(app)

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        integrations=[FlaskIntegration()]
    )

    CORS(
        app,
        resources={
            r"/*": {
                'origins': '*'
            }
        },
        expose_headers=["X-Total-Count"]
    )

    if os.getenv('ENV') and os.getenv('ENV') != 'PROD':
        Swagger(app, template=SWAGGER_CONFIG)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.json_encoder = AlchemyEncoder
    register_error_handlers(app)
    app.sess = Session()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()
        if exception and Session.is_active:
            Session.rollback()

    from model.db import db

    db.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
