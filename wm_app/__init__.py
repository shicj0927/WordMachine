from flask import Flask
from .utils import inject_auth_context


def create_app():
    app = Flask(__name__,template_folder="../templates",static_folder="../static")
    app.config['JSON_SORT_KEYS'] = False

    # Register context processor
    app.context_processor(inject_auth_context)

    # Register blueprints
    from .routes_main import bp as main_bp
    from .routes_auth import bp as auth_bp
    from .routes_admin import bp as admin_bp
    from .routes_dict import bp as dict_bp
    from .routes_game import bp as game_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dict_bp)
    app.register_blueprint(game_bp)

    return app
