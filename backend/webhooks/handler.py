from sqlalchemy import select, text
from backend.models import ProviderEvent, Payment, Refund, Subscription, Customer
from backend.agent.service import DomainError

def ingest(s,event):
    if event.get('livemode'): raise DomainError('Live events prohibited',400)
    obj=event['data']['object']
    if s.bind.dialect.name=='postgresql':
        import hashlib
        lock_id=int.from_bytes(hashlib.sha256(obj['id'].encode()).digest()[:8],'big',signed=True)
        s.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':lock_id})
    # Serialize by linked business row before checking deduplication.
    if obj.get('object')=='refund':
        refund=s.scalar(select(Refund).where(Refund.provider_reference==obj['id']))
        if refund:
            payment=s.get(Payment,refund.payment_id)
            s.scalar(select(Customer).where(Customer.id==payment.customer_id).with_for_update())
    else:
        payment=s.scalar(select(Payment).where(Payment.provider_id==obj['id']))
        if payment: s.scalar(select(Customer).where(Customer.id==payment.customer_id).with_for_update())
    if s.get(ProviderEvent,event['id']): return {'duplicate':True}
    rec=ProviderEvent(id=event['id'],object_id=obj['id'],event_type=event['type'],created=event['created'],payload=event)
    s.add(rec); s.flush()
    apply(s,rec)
    return {'duplicate':False,'status':rec.status}

def apply(s,rec):
    obj=rec.payload['data']['object']
    payment=s.scalar(select(Payment).where(Payment.provider_id==obj['id']))
    refund=s.scalar(select(Refund).where(Refund.provider_reference==obj['id']))
    if refund: payment=s.get(Payment,refund.payment_id)
    if payment:
        s.scalar(select(Customer).where(Customer.id==payment.customer_id).with_for_update())
        s.refresh(payment)
        if refund: s.refresh(refund)
    newer=s.scalar(select(ProviderEvent).where(ProviderEvent.object_id==rec.object_id,ProviderEvent.created>rec.created,ProviderEvent.status=='applied'))
    if newer: rec.status='stale'; return
    if rec.event_type in {'refund.created','refund.updated','refund.failed'}:
        r=s.scalar(select(Refund).where(Refund.provider_reference==obj['id']))
        if not r: rec.status='unmatched'; return
        # Terminal outcomes cannot be regressed by replay of old pending events.
        status=obj.get('status','pending')
        if r.status in {'succeeded','failed','canceled'} and status!=r.status:
            rec.status='stale'; return
        if status in {'failed','canceled'} and r.status not in {'failed','canceled'}:
            p=s.get(Payment,r.payment_id); p.refunded_cents-=r.amount_cents
        r.status=status
    elif rec.event_type in {'payment_intent.succeeded','payment_intent.payment_failed'}:
        p=s.scalar(select(Payment).where(Payment.provider_id==obj['id']))
        if not p: rec.status='unmatched'; return
        if p.status!='succeeded': p.status='succeeded' if rec.event_type.endswith('.succeeded') else 'failed'
    elif rec.event_type=='customer.subscription.deleted':
        # Simulator subscription IDs differ from Stripe IDs; only an explicitly
        # imported test subscription with the exact ID can be reconciled.
        sub=s.get(Subscription,obj['id'])
        if not sub: rec.status='unmatched'; return
        from datetime import datetime, timezone
        sub.status='cancelled'; sub.cancelled_at=datetime.fromtimestamp(obj.get('canceled_at') or rec.created,timezone.utc).isoformat()
    else: rec.status='ignored'; return
    rec.status='applied'
