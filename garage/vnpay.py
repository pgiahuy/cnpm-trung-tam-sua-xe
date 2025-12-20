# vnpay.py

import hmac
import hashlib
import urllib.parse
import time
from flask import request

VNPAY_TMN_CODE = "Q2FNEKGM"
VNPAY_HASH_SECRET = "0TCYX8WBOXJIRXHOTYJFD65650S06J6I"
VNPAY_RETURN_URL = "http://localhost:5000/billing/vnpay_return"
VNPAY_PAYMENT_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"


def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def build_vnpay_url(amount, txn_ref, order_info='Thanh toan don hang'):
    vnp_amount = int(amount * 100)

    params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': VNPAY_TMN_CODE,
        'vnp_Amount': vnp_amount,
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': txn_ref,
        'vnp_OrderInfo': order_info,
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': VNPAY_RETURN_URL,
        'vnp_IpAddr': get_client_ip(),
        'vnp_CreateDate': time.strftime('%Y%m%d%H%M%S')
    }

    sorted_params = sorted(params.items())

    hash_data = '&'.join(
        f"{k}={urllib.parse.quote_plus(str(v))}"
        for k, v in sorted_params
    )

    secure_hash = hmac.new(
        VNPAY_HASH_SECRET.encode(),
        hash_data.encode(),
        hashlib.sha512
    ).hexdigest()

    params['vnp_SecureHash'] = secure_hash

    return VNPAY_PAYMENT_URL + '?' + urllib.parse.urlencode(params)
