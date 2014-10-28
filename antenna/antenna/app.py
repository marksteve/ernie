import os

from flask import Flask
from flask_restful import Api

from . import views
from .api import SMS


def create_app(**config):
  app = Flask(__name__)
  app.config.update(**config)
  app.config.update(
    CHIKKA_CLIENT_ID=os.environ["CHIKKA_CLIENT_ID"],
    CHIKKA_SECRET_KEY=os.environ["CHIKKA_SECRET_KEY"],
    CHIKKA_SHORTCODE=os.environ["CHIKKA_SHORTCODE"],
  )
  app.register_blueprint(views.blueprint)
  api = Api(app)
  api.add_resource(SMS, "/sms")
  return app
