from django import forms

from .models import MenuItem, MenuCategory


class MenuItemForm(forms.ModelForm):

    class Meta:
        model = MenuItem

        fields = [
            "category",
            "name",
            "description",
            "price",
            "is_available",
        ]


class MenuCategoryForm(forms.ModelForm):

    class Meta:
        model = MenuCategory

        fields = [
            "name",
            "description",
            "is_active",
        ]
