"""Create an actual TEST payment and map it to the local seed payment.
Run once against a fresh seeded DB with explicit test credentials.
"""
import stripe
from backend.config import settings
from backend.db import Session
from backend.models import Payment
cfg=settings()
if not cfg.stripe_secret_key.startswith('sk_test_'): raise SystemExit('STRIPE_SECRET_KEY must be a test key')
client=stripe.StripeClient(cfg.stripe_secret_key)
with Session.begin() as s:
    p=s.get(Payment,'pay_demo')
    if not p: raise SystemExit('Run the seed first')
    if p.provider_id or p.refunded_cents: raise SystemExit('Use a fresh seed payment without prior refunds')
    obj=client.v1.payment_intents.create({'amount':p.amount_cents,'currency':'usd','payment_method':'pm_card_visa','payment_method_types':['card'],'confirm':True},options={'idempotency_key':'conduit-fixture-pay-demo-v1'}).to_dict()
    if obj.get('livemode') or obj['status']!='succeeded': raise SystemExit('Test payment did not succeed')
    p.provider_id=obj['id']
print('Test payment linked. Start API with PAYMENT_PROVIDER=stripe.')
