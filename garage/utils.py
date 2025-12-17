import math
from datetime import datetime

from flask_login import current_user
from garage.models import Receipt, ReceiptItem, Comment
from garage import db, app


def count_cart(cart):
    total_quantity, total_amount = 0, 0
    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity']*c['unit_price']

    return {
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }




def add_receipt(cart, payment_method="CASH"):
    subtotal = 0

    receipt = Receipt(
        subtotal=0,
        vat_rate=0,
        vat_amount=0,
        total_paid=0,
        payment_method=payment_method,
        paid_at=datetime.now()
    )
    db.session.add(receipt)
    db.session.flush()

    for c in cart.values():
        total_price = c['quantity'] * c['unit_price']
        subtotal += total_price

        item = ReceiptItem(
            receipt_id=receipt.id,
            spare_part_id=int(c['id']),
            quantity=c['quantity'],
            unit_price=c['unit_price'],
            total_price=total_price
        )
        db.session.add(item)

    receipt.subtotal = subtotal
    receipt.vat_amount = subtotal * receipt.vat_rate
    receipt.total_paid = receipt.subtotal + receipt.vat_amount

    db.session.commit()
    return receipt



def add_comment(content: str, sparepart_id: int):

    if not current_user.is_authenticated:
        raise PermissionError("Người dùng chưa đăng nhập.")

    if not content or not content.strip():
        raise ValueError("Nội dung bình luận không được để trống.")

    if not sparepart_id:
        raise ValueError("ID linh kiện không hợp lệ.")

    try:
        comment = Comment(
            content=content.strip(),
            sparepart_id=sparepart_id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        return comment

    except Exception as e:
        db.session.rollback()
        raise e


def get_comments(sparepart_id: int, page: int = 1):
    page = page if page > 0 else 1
    page_size = app.config.get("COMMENTS_PAGE_SIZE", 10)

    query = Comment.query.filter_by(sparepart_id=sparepart_id)\
                         .order_by(Comment.created_date.desc())

    return query.paginate(page=page, per_page=page_size, error_out=False).items


def count_comment(sparepart_id: int):
    return Comment.query.filter_by(sparepart_id=sparepart_id).count()


def get_comment_pagination(sparepart_id: int, current_page: int = 1):
    page_size = app.config.get("COMMENTS_PAGE_SIZE", 10)
    total_comments = count_comment(sparepart_id)
    total_pages = math.ceil(total_comments / page_size) if total_comments > 0 else 1
    current_page = max(1, min(current_page, total_pages))

    return {
        'total_pages': total_pages,
        'current_page': current_page,
        'has_prev': current_page > 1,
        'has_next': current_page < total_pages
    }