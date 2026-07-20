from decimal import Decimal
from django.utils import timezone
from .models import Coupon


class CouponService:
    @staticmethod
    def validate_and_apply(code, subtotal, branch=None):
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            raise ValueError("Invalid coupon code.")

        now = timezone.now()
        if now < coupon.valid_from:
            raise ValueError("Coupon is not yet valid.")
        if now > coupon.valid_until:
            raise ValueError("Coupon has expired.")
        if coupon.max_uses > 0 and coupon.current_uses >= coupon.max_uses:
            raise ValueError("Coupon usage limit reached.")
        if subtotal < coupon.minimum_order_amount:
            raise ValueError(f"Minimum order amount of {coupon.minimum_order_amount} required.")
        if branch and coupon.applicable_branches.exists() and branch not in coupon.applicable_branches.all():
            raise ValueError("Coupon not valid for this branch.")

        discount = coupon.calculate_discount(subtotal)
        coupon.current_uses += 1
        coupon.save(update_fields=["current_uses"])
        return discount

    @staticmethod
    def reverse_usage(code):
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.current_uses > 0:
                coupon.current_uses -= 1
                coupon.save(update_fields=["current_uses"])
        except Coupon.DoesNotExist:
            pass
