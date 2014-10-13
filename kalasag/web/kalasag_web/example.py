import requests
from flask import (abort, Blueprint, flash, redirect, render_template, request,
                   session, url_for)

from . import db
from .util import rand_str

blueprint = Blueprint("example", __name__)


@blueprint.route("/")
def index():
  user = None

  client_id = session.get("example_client_id")
  user_id = session.get("example_user_id")
  secret_key = session.get("example_secret_key")

  if client_id and user_id and secret_key:
    user = db.hgetall("apps:{}:users:{}".format(
      client_id,
      user_id,
    ))

  return render_template(
    "example/index.html",
    user=user,
  )


@blueprint.route("/add_user", methods=["POST"])
def add_user():
  if request.method == "POST":
    res = requests.put(
      url_for(
        "api_user",
        client_id=request.form["client_id"],
        user_id=request.form["user_id"],
        _external=True,
      ),
      data=dict(
        secret_key=request.form["secret_key"],
        name=request.form["user_name"],
        number=request.form["user_number"],
      ),
    )
    if res.status_code != requests.codes.ok:
      abort(500)
    session["example_client_id"] = request.form["client_id"]
    session["example_secret_key"] = request.form["secret_key"]
    session["example_user_id"] = request.form["user_id"]
  return redirect(url_for(".index"))


@blueprint.route("/login", methods=["POST"])
def login():
  res = requests.post(
    url_for(
      "api_otp_request",
      client_id=session["example_client_id"],
      user_id=session["example_user_id"],
      _external=True,
    ),
    data=dict(
      secret_key=session["example_secret_key"],
    ),
  )
  if res.status_code != requests.codes.ok:
    abort(500)
  return redirect(url_for(".validate"))


@blueprint.route("/validate", methods=["GET", "POST"])
def validate():
  if request.method == "POST":
    res = requests.post(
      url_for(
        "api_otp_validate",
        client_id=session["example_client_id"],
        user_id=session["example_user_id"],
        _external=True,
      ),
      data=dict(
        code=request.form["code"],
        secret_key=session["example_secret_key"],
      ),
    )
    if res.status_code != requests.codes.ok:
      abort(500)
    if res.json()["valid"]:
      flash("Login success!")
    else:
      flash("Login failed")
  return render_template("example/validate.html")

