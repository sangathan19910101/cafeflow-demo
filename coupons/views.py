from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from core.permissions import group_required
from .models import Coupon


@group_required("Admin", "Manager")
def coupon_list(request):
    coupons = Coupon.objects.all().order_by("-created_at")
    return render(request, "coupons/list.html", {"coupons": coupons})


@group_required("Admin", "Manager")
def create_coupon(request):
    if request.method == "POST":
        code = request.POST.get("code")
        discount_type = request.POST.get("discount_type", "PERCENTAGE")
        discount_value = request.POST.get("discount_value", 0)
        valid_from = request.POST.get("valid_from")
        valid_until = request.POST.get("valid_until")
        if code and discount_type and discount_value and valid_from and valid_until:
            vf = datetime.fromisoformat(valid_from)
            vu = datetime.fromisoformat(valid_until)
            if timezone.is_naive(vf):
                vf = timezone.make_aware(vf, timezone.get_default_timezone())
            if timezone.is_naive(vu):
                vu = timezone.make_aware(vu, timezone.get_default_timezone())
            coupon = Coupon.objects.create(
                code=code.upper(), discount_type=discount_type,
                discount_value=discount_value,
                valid_from=vf, valid_until=vu,
            )
            messages.success(request, f"Coupon '{coupon.code}' created.")
            return redirect("coupon_list")
        messages.error(request, "All required fields must be filled.")
    now = timezone.now()
    default_from = now.strftime("%Y-%m-%dT%H:%M")
    default_until = (now + timezone.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M")
    return render(request, "coupons/create_coupon.html", {
        "default_from": default_from,
        "default_until": default_until,
    })
