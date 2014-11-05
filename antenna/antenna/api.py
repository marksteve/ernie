import os

import requests
from flask import current_app
from flask_restful import abort, fields, marshal_with, Resource
from flask_restful.reqparse import RequestParser
from simpleflake import simpleflake

CHIKKA_REPLY_ENDPOINT = "https://post.chikka.com/smsapi/request"
MSG_MAX_LEN = 200


wit = requests.Session()
wit.headers.update({
  "Authorization": "Bearer {}".format(
    os.environ["WIT_ACCESS_TOKEN"],
  )
})


def parse_query(q):
  res = wit.get("https://api.wit.ai/message", params=dict(
    v=20141022,
    q=q,
  ))
  if res.status_code != requests.codes.ok:
    return
  for outcome in res.json()["outcomes"]:
    return outcome


def ernie_answer(q):
  outcome = parse_query(q)
  if not outcome:
    return "Failed to parse query"

  intent = outcome["intent"]

  current_app.logger.debug("Outcome: %r", outcome)

  if outcome["confidence"] < 0.7:
    intent = "wolfram"

  if intent == "get_weather":
    location = None
    for entity_type, entities in outcome["entities"].items():
      if entity_type == "location":
        for entity in entities:
          location = entity["value"]
          break
        break
    if not location:
      return "You need to provide a location"
    res = requests.get(
      "http://omniscient:4567/weather/{}".format(
        location
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to get weather"
    return res.json()["reply"]

  if intent == "get_direction":
    origin = None
    destination = None
    for entity_type, entities in outcome["entities"].items():
      if entity_type == "origin":
        for entity in entities:
          origin = entity["value"]
          break
      if entity_type == "destination":
        for entity in entities:
          destination = entity["value"]
          break
    if not (origin and destination):
      return "You need to provide the origin and destination"
    res = requests.get(
      "http://omniscient:4567/goto/{}/{}".format(
        origin,
        destination,
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to get directions"
    return res.json()["reply"]

  if intent == "get_traffic":
    location = None
    for entity_type, entities in outcome["entities"].items():
      if entity_type == "location":
        for entity in entities:
          location = entity["value"]
          break
        break
    if not location:
      return "You need to provide a location"
    res = requests.get(
      "http://omniscient:4567/traffic/{}".format(
        location
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to get traffic"
    return res.json()["reply"]

  if intent == "wolfram":
    res = requests.get(
      "http://omniscient:4567/any",
      params=dict(
        query=outcome["_text"],
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to answer question"
    return res.json()["reply"]

  return "Sorry. I can't answer you right now :("


class SMS(Resource):

  def __init__(self):
    parser = RequestParser()
    parser.add_argument("demo", type=bool)
    parser.add_argument("message_type", type=str)
    parser.add_argument("mobile_number", type=int)
    parser.add_argument("shortcode", type=int)
    parser.add_argument("request_id", type=str)
    parser.add_argument("message", type=str)
    parser.add_argument("timestamp", type=float)
    self.parser = parser

  def __send(self, message_type, args, message):
    data = dict(
      message_type=message_type,
      mobile_number=args.mobile_number,
      shortcode=args.shortcode,
      message_id=str(simpleflake()),
      message=message,
      client_id=current_app.config["CHIKKA_CLIENT_ID"],
      secret_key=current_app.config["CHIKKA_SECRET_KEY"],
    )
    if message_type == "REPLY":
      data.update(
        request_id=args.request_id,
        request_cost="FREE",
      )

    current_app.logger.debug("Sending message: %r", data)
    res = requests.post(CHIKKA_REPLY_ENDPOINT, data=data)
    current_app.logger.debug("""
Status code: %r
Body: %r
""", res.status_code, res.content)

    if res.status_code != requests.codes.ok:
      abort(500)

  @marshal_with(dict(
    status=fields.Integer,
    message=fields.String,
  ))
  def post(self):
    args = self.parser.parse_args()

    if not args.demo:

      if args.message_type != "incoming":
        abort(400, message="Unknown message type: {}".format(
          args.message_type,
        ))

      if args.shortcode != int(current_app.config["CHIKKA_SHORTCODE"]):
        abort(400, message="Invalid shortcode: {}".format(args.shortcode))

    current_app.logger.debug("Query: %r", args)
    reply = ernie_answer(args.message)

    if not args.demo:

      self.__send("REPLY", args, reply[:MSG_MAX_LEN] + "\n-\n")

      if len(reply) > MSG_MAX_LEN:
        reply = reply[MSG_MAX_LEN:]
        while reply:
          self.__send("SEND", args, reply[:MSG_MAX_LEN] + "\n-\n")
          reply = reply[MSG_MAX_LEN:]

    return dict(status=200, message=reply)

