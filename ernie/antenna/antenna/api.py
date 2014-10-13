import requests
from flask import current_app
from flask_restful import abort, fields, marshal_with, Resource
from flask_restful.reqparse import RequestParser
from simpleflake import simpleflake

CHIKKA_REPLY_ENDPOINT = "https://post.chikka.com/smsapi/request"


class SMS(Resource):

  def __init__(self):
    parser = RequestParser()
    parser.add_argument("message_type", type=str)
    parser.add_argument("mobile_number", type=int)
    parser.add_argument("shortcode", type=int)
    parser.add_argument("request_id", type=str)
    parser.add_argument("message", type=str)
    parser.add_argument("timestamp", type=float)
    self.parser = parser

  @marshal_with(dict(
    status=fields.Integer,
    message=fields.String,
  ))
  def post(self):
    args = self.parser.parse_args()

    if args.message_type != "incoming":
      abort(400, message="Unknown message type: {}".format(args.message_type))

    if args.shortcode != int(current_app.config["CHIKKA_SHORTCODE"]):
      abort(400, message="Invalid shortcode: {}".format(args.shortcode))

    res = requests.post(
      CHIKKA_REPLY_ENDPOINT,
      data=dict(
        message_type="REPLY",  # Inconsistent
        mobile_number=args.mobile_number,
        shortcode=args.shortcode,
        request_id=args.request_id,
        message_id=simpleflake(),
        message=args.message,
        request_cost="FREE",
        client_id=current_app.config["CHIKKA_CLIENT_ID"],
        secret_key=current_app.config["CHIKKA_SECRET_KEY"],
      ),
    )

    if res.status_code != requests.codes.ok:
      abort(500)

    return dict(status=200, message=args.message)

