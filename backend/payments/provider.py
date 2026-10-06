from backend.config import Settings

class StripeTestProvider:
    def __init__(self, config: Settings):
        if not config.stripe_secret_key.startswith('sk_test_'): raise ValueError('Test mode only')
        import stripe
        self.client=stripe.StripeClient(config.stripe_secret_key)
    def refund(self, payment_id, amount, key):
        result=self.client.v1.refunds.create({'payment_intent':payment_id,'amount':amount},options={'idempotency_key':key}).to_dict()
        if result.get('livemode'): raise ValueError('Live provider object rejected')
        return {'id':result['id'],'status':result['status']}
    def verify(self, reference):
        result=self.client.v1.refunds.retrieve(reference).to_dict()
        if result.get('livemode'): raise ValueError('Live provider object rejected')
        return {'id':result['id'],'status':result['status']}
