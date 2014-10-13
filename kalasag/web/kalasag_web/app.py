import os

from flask import Flask
from flask_restful import Api

from . import views, example
from .api import OTPRequest, OTPValidate, User


def create_app(**config):
  app = Flask(__name__)

  app.config.update(**config)
  app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    CHIKKA_CLIENT_ID=os.environ["CHIKKA_CLIENT_ID"],
    CHIKKA_SECRET_KEY=os.environ["CHIKKA_SECRET_KEY"],
    CHIKKA_SHORTCODE=os.environ["CHIKKA_SHORTCODE"],
  )

  app.register_blueprint(views.blueprint)
  app.register_blueprint(example.blueprint, url_prefix="/example")

  api = Api(app)
  api.add_resource(
    User,
    "/apps/<client_id>/users/<user_id>",
    endpoint="api_user",
  )
  api.add_resource(
    OTPRequest,
    "/apps/<client_id>/users/<user_id>/otp_request",
    endpoint="api_otp_request",
  )
  api.add_resource(
    OTPValidate,
    "/apps/<client_id>/users/<user_id>/otp_validate",
    endpoint="api_otp_validate",
  )

  return app
