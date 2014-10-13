import requests
from flask import current_app
from flask_restful import abort, fields, marshal_with, Resource
from flask_restful.reqparse import RequestParser
from otpauth import OtpAuth
from simpleflake import simpleflake

from . import db

CHIKKA_SMS_ENDPOINT = "https://post.chikka.com/smsapi/request"


user_fields = dict(
  id=fields.String,
  name=fields.String,
  number=fields.String,
)


class User(Resource):

  def __init__(self):
    parser = RequestParser()
    parser.add_argument("secret_key", type=str)
    parser.add_argument("name", type=str)
    parser.add_argument("number", type=str)
    self.parser = parser

  @marshal_with(user_fields)
  def put(self, client_id, user_id):
    args = self.parser.parse_args()

    if args.secret_key != db.hget("apps:" + client_id, "secret_key"):
      abort(401)

    user = dict(
      id=user_id,
      name=args.name,
      number=args.number,
    )
    db.hmset(
      "apps:{}:users:{}".format(client_id, user_id),
      user,
    )
    return user


class OTPRequest(Resource):

  def __init__(self):
    parser = RequestParser()
    parser.add_argument("secret_key", type=str)
    self.parser = parser

  def post(self, client_id, user_id):
    args = self.parser.parse_args()

    if args.secret_key != db.hget("apps:" + client_id, "secret_key"):
      abort(401)

    app_name = db.hget("apps:" + client_id, "name")
    user = db.hgetall(
      "apps:{}:users:{}".format(client_id, user_id),
    )

    auth = OtpAuth(args.secret_key)
    code = auth.totp()

    res = requests.post(
      CHIKKA_SMS_ENDPOINT,
      data=dict(
        message_type="SEND",  # Inconsistent
        mobile_number=user["number"],
        shortcode=current_app.config["CHIKKA_SHORTCODE"],
        message_id=simpleflake(),
        message="""{}

Code: {}

-
""".format(app_name, code),
        request_cost="FREE",
        client_id=current_app.config["CHIKKA_CLIENT_ID"],
        secret_key=current_app.config["CHIKKA_SECRET_KEY"],
      ),
    )

    if res.status_code != requests.codes.ok:
      abort(500)

    return ""


class OTPValidate(Resource):

  def __init__(self):
    parser = RequestParser()
    parser.add_argument("secret_key", type=str)
    parser.add_argument("code", type=str)
    self.parser = parser

  @marshal_with(dict(
    valid=fields.Boolean,
  ))
  def post(self, client_id, user_id):
    args = self.parser.parse_args()

    if args.secret_key != db.hget("apps:" + client_id, "secret_key"):
      abort(401)

    auth = OtpAuth(args.secret_key)
    return dict(
      valid=auth.valid_totp(args.code),
    )

