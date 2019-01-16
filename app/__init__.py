import os
import click
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from flask_login import LoginManager

from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth_bp.login'
login_manager.login_message = '请登录账号。'


def create_app(config_name=os.getenv('FLASK_CONFIG', 'production')):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.cli.command()
    def deploy():
        """ 部署，部署前请创建数据库迁移脚本flask db migrate """
        upgrade()
        click.echo(u'本次部署初始化成功')

    register_logging(app)
    register_blueprints(app)
    register_errors(app)

    return app


def register_blueprints(app):
    from .main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(main_bp, subdomain='www')

    from .auth import auth_bp
    app.register_blueprint(auth_bp, subdomain='auth')

    from .goods import goods_bp
    app.register_blueprint(goods_bp, subdomain='goods')


def register_errors(app):
    @app.errorhandler(403)
    def forbid_error(e):
        return render_template('404.html'), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('404.html'), 500


def register_template_context(app):
    pass


def register_logging(app):
    if not app.debug:
        if app.config.get('MAIL_SERVER'):
            mail_handler = SMTPHandler(mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                                       credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
                                       fromaddr=app.config['MAIL_SENDER'], toaddrs=app.config['MAIL_ADMINS'],
                                       subject='兰亭续官网 ERRORS 警报日志', secure=())
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/run.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
