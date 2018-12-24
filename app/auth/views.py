from flask import render_template, redirect, url_for, request
from flask_login import login_user

from . import auth_bp
from .forms import LoginForm
from app.models import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_user(User.query.filter_by(email=form.email.data).first(), True)
        return redirect(request.args.get('next') or url_for('goods_bp.index'))
    return render_template('auth/login.html', form=form)