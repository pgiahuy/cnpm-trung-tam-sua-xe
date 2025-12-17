from garage.models import SystemConfig

VNPAY_TMN_CODE = "Q2FNEKGM"
VNPAY_HASH_SECRET = "0TCYX8WBOXJIRXHOTYJFD65650S06J6I"
VNPAY_PAYMENT_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_RETURN_URL = "http://localhost:5000/payment_return"

def load_system_config(app):
    configs = SystemConfig.query.all()
    for cfg in configs:
        if cfg.key in ['MAX_SLOT_PER_DAY']:
            app.config[cfg.key] = int(cfg.value)
        elif cfg.key in ['VAT']:
            app.config[cfg.key] = float(cfg.value)
        else:
            app.config[cfg.key] = cfg.value

    # set default nếu chưa có trong DB
    app.config.setdefault('MAX_SLOT_PER_DAY', 30)
    app.config.setdefault('VAT', 0.1)

