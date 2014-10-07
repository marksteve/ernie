from antenna.app import create_app


if __name__ == "__main__":
  app = create_app(DEBUG=True)
  app.run(host="0.0.0.0")
