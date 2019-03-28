
from flask import render_template, request, jsonify, abort, redirect, url_for, flash
from flask_login import current_user

from app.models import User, Role, Permission, GoodsType
from . import manage_bp
from .forms import UserForm, HomePageForm


@manage_bp.before_request
def before_request():
    if not current_user.is_authenticated:
        flash('请先登录。')
        return redirect(url_for('auth_bp.login'))
    if not current_user.can('system_manage'):
        abort(403)


@manage_bp.route('/user', methods=['GET', 'POST'])
def user():
    """ 用户查看，用户密码修改 """
    if request.method == 'POST':
        User.query.get_or_404(int(request.form.get('user_id', 0))).change_password(request.form.get('password'))
        return 'successful'

    users = User.query.order_by(User.id.desc()).all()
    return render_template('manage/user.html', users=users)


@manage_bp.route('/user_update/<int:user_id>', methods=['GET', 'POST'])
def user_update(user_id):
    the_user = User.query.get_or_404(user_id)
    form = UserForm(the_user)
    if request.method == 'GET':
        form.set_data()
    if form.validate_on_submit():
        kwargs = {'username': form.username.data, 'email': form.email.data, 'phone_number': form.phone_number.data,
                  'resume': form.resume.data}
        the_user.edit(**kwargs)
        flash('账户信息修改成功！')
        return redirect(url_for('.user'))
    return render_template('manage/update_user.html', form=form)


@manage_bp.route('/user_delete', methods=['POST'])
def user_delete():
    User.query.get_or_404(int(request.form.get('user_id', 0))).delete()
    return 'successful'


@manage_bp.route('/user_role/<user_id>', methods=['GET', 'POST'])
def user_role(user_id):
    the_user = User.query.get_or_404(int(user_id))

    if request.method == "POST":
        role_id = request.form.get('role_id')
        status = request.form.get('status')
        if status == 'append':
            the_user.append_role(int(role_id))
        else:
            the_user.remove_role(int(role_id))
        return 'successful'

    return jsonify([(item.name, item.id) for item in Role.query.all()
                    if the_user.roles.filter(Role.id == item.id).count() is 0])


@manage_bp.route('/role', methods=['GET', 'POST'])
def role():
    """ 用户角色的查看、添加和修改。 """
    if request.method == 'POST':
        role_id = request.form.get('role_id', -1) or -1
        role_name = request.form.get('role_name', None)
        role_details = request.form.get('role_details', None)

        if not role_name or Role.query.filter(Role.name == role_name, Role.id != int(role_id)).count() > 0:
            return '角色名非空且唯一', 400

        if role_id is not -1:
            Role.query.get_or_404(int(role_id)).add(role_name, role_details)
        else:
            Role().add(role_name, role_details)
        return 'successful'

    roles = Role.query.order_by(Role.id.desc()).all()
    return render_template('manage/role.html', roles=roles)


@manage_bp.route('/role_delete', methods=['POST'])
def role_delete():
    Role.query.get_or_404(int(request.form.get('role_id', 0))).delete()
    return 'successful'


@manage_bp.route('/permission/<role_id>', methods=['GET', 'POST'])
def permission(role_id):
    """ 角色权限的添加和移除 """
    result = []
    the_role = Role.query.get_or_404(int(role_id))

    if request.method == "POST":
        permission_id = request.form.get('permission_id')
        status = request.form.get('status')
        if status == 'true':
            the_role.append_permission(permission_id)
        else:
            the_role.remove_permission(permission_id)
        return 'successful'

    for item in Permission.query.all():
        if the_role.permissions.filter(Permission.name == item.name).count() > 0:
            result.append((item.name, item.id, 1))
        else:
            result.append((item.name, item.id, 0))
    return jsonify(result)


@manage_bp.route('/goods_type', methods=['GET', 'POST'])
def goods_type():
    if request.method == "POST":
        type_id = request.form.get('type_id', 0) or -1
        type_name = request.form.get('type_name')

        if not type_name or GoodsType.query.filter(GoodsType.id != int(type_id),
                                                   GoodsType.name == type_name).count() > 0:
            return '商品类型名非空且唯一', 400

        if type_id is -1:
            GoodsType().update(type_name)
        else:
            GoodsType.query.get_or_404(int(type_id)).update(type_name)
        return 'successful'

    goods_types = GoodsType.query.order_by(GoodsType.id.desc()).all()
    return render_template('manage/goods_type.html', goods_types=goods_types)


@manage_bp.route('/goods_type_delete', methods=['POST'])
def goods_type_delete():
    GoodsType.query.get_or_404(int(request.form.get('type_id', 0))).delete()
    return 'successful'


@manage_bp.route('/homepage', methods=['GET', 'POST'])
def homepage():
    form = HomePageForm()
    if form.validate_on_submit():
        print('post')
        print(form.bg_img.data.filename, form.caption.data)
        return redirect(url_for('.homepage'))
    print(form.caption.data, form.subhead.data)
    return render_template('manage/homepage.html', form=form)
