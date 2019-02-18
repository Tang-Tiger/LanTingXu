
from flask import render_template, request, jsonify

from app.models import User, Role, Permission
from . import manage_bp


@manage_bp.route('/user')
def user():
    users = User.query.all()
    return render_template('manage/user.html', users=users)


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
