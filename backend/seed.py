from datetime import datetime, timedelta, timezone
from backend.models import *
from backend.db import Session

def seed(s, customer_id='cus_demo', amount=8900, kind='post_cancel', suffix='demo'):
    if s.get(Customer,customer_id): return
    s.add(Customer(id=customer_id,name='Kim Demo',email='demo@example.test',account_age_days=180)); s.flush()
    s.add(Account(id='acct_'+suffix,customer_id=customer_id)); s.flush()
    cancelled=kind not in {'ineligible','active'}
    s.add(Subscription(id='sub_'+suffix,customer_id=customer_id,status='cancelled' if cancelled else 'active',cancelled_at='2026-01-01T00:00:00+00:00' if cancelled else None)); s.flush()
    s.add(Payment(id='pay_'+suffix,customer_id=customer_id,subscription_id='sub_'+suffix,amount_cents=amount,created_at='2026-01-02T00:00:00+00:00')); s.flush()
    s.add(Order(id='ord_'+suffix,customer_id=customer_id,amount_cents=amount,status='processing',missing_verified=True)); s.flush()
    s.add(OrderItem(id='item_'+suffix,order_id='ord_'+suffix,sku='CONDUIT-TEE'))
    s.add(Shipment(id='ship_'+suffix,order_id='ord_'+suffix,status='label_created',tracking='TEST123'))

if __name__=='__main__':
    with Session.begin() as s: seed(s)
    print('Seeded cus_demo / pay_demo / sub_demo / ord_demo')
