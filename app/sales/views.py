
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash
from sqlalchemy import cast, DATE, extract, func
from . import sales_bp
from .. import db
from .forms import SalesOrderForm
from ..models import Goods, SalesOrder, RelationOrderGoods


@sales_bp.route('/')
@sales_bp.route('/<the_type>')
@sales_bp.route('/<the_type>/<the_date>')
def index(the_type='day', the_date=None):
    # 在每次GET请求时清理无效订单
    SalesOrder.clear_invalid()

    # 这里有sqlalchemy关于日期查询的典型示例
    if the_type == 'day':
        the_date = datetime.strptime(the_date, '%Y-%m-%d') if the_date else datetime.now()
        order_find = SalesOrder.query.filter(
            cast(SalesOrder.create_time, DATE) == the_date.date(), SalesOrder.status != 0)

        sum_price = db.session.query(func.sum(SalesOrder.price)).filter(
            cast(SalesOrder.create_time, DATE) == the_date.date(), SalesOrder.status != 0).scalar()
        sum_total_real = db.session.query(func.sum(SalesOrder.total_real)).filter(
            cast(SalesOrder.create_time, DATE) == the_date.date(),
            SalesOrder.status != 0, SalesOrder.pay_status == True).scalar()
        count_pay_false = SalesOrder.query.filter(
            cast(SalesOrder.create_time, DATE) == the_date.date(),
            SalesOrder.status != 0, SalesOrder.pay_status == False).count()
        sum_pay_type = db.session.query(func.sum(SalesOrder.total_real).label('total'), SalesOrder.pay_type).filter(
            cast(SalesOrder.create_time, DATE) == the_date.date(),
            SalesOrder.status != 0, SalesOrder.pay_status == True).group_by(SalesOrder.pay_type)

        sum_goods_count = db.session.query(Goods.id, func.sum(RelationOrderGoods.count).label('number')).join(RelationOrderGoods, RelationOrderGoods.goods_id == Goods.id).join(SalesOrder, SalesOrder.id == RelationOrderGoods.order_id).filter(cast(SalesOrder.create_time, DATE) == the_date.date(), SalesOrder.status != 0).group_by(Goods.id)[0:3]

        current_date = the_date.strftime('%Y-%m-%d')
        current_type = 'day'  # 控制请求的url
        current_fmt = 'yyyy-mm-dd'  # 控制date插件显示的日期格式
        current_min_view = 0  # 控制date插件显示的粒度
        toggle_type = 'month'  # 控制切换
    else:
        the_date = datetime.strptime(the_date, '%Y-%m') if the_date else datetime.now()
        order_find = SalesOrder.query.filter(
            extract('year', SalesOrder.create_time) == the_date.year,
            extract('month', SalesOrder.create_time) == the_date.month,
            SalesOrder.status != 0)

        sum_price = db.session.query(func.sum(SalesOrder.price)).filter(
            extract('year', SalesOrder.create_time) == the_date.year,
            extract('month', SalesOrder.create_time) == the_date.month,
            SalesOrder.status != 0).scalar()
        sum_total_real = db.session.query(func.sum(SalesOrder.total_real)).filter(
            extract('year', SalesOrder.create_time) == the_date.year,
            extract('month', SalesOrder.create_time) == the_date.month,
            SalesOrder.status != 0, SalesOrder.pay_status == True).scalar()
        count_pay_false = SalesOrder.query.filter(
            extract('year', SalesOrder.create_time) == the_date.year,
            extract('month', SalesOrder.create_time) == the_date.month,
            SalesOrder.status != 0, SalesOrder.pay_status == False).count()
        sum_pay_type = db.session.query(func.sum(SalesOrder.total_real).label('total'), SalesOrder.pay_type).filter(
            extract('year', SalesOrder.create_time) == the_date.year,
            extract('month', SalesOrder.create_time) == the_date.month,
            SalesOrder.status != 0, SalesOrder.pay_status == True).group_by(SalesOrder.pay_type)

        current_date = the_date.strftime('%Y-%m')
        current_type = 'month'
        current_fmt = 'yyyy-mm'
        current_min_view = 1
        toggle_type = 'day'

    order_list = order_find.order_by(SalesOrder.create_time.desc()).all()
    # 统计分析数据结果
    total = order_find.count()
    stat = {'total': total, 'sum_total_real': sum_total_real, 'sum_price': sum_price,
            'count_pay_false': count_pay_false, 'sum_pay_type': sum_pay_type, 'sum_goods_count': sum_goods_count}

    return render_template('sales/index.html', order_list=order_list, stat=stat,
                           current_fmt=current_fmt, current_min_view=current_min_view,
                           current_date=current_date, current_type=current_type, toggle_type=toggle_type)


@sales_bp.route('/order_add_goods')
@sales_bp.route('/order_add_goods/<int:order_id>', methods=['GET', 'POST'])
def order_add_goods(order_id=None):
    if order_id is None:
        return redirect(url_for('.order_add_goods', order_id=SalesOrder().salesman_add()))
    else:
        current_order = SalesOrder.query.get_or_404(order_id)

    if request.method == 'POST':
        # 接收ajax发送的post请求，处理商品的追加和移除
        goods_id = request.form.get('goods_id')
        shift_type = request.form.get('shift_type')
        if shift_type == "append":
            current_order.salesman_goods_append(int(goods_id))
        else:
            current_order.salesman_goods_remove(int(goods_id))
        return "successful"

    goods_list = current_order.goods
    return render_template('sales/order_add_goods.html', goods_list=goods_list, order_id=order_id)


@sales_bp.route('/goods_search/<int:order_id>', methods=['GET', 'POST'])
def goods_search(order_id):
    goods_list = []
    if request.method == "POST":
        search_word=request.form.get('search_word')
        if search_word.isdigit():
            goods_list = Goods.query.filter_by(id=int(search_word)).all()
        else:
            goods_list = Goods.query.filter(Goods.name.like('%{}%'.format(search_word))).all()
    return render_template('sales/search_goods.html', goods_list=goods_list, order_id=order_id)


@sales_bp.route('/order_update/<int:order_id>', methods=['GET', 'POST'])
def order_update(order_id):
    current_order = SalesOrder.query.get_or_404(order_id)
    form = SalesOrderForm()

    if request.method == "GET":
        form.set_data(current_order)

    if form.validate_on_submit():
        current_order.salesman_update(form.total_real.data, form.pay_type.data, form.pay_status.data, form.remarks.data)
        flash('操作成功')
        return redirect(url_for('.index'))

    return render_template('sales/order_update.html', form=form)


@sales_bp.route('/order_info/<int:order_id>')
def order_info(order_id):
    current_order = SalesOrder.query.get_or_404(order_id)
    return render_template('sales/order_info.html', current_order=current_order)


@sales_bp.route('/order_delete', methods=['POST'])
def order_delete():
    SalesOrder.query.get_or_404(int(request.form.get('order_id'))).salesman_close()
    return 'successful'
