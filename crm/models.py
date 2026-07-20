from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from organisation.models import Branch


class Customer(BaseModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    preferred_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    visit_count = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_visit = models.DateTimeField(blank=True, null=True)
    is_vip = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["phone"]), models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class LoyaltyProgram(BaseModel):
    class Tier(models.TextChoices):
        BRONZE = "BRONZE", "Bronze"
        SILVER = "SILVER", "Silver"
        GOLD = "GOLD", "Gold"
        PLATINUM = "PLATINUM", "Platinum"

    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.BRONZE)
    points_per_currency = models.DecimalField(max_digits=6, decimal_places=2, default=1,
                                              help_text="Points earned per unit currency spent")
    minimum_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    free_item_on_birthday = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["tier"]

    def __str__(self):
        return f"{self.name} ({self.tier})"


class CustomerLoyalty(BaseModel):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="loyalty")
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.PROTECT, related_name="members")
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.points_balance} pts"


class LoyaltyTransaction(BaseModel):
    class Type(models.TextChoices):
        EARNED = "EARNED", "Points Earned"
        REDEEMED = "REDEEMED", "Points Redeemed"
        EXPIRED = "EXPIRED", "Points Expired"
        ADJUSTED = "ADJUSTED", "Manual Adjustment"

    customer_loyalty = models.ForeignKey(CustomerLoyalty, on_delete=models.PROTECT, related_name="transactions")
    type = models.CharField(max_length=20, choices=Type.choices)
    points = models.IntegerField()
    reference = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} {self.points} pts - {self.customer_loyalty.customer.name}"


class CustomerCommunication(BaseModel):
    class Channel(models.TextChoices):
        SMS = "SMS", "SMS"
        EMAIL = "EMAIL", "Email"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        IN_APP = "IN_APP", "In-App"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="communications")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} to {self.customer.name} - {self.subject[:50]}"


class CustomerFeedback(BaseModel):
    class Rating(models.IntegerChoices):
        TERRIBLE = 1, "Terrible"
        POOR = 2, "Poor"
        AVERAGE = 3, "Average"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="feedback")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(choices=Rating.choices)
    comment = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.rating}/5"


class CustomerSegment(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rules = models.JSONField(default=dict, blank=True,
                             help_text="Segment criteria rules in JSON")
    customers = models.ManyToManyField(Customer, blank=True, related_name="segments")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
