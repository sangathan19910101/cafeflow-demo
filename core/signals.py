from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="billing.Payment")
def payment_update_customer(sender, instance, created, **kwargs):
    if created and instance.bill.customer_id:
        try:
            from crm.services import CRMService
            CRMService.record_visit(
                customer_id=instance.bill.customer_id,
                amount_spent=instance.amount_paid,
                branch=instance.bill.branch,
            )
        except Exception:
            pass
