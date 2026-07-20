import json
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from billing.models import Bill, Payment, QuickSaleItem
from orders.models import Order


class BillingService:
    TAX_PERCENTAGE = Decimal("13")

    PAYMENT_GATEWAYS = {
        "ESEWA": {"name": "eSewa", "test_url": "https://rc.esewa.com.np/epay/main", "live_url": "https://esewa.com.np/epay/main"},
        "KHALTI": {"name": "Khalti", "test_url": "https://a.khalti.com/api/v2/epayment/initiate/", "live_url": "https://khalti.com/api/v2/epayment/initiate/"},
        "FONEPAY": {"name": "FonePay", "test_url": "https://sandbox.fonepay.com/api/merchantRequest", "live_url": "https://fonepay.com/api/merchantRequest"},
        "CONNECT_IPS": {"name": "ConnectIPS", "test_url": "https://www.connectips.com/api/", "live_url": "https://www.connectips.com/api/"},
    }

    @staticmethod
    def calculate_subtotal(session):
        subtotal = Decimal("0")
        accepted_orders = session.orders.filter(status=Order.Status.ACCEPTED)
        for order in accepted_orders:
            for item in order.items.all():
                subtotal += item.price_snapshot * item.quantity
        return subtotal

    @staticmethod
    def calculate_tax(subtotal):
        return (subtotal * BillingService.TAX_PERCENTAGE) / Decimal("100")

    @staticmethod
    def calculate_grand_total(subtotal, tax, discount, tip=Decimal("0")):
        return subtotal + tax + tip - discount

    @classmethod
    @transaction.atomic
    def generate_bill(cls, session, discount=Decimal("0"), tip=Decimal("0"), coupon_code=""):
        session = session.__class__.objects.select_for_update().get(pk=session.pk)
        existing = getattr(session, "bill", None)
        if existing:
            return existing
        if discount < 0:
            raise ValueError("Discount cannot be negative.")
        subtotal = cls.calculate_subtotal(session)
        tax = cls.calculate_tax(subtotal)
        grand_total = cls.calculate_grand_total(subtotal, tax, discount, tip)
        if grand_total < 0:
            raise ValueError("Grand total cannot be negative.")
        bill = Bill.objects.create(
            session=session,
            branch=session.table.floor.branch,
            sale_type=Bill.SaleType.DINE_IN,
            subtotal=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            tip_amount=tip,
            grand_total=grand_total,
            coupon_code=coupon_code,
        )
        return bill

    @classmethod
    @transaction.atomic
    def create_quick_sale(cls, branch_id, items, payment_method="CASH", payment_amount=None):
        subtotal = Decimal("0")
        bill = Bill.objects.create(
            branch_id=branch_id,
            sale_type=Bill.SaleType.QUICK_SALE,
            subtotal=0,
            tax_amount=0,
            grand_total=0,
        )
        for item_data in items:
            qsi = QuickSaleItem.objects.create(
                bill=bill,
                item_name=item_data["name"],
                quantity=item_data["quantity"],
                unit_price=Decimal(str(item_data["price"])),
            )
            subtotal += qsi.line_total

        tax = cls.calculate_tax(subtotal)
        grand_total = cls.calculate_grand_total(subtotal, tax, Decimal("0"))
        bill.subtotal = subtotal
        bill.tax_amount = tax
        bill.grand_total = grand_total
        bill.save(update_fields=["subtotal", "tax_amount", "grand_total"])

        if payment_amount:
            cls.record_payment(bill, Decimal(str(payment_amount)), payment_method)

        return bill

    @staticmethod
    @transaction.atomic
    def record_payment(bill, amount_paid, payment_method, reference_number=""):
        bill = Bill.objects.select_for_update().get(pk=bill.pk)
        total_paid = bill.payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0
        remaining = bill.grand_total - total_paid

        if amount_paid <= 0:
            raise ValueError("Payment amount must be positive.")
        if amount_paid > remaining:
            raise ValueError(f"Payment exceeds remaining balance of {remaining}.")

        payment = Payment.objects.create(
            bill=bill,
            amount_paid=amount_paid,
            payment_method=payment_method,
            reference_number=reference_number,
        )

        if payment_method == "CASH":
            from operations.models import CashRegister, CashMovement
            branch = bill.session.table.floor.branch if bill.session else bill.branch
            if branch:
                open_register = CashRegister.objects.filter(
                    branch=branch, status=CashRegister.Status.OPEN
                ).order_by("-opened_at").first()
                if open_register:
                    CashMovement.objects.create(
                        register=open_register,
                        movement_type=CashMovement.MovementType.PAYMENT,
                        amount=amount_paid,
                        reference=f"Bill #{bill.id}",
                        notes="Payment received via cash",
                        recorded_by=None,
                    )

        from auditlog.models import AuditService
        AuditService.log(
            user=None, action="PAYMENT", entity_type="Payment",
            entity_id=str(payment.id),
            details={"bill_id": str(bill.id), "amount": str(amount_paid), "method": payment_method},
        )

        if BillingService.is_bill_fully_paid(bill) and bill.session:
            bill.session.is_billed = True
            bill.session.save(update_fields=["is_billed"])

        return payment

    @staticmethod
    def is_bill_fully_paid(bill):
        total_paid = bill.payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0
        return total_paid >= bill.grand_total

    @staticmethod
    @transaction.atomic
    def apply_coupon(bill, coupon_code):
        from coupons.models import Coupon
        bill = Bill.objects.select_for_update().get(pk=bill.pk)
        if bill.coupon_code:
            raise ValueError(f"Coupon '{bill.coupon_code}' is already applied to this bill.")
        coupon = Coupon.objects.filter(code__iexact=coupon_code.strip().upper()).first()
        if not coupon:
            raise ValueError(f"Invalid coupon code: '{coupon_code}'.")
        if not coupon.is_valid:
            reason = "Coupon is expired or not yet valid."
            if not coupon.is_active:
                reason = "Coupon has been deactivated."
            elif coupon.max_uses > 0 and coupon.current_uses >= coupon.max_uses:
                reason = "Coupon usage limit has been reached."
            raise ValueError(reason)
        if coupon.minimum_order_amount > 0 and bill.subtotal < coupon.minimum_order_amount:
            raise ValueError(f"Minimum order of Rs.{coupon.minimum_order_amount} required. Current subtotal: Rs.{bill.subtotal}.")
        discount = coupon.calculate_discount(bill.subtotal)
        new_grand_total = BillingService.calculate_grand_total(
            bill.subtotal, bill.tax_amount, discount, bill.tip_amount,
        )
        if new_grand_total < 0:
            raise ValueError("Coupon discount exceeds bill total.")
        bill.discount_amount = discount
        bill.grand_total = new_grand_total
        bill.coupon_code = coupon.code
        bill.save(update_fields=["discount_amount", "grand_total", "coupon_code"])
        coupon.current_uses += 1
        coupon.save(update_fields=["current_uses"])
        return bill

    @staticmethod
    def get_online_payment_url(bill, gateway="ESEWA", request=None):
        from django.urls import reverse
        config = BillingService.PAYMENT_GATEWAYS.get(gateway)
        if not config:
            raise ValueError(f"Unsupported payment gateway: {gateway}")
        base_success = reverse("payment_success", kwargs={"bill_id": bill.id})
        base_failed = reverse("payment_failed", kwargs={"bill_id": bill.id})
        if request:
            base_success = request.build_absolute_uri(base_success)
            base_failed = request.build_absolute_uri(base_failed)
        if gateway == "ESEWA":
            params = {
                "amt": float(bill.grand_total),
                "pdc": 0,
                "psc": 0,
                "txAmt": 0,
                "tAmt": float(bill.grand_total),
                "pid": str(bill.id),
                "scd": "EPAYTEST",
                "su": base_success,
                "fu": base_failed,
            }
            return f"{config['test_url']}?{chr(38).join(f'{k}={v}' for k, v in params.items())}"
        return config["test_url"]
