from django.contrib import admin
from .models import Customer, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, CustomerCommunication, CustomerFeedback, CustomerSegment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "visit_count", "total_spent", "is_vip", "last_visit")
    list_filter = ("is_vip", "is_blacklisted", "preferred_branch")
    search_fields = ("name", "phone", "email")


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "points_per_currency", "discount_percent", "is_active")
    list_filter = ("tier", "is_active")


@admin.register(CustomerLoyalty)
class CustomerLoyaltyAdmin(admin.ModelAdmin):
    list_display = ("customer", "program", "points_balance", "lifetime_points")


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ("customer_loyalty", "type", "points", "created_at")
    list_filter = ("type",)


@admin.register(CustomerCommunication)
class CustomerCommunicationAdmin(admin.ModelAdmin):
    list_display = ("customer", "channel", "subject", "sent_at", "delivered")
    list_filter = ("channel", "delivered")


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ("customer", "rating", "branch", "created_at")
    list_filter = ("rating",)


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    filter_horizontal = ("customers",)
