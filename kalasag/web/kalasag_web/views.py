from flask import (abort, Blueprint, redirect, render_template, request,
                   session, url_for)

from . import db
from .util import rand_str

blueprint = Blueprint("views", __name__)


@blueprint.route("/")
def index():
  app = None
  if "app_client_id" in session:
    app = db.hgetall("apps:" + session["app_client_id"])
  return render_template("index.html", app=app)


@blueprint.route("/signup", methods=["GET", "POST"])
def signup():
  if request.method == "POST":
    app = dict(
      name=request.form["app_name"],
      client_id=rand_str(16),
      secret_key=rand_str(32),
    )
    db.hmset("apps:" + app["client_id"], app)
    session["app_client_id"] = app["client_id"]
    return redirect(url_for(".index"))
  return render_template("signup.html")

