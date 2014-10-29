import os

import requests
from flask import current_app
from flask_restful import abort, fields, marshal_with, Resource
from flask_restful.reqparse import RequestParser
from simpleflake import simpleflake

CHIKKA_REPLY_ENDPOINT = "https://post.chikka.com/smsapi/request"


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

  if outcome["confidence"] < 0.5:
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
    return "It's {} in {}.".format(
      res.json()["desc"],
      location,
    )

  if intent == "get_direction":
    locations = []
    for entity_type, entities in outcome["entities"].items():
      if entity_type == "location":
        for entity in entities:
          locations.append(entity["value"])
          if len(locations) >= 2:
            break
    if len(locations) != 2:
      return "Didn't understand that"
    res = requests.get(
      "http://omniscient:4567/goto/{}/{}".format(
        locations[0],
        locations[1],
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to get directions"
    directions = res.json()
    if directions["steps"] == "[]":
      return "Failed to get directions"
    return """
Distance: {distance}
Time: {time} mins
Steps:
{steps}""".format(**directions)

  if intent == "wolfram":
    res = requests.get(
      "http://omniscient:4567/any",
      params=dict(
        q=outcome["_text"],
      ),
    )
    if res.status_code != requests.codes.ok:
      return "Failed to answer question"
    return "[WOLFRAM ANSWER GOES HERE]"

  return "Sorry. I can't answer you right now :("


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

    reply = ernie_answer(args.message)

    res = requests.post(
      CHIKKA_REPLY_ENDPOINT,
      data=dict(
        message_type="REPLY",  # Inconsistent
        mobile_number=args.mobile_number,
        shortcode=args.shortcode,
        request_id=args.request_id,
        message_id=simpleflake(),
        message=reply + "\n-\n",
        request_cost="FREE",
        client_id=current_app.config["CHIKKA_CLIENT_ID"],
        secret_key=current_app.config["CHIKKA_SECRET_KEY"],
      ),
    )

    if res.status_code != requests.codes.ok:
      abort(500)

    return dict(status=200, message=reply)
