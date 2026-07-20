from django.db import models
from core.models import BaseModel


class TaxCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax rate in percentage")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Tax Categories"

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class MenuCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ModifierGroup(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_selections = models.PositiveIntegerField(default=0)
    max_selections = models.PositiveIntegerField(default=1)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Modifier(BaseModel):
    group = models.ForeignKey(ModifierGroup, on_delete=models.CASCADE, related_name="modifiers")
    name = models.CharField(max_length=100)
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        adj = f" (+{self.price_adjustment})" if self.price_adjustment else ""
        return f"{self.name}{adj}"


class MenuItem(BaseModel):
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_category = models.ForeignKey(TaxCategory, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to="menu/items/", blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    preparation_time = models.PositiveIntegerField(default=0, help_text="Preparation time in minutes")
    sort_order = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    nutritional_info = models.JSONField(default=dict, blank=True, help_text="JSON: calories, protein, fat, carbs")
    allergen_info = models.JSONField(default=list, blank=True, help_text="JSON list: gluten, dairy, nuts")
    modifier_groups = models.ManyToManyField(ModifierGroup, blank=True, related_name="menu_items")

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [models.UniqueConstraint(fields=["category", "name"], name="unique_item_per_category")]

    def __str__(self):
        return self.name

    @property
    def profit_margin(self):
        if self.cost_price and self.price:
            return ((self.price - self.cost_price) / self.price) * 100
        return 0
