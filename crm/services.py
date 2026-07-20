from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Customer, CustomerLoyalty, LoyaltyTransaction, LoyaltyProgram


class CRMService:
    @staticmethod
    def find_or_create_customer(phone, name="", email=""):
        try:
            customer = Customer.objects.get(phone=phone)
            if name and customer.name != name:
                customer.name = name
                customer.save(update_fields=["name"])
            return customer
        except Customer.DoesNotExist:
            return Customer.objects.create(phone=phone, name=name or phone, email=email)

    @staticmethod
    @transaction.atomic
    def record_visit(customer_id, amount_spent=0, branch=None):
        customer = Customer.objects.select_for_update().get(pk=customer_id)
        customer.visit_count += 1
        customer.total_spent += Decimal(str(amount_spent))
        customer.last_visit = timezone.now()
        if branch:
            customer.preferred_branch = branch
        customer.save(update_fields=["visit_count", "total_spent", "last_visit", "preferred_branch"])

        try:
            loyalty = CustomerLoyalty.objects.get(customer=customer)
            if loyalty.program.is_active:
                points = int(Decimal(str(amount_spent)) * loyalty.program.points_per_currency)
                if points > 0:
                    loyalty.points_balance += points
                    loyalty.lifetime_points += points
                    loyalty.save(update_fields=["points_balance", "lifetime_points"])
                    LoyaltyTransaction.objects.create(
                        customer_loyalty=loyalty,
                        type=LoyaltyTransaction.Type.EARNED,
                        points=points,
                        reference=f"Visit {customer.visit_count}",
                    )
        except CustomerLoyalty.DoesNotExist:
            pass

    @staticmethod
    @transaction.atomic
    def redeem_points(customer_id, points):
        try:
            loyalty = CustomerLoyalty.objects.get(customer_id=customer_id)
        except CustomerLoyalty.DoesNotExist:
            raise ValueError("Customer not enrolled in loyalty program.")
        if loyalty.points_balance < points:
            raise ValueError(f"Insufficient points. Balance: {loyalty.points_balance}, Requested: {points}")
        loyalty.points_balance -= points
        loyalty.save(update_fields=["points_balance"])
        LoyaltyTransaction.objects.create(
            customer_loyalty=loyalty,
            type=LoyaltyTransaction.Type.REDEEMED,
            points=-points,
        )
        return True
