from datetime import datetime
from garage.models import Receipt, ReceiptItem
from garage import db

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



# Thanh toán

def add_receipt(cart, payment_method="CASH"):
    subtotal = 0

    # 1. Tạo receipt
    receipt = Receipt(
        subtotal=0,
        vat_rate=0,
        vat_amount=0,
        total_paid=0,
        payment_method=payment_method,
        paid_at=datetime.now()
    )
    db.session.add(receipt)
    db.session.flush()  # để có receipt.id

    # 2. Tạo receipt_item từ cart
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

    # 3. Cập nhật tiền
    receipt.subtotal = subtotal
    receipt.vat_amount = subtotal * receipt.vat_rate
    receipt.total_paid = receipt.subtotal + receipt.vat_amount

    db.session.commit()
    return receipt

# Xong thanh toán
