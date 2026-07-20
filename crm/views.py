from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from core.permissions import group_required
from .models import Customer, CustomerFeedback, CustomerSegment, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, CustomerCommunication


@group_required("Admin", "Manager")
def customer_list(request):
    customers = Customer.objects.all().order_by("-created_at")
    search = request.GET.get("search")
    vip = request.GET.get("vip")
    if search:
        customers = customers.filter(Q(name__icontains=search) | Q(phone__icontains=search))
    if vip:
        customers = customers.filter(is_vip=True)
    return render(request, "crm/customer_list.html", {"customers": customers})


@group_required("Admin", "Manager", "Waiter")
def customer_detail(request, customer_id):
    customer = get_object_or_404(
        Customer.objects.prefetch_related("feedback", "communications", "loyalty", "reservations"),
        pk=customer_id,
    )
    return render(request, "crm/customer_detail.html", {"customer": customer})


@group_required("Admin", "Manager")
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == "POST":
        customer.name = request.POST.get("name", customer.name)
        customer.phone = request.POST.get("phone", customer.phone)
        customer.email = request.POST.get("email", customer.email)
        customer.gender = request.POST.get("gender", customer.gender)
        customer.address = request.POST.get("address", "")
        customer.notes = request.POST.get("notes", "")
        customer.tags = request.POST.get("tags", "")
        customer.is_vip = request.POST.get("is_vip") == "on"
        customer.is_blacklisted = request.POST.get("is_blacklisted") == "on"
        dob = request.POST.get("date_of_birth", "")
        if dob:
            from datetime import datetime
            customer.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
        customer.save()
        messages.success(request, "Customer updated.")
        return redirect("customer_detail", customer_id=customer.id)
    return render(request, "crm/edit_customer.html", {"customer": customer})


@group_required("Admin")
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == "POST":
        customer_name = customer.name
        customer.delete()
        messages.success(request, f"Customer '{customer_name}' deleted.")
        return redirect("customer_list")
    return render(request, "crm/delete_customer.html", {"customer": customer})


@group_required("Admin", "Manager", "Waiter")
def create_customer(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email", "")
        address = request.POST.get("address", "")
        gender = request.POST.get("gender", "")
        is_vip = request.POST.get("is_vip") == "on"
        dob = request.POST.get("date_of_birth", "")
        if name and phone:
            customer = Customer.objects.create(
                name=name, phone=phone, email=email,
                address=address, gender=gender, is_vip=is_vip,
            )
            if dob:
                from datetime import datetime
                customer.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
                customer.save(update_fields=["date_of_birth"])
            messages.success(request, f"Customer '{customer.name}' created.")
            return redirect("customer_list")
        messages.error(request, "Name and phone are required.")
    return render(request, "crm/create_customer.html")


@group_required("Admin", "Manager")
def add_feedback(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    from organisation.models import Branch
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")
        branch_id = request.POST.get("branch") or None
        category = request.POST.get("category", "")
        if rating:
            CustomerFeedback.objects.create(
                customer=customer, rating=int(rating),
                comment=comment, branch_id=branch_id,
                category=category,
            )
            messages.success(request, "Feedback recorded.")
            return redirect("customer_detail", customer_id=customer.id)
        messages.error(request, "Rating is required.")
    return render(request, "crm/add_feedback.html", {
        "customer": customer,
        "branches": Branch.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def segment_list(request):
    segments = CustomerSegment.objects.prefetch_related("customers").all()
    return render(request, "crm/segment_list.html", {"segments": segments})


@group_required("Admin", "Manager")
def feedback_list(request):
    feedbacks = CustomerFeedback.objects.select_related("customer", "branch").all().order_by("-created_at")
    rating = request.GET.get("rating")
    if rating:
        feedbacks = feedbacks.filter(rating=rating)
    return render(request, "crm/feedback_list.html", {"feedbacks": feedbacks})


@group_required("Admin", "Manager")
def create_segment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        if name:
            segment = CustomerSegment.objects.create(name=name, description=description)
            messages.success(request, f"Segment '{segment.name}' created.")
            return redirect("segment_list")
        messages.error(request, "Name is required.")
    return render(request, "crm/create_segment.html")


@group_required("Admin", "Manager")
def loyalty_list(request):
    programs = LoyaltyProgram.objects.all().order_by("tier")
    return render(request, "crm/loyalty_list.html", {"programs": programs})


@group_required("Admin", "Manager")
def enroll_loyalty(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == "POST":
        program_id = request.POST.get("program")
        if program_id:
            program = get_object_or_404(LoyaltyProgram, pk=program_id)
            CustomerLoyalty.objects.get_or_create(
                customer=customer,
                defaults={"program": program},
            )
            messages.success(request, f"Enrolled in {program.name}.")
            return redirect("customer_detail", customer_id=customer.id)
        messages.error(request, "Select a program.")
    return render(request, "crm/enroll_loyalty.html", {
        "customer": customer,
        "programs": LoyaltyProgram.objects.filter(is_active=True),
    })


@group_required("Admin", "Manager")
def create_loyalty_program(request):
    if request.method == "POST":
        name = request.POST.get("name")
        tier = request.POST.get("tier", LoyaltyProgram.Tier.BRONZE)
        points_per_currency = request.POST.get("points_per_currency", 1)
        minimum_spend = request.POST.get("minimum_spend", 0)
        discount_percent = request.POST.get("discount_percent", 0)
        free_item_on_birthday = request.POST.get("free_item_on_birthday") == "on"
        if name:
            LoyaltyProgram.objects.create(
                name=name, tier=tier,
                points_per_currency=points_per_currency,
                minimum_spend=minimum_spend,
                discount_percent=discount_percent,
                free_item_on_birthday=free_item_on_birthday,
            )
            messages.success(request, f"Loyalty program '{name}' created.")
            return redirect("loyalty_list")
        messages.error(request, "Name is required.")
    return render(request, "crm/create_loyalty_program.html")


@group_required("Admin", "Manager")
def edit_loyalty_program(request, program_id):
    program = get_object_or_404(LoyaltyProgram, pk=program_id)
    if request.method == "POST":
        program.name = request.POST.get("name", program.name)
        program.tier = request.POST.get("tier", program.tier)
        program.points_per_currency = request.POST.get("points_per_currency", program.points_per_currency)
        program.minimum_spend = request.POST.get("minimum_spend", program.minimum_spend)
        program.discount_percent = request.POST.get("discount_percent", program.discount_percent)
        program.free_item_on_birthday = request.POST.get("free_item_on_birthday") == "on"
        program.is_active = request.POST.get("is_active") == "on"
        program.save()
        messages.success(request, "Loyalty program updated.")
        return redirect("loyalty_list")
    return render(request, "crm/edit_loyalty_program.html", {"program": program})


@group_required("Admin", "Manager")
def loyalty_transactions(request, customer_id=None):
    if customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        try:
            loyalty = CustomerLoyalty.objects.get(customer=customer)
            transactions = LoyaltyTransaction.objects.filter(customer_loyalty=loyalty).order_by("-created_at")
        except CustomerLoyalty.DoesNotExist:
            transactions = []
        return render(request, "crm/loyalty_transactions.html", {
            "customer": customer, "transactions": transactions,
        })
    transactions = LoyaltyTransaction.objects.select_related(
        "customer_loyalty", "customer_loyalty__customer"
    ).all().order_by("-created_at")[:200]
    return render(request, "crm/loyalty_transactions.html", {"transactions": transactions})


@group_required("Admin", "Manager")
def send_communication(request, customer_id=None):
    if request.method == "POST":
        c_ids = request.POST.getlist("customers") if not customer_id else [customer_id]
        subject = request.POST.get("subject")
        message_text = request.POST.get("message")
        channel = request.POST.get("channel", "SMS")
        if c_ids and subject and message_text:
            count = 0
            for cid in c_ids:
                CustomerCommunication.objects.create(
                    customer_id=cid, channel=channel,
                    subject=subject, message=message_text,
                    sent_at=timezone.now(),
                )
                count += 1
            messages.success(request, f"Communication queued for {count} customer(s).")
            if customer_id:
                return redirect("customer_detail", customer_id=customer_id)
            return redirect("customer_list")
        messages.error(request, "Subject and message are required.")
    segments = CustomerSegment.objects.filter(is_active=True)
    customers = Customer.objects.all().order_by("name")
    ctx = {
        "segments": segments,
        "customers": customers,
        "customer_id": customer_id,
    }
    if customer_id:
        ctx["customer"] = get_object_or_404(Customer, pk=customer_id)
    return render(request, "crm/send_communication.html", ctx)


@group_required("Admin", "Manager")
def populate_segment(request, segment_id):
    segment = get_object_or_404(CustomerSegment, pk=segment_id)
    if request.method == "POST":
        rules = request.POST.get("rules", "")
        if rules:
            import json
            try:
                rule_dict = json.loads(rules)
                segment.rules = rule_dict
                segment.save(update_fields=["rules"])
                customers = Customer.objects.all()
                if "min_visits" in rule_dict and rule_dict["min_visits"]:
                    customers = customers.filter(visit_count__gte=int(rule_dict["min_visits"]))
                if "min_spent" in rule_dict and rule_dict["min_spent"]:
                    customers = customers.filter(total_spent__gte=rule_dict["min_spent"])
                if "is_vip" in rule_dict and rule_dict["is_vip"]:
                    customers = customers.filter(is_vip=True)
                if "tags" in rule_dict and rule_dict["tags"]:
                    customers = customers.filter(tags__icontains=rule_dict["tags"])
                if "gender" in rule_dict and rule_dict["gender"]:
                    customers = customers.filter(gender=rule_dict["gender"])
                segment.customers.set(customers)
                messages.success(request, f"Segment populated with {customers.count()} customers.")
            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON format for rules.")
        return redirect("segment_list")
    return render(request, "crm/populate_segment.html", {"segment": segment})


@group_required("Admin", "Manager")
def customer_communications(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    comms = CustomerCommunication.objects.filter(customer=customer).order_by("-created_at")
    return render(request, "crm/customer_communications.html", {
        "customer": customer,
        "communications": comms,
    })
