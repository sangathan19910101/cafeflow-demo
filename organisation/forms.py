from django import forms

from .models import (
    Branch,
    Floor,  Table,
)


class BranchForm(forms.ModelForm):

    class Meta:
        model = Branch

        fields = [
            "name",
            "description",
            "is_active",
        ]


class FloorForm(forms.ModelForm):

    class Meta:
        model = Floor

        fields = [
            "branch",
            "name",
            "rows",
            "columns",
            "is_active",
        ]


class TableForm(forms.ModelForm):

    class Meta:
        model = Table

        fields = [
            "floor",
            "name",
            "capacity",
            "shape",
            "status",
        ]
