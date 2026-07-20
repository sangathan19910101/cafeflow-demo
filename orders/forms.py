from django import forms

from menu.models import MenuItem


class OrderItemForm(forms.Form):

    menu_item = forms.ModelChoiceField(
        queryset=MenuItem.objects.filter(
            is_available=True,
            is_deleted=False,
            category__is_active=True,
        )
        .select_related("category")
        .order_by(
            "category__name",
            "name",
        )
    )

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 2}
        )
    )
