from blueprint.auth import bp as auth
from blueprint.book import bp as book
from blueprint.user import bp as user

def register_blueprint(app) -> None:
    app.register_blueprint(auth)
    app.register_blueprint(user)
    app.register_blueprint(book)