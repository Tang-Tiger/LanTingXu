import os
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth_bp.login'
login_manager.login_message = '请先登录账号。'


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'production')
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    @app.cli.command()
    def reset_db():
        """ 重置数据库 """
        from .models import User
        db.drop_all()
        db.create_all()
        User.insert_basic()
        click.echo(u'数据库重置成功。')

    from .main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(main_bp, subdomain='www')

    from .auth import auth_bp
    app.register_blueprint(auth_bp, subdomain='auth')

    from .goods import goods_bp
    app.register_blueprint(goods_bp, subdomain='goods')

    return app
