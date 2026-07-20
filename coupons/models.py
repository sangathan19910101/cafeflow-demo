from django.db import models
from django.utils import timezone
from core.models import BaseModel
from organisation.models import Branch
from menu.models import MenuCategory, MenuItem


class Coupon(BaseModel):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED = "FIXED", "Fixed Amount"
        BOGO = "BOGO", "Buy One Get One"
        FREE_DELIVERY = "FREE_DELIVERY", "Free Delivery"

    class DayOfWeek(models.TextChoices):
        MON = "MON", "Monday"
        TUE = "TUE", "Tuesday"
        WED = "WED", "Wednesday"
        THU = "THU", "Thursday"
        FRI = "FRI", "Friday"
        SAT = "SAT", "Saturday"
        SUN = "SUN", "Sunday"

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_items_required = models.PositiveIntegerField(default=0)
    max_discount_cap = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    current_uses = models.PositiveIntegerField(default=0)
    usage_limit_per_customer = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    applicable_days = models.CharField(max_length=100, blank=True, help_text="Comma-separated: MON,TUE,WED")
    applicable_start_time = models.TimeField(blank=True, null=True)
    applicable_end_time = models.TimeField(blank=True, null=True)
    applicable_branches = models.ManyToManyField(Branch, blank=True, related_name="coupons")
    applicable_categories = models.ManyToManyField(MenuCategory, blank=True, related_name="coupons")
    applicable_items = models.ManyToManyField(MenuItem, blank=True, related_name="coupons")
    is_first_order_only = models.BooleanField(default=False)
    is_new_customer_only = models.BooleanField(default=False)
    stackable = models.BooleanField(default=False, help_text="Can be combined with other coupons")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        if self.valid_from:
            vf = self.valid_from
            if timezone.is_naive(vf):
                vf = timezone.make_aware(vf, timezone.get_default_timezone())
            if now < vf:
                return False
        if self.valid_until:
            vu = self.valid_until
            if timezone.is_naive(vu):
                vu = timezone.make_aware(vu, timezone.get_default_timezone())
            if now > vu:
                return False
        day_name = now.strftime("%a").upper()[:3]
        if self.applicable_days and day_name not in self.applicable_days.upper().split(","):
            return False
        if self.applicable_start_time:
            now_time = now.time()
            if now_time < self.applicable_start_time:
                return False
        if self.applicable_end_time:
            now_time = now.time()
            if now_time > self.applicable_end_time:
                return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = (subtotal * self.discount_value) / 100
            if self.max_discount_cap:
                discount = min(discount, self.max_discount_cap)
        elif self.discount_type == self.DiscountType.FIXED:
            discount = min(self.discount_value, subtotal)
        elif self.discount_type == self.DiscountType.BOGO:
            discount = self.discount_value
        else:
            discount = self.discount_value
        return discount
