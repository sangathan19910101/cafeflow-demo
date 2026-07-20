from core.permissions import group_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import BranchForm, FloorForm, TableForm
from .models import Branch, Floor, Table
from django.views.decorators.http import require_GET


# ====================================================
# BRANCHES
# =====================================================


@group_required("Admin", "Manager")
def branch_list(request):
    branches = Branch.objects.filter(
        is_deleted=False
    ).order_by("name")

    return render(
        request,
        "organisation/branch_list.html",
        {
            "branches": branches
        }
    )


@group_required("Admin", "Manager")
def create_branch(request):

    if request.method == "POST":
        form = BranchForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("branch_list")

    else:
        form = BranchForm()

    return render(
        request,
        "organisation/create_branch.html",
        {
            "form": form
        }
    )


@group_required("Admin", "Manager")
def edit_branch(request, branch_id):

    branch = get_object_or_404(
        Branch,
        id=branch_id,
    )

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)

        if form.is_valid():
            form.save()
            return redirect("branch_list")

    else:
        form = BranchForm(instance=branch)

    return render(
        request,
        "organisation/edit_branch.html",
        {
            "form": form,
            "branch": branch,
        }
    )


@group_required("Admin", "Manager")
def toggle_branch(request, branch_id):

    branch = get_object_or_404(
        Branch,
        id=branch_id,
    )

    branch.is_active = not branch.is_active
    branch.save(update_fields=["is_active"])

    return redirect("branch_list")


# =====================================================
# FLOORS
# =====================================================

@group_required("Admin", "Manager")
def create_floor(request):

    if request.method == "POST":
        form = FloorForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("floor_list")

    else:
        form = FloorForm()

    return render(
        request,
        "organisation/create_floor.html",
        {
            "form": form
        }
    )


@group_required("Admin", "Manager")
def edit_floor(request, floor_id):

    floor = get_object_or_404(
        Floor,
        id=floor_id,
    )

    if request.method == "POST":
        form = FloorForm(request.POST, instance=floor)

        if form.is_valid():
            form.save()
            return redirect("floor_list")

    else:
        form = FloorForm(instance=floor)

    return render(
        request,
        "organisation/edit_floor.html",
        {
            "form": form,
            "floor": floor,
        }
    )


@group_required("Admin", "Manager")
def toggle_floor(request, floor_id):

    floor = get_object_or_404(
        Floor,
        id=floor_id,
    )

    floor.is_active = not floor.is_active
    floor.save(update_fields=["is_active"])

    return redirect("floor_list")


# =====================================================
# TABLES
# =====================================================

@group_required("Admin", "Manager")
def create_table(request):

    if request.method == "POST":
        form = TableForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("table_list")

    else:
        form = TableForm()

    return render(
        request,
        "organisation/create_table.html",
        {
            "form": form,
        },
    )


@group_required("Admin", "Manager")
def edit_table(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
    )

    if request.method == "POST":
        form = TableForm(request.POST, instance=table)

        if form.is_valid():
            form.save()
            return redirect("table_list")

    else:
        form = TableForm(instance=table)

    return render(
        request,
        "organisation/edit_table.html",
        {
            "form": form,
            "table": table,
        },
    )


@group_required("Admin", "Manager")
def toggle_table(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
    )

    table.is_active = not table.is_active
    table.save(update_fields=["is_active"])

    return redirect("table_list")


@group_required("Admin", "Manager")
def mark_table_available(request, table_id):

    table = get_object_or_404(Table, id=table_id)

    table.status = Table.Status.AVAILABLE
    table.save(update_fields=["status"])

    return redirect("table_list")


@group_required("Admin", "Manager")
def floor_list(request):

    floors = Floor.objects.filter(
        is_deleted=False,
    ).select_related(
        "branch"
    ).order_by(
        "branch__name",
        "name"
    )

    return render(
        request,
        "organisation/floor_list.html",
        {
            "floors": floors
        }
    )


@group_required("Admin", "Manager")
def table_list(request):

    tables = (
        Table.objects
        .filter(is_deleted=False)
        .select_related(
            "floor",
            "floor__branch",
        )
        .order_by(
            "floor__branch__name",
            "floor__name",
            "name",
        )
    )

    for table in tables:
        table.active_session = (
            table.sessions.filter(status="OPEN")
            .order_by("-opened_at")
            .first()
        )

    return render(
        request,
        "organisation/table_list.html",
        {
            "tables": tables,
            "floors": Floor.objects.filter(is_active=True, is_deleted=False).select_related("branch").order_by("branch__name", "name"),
        }
    )


@group_required("Admin", "Manager")
def floor_layout(request, floor_id):
    floor = get_object_or_404(
        Floor.objects.select_related("branch"),
        id=floor_id,
    )

    tables = (
        Table.objects
        .filter(
            floor=floor,
            is_deleted=False,
        )
        .select_related("floor")
    )

    available_count = tables.filter(
        status=Table.Status.AVAILABLE
    ).count()

    occupied_count = tables.filter(
        status=Table.Status.OCCUPIED
    ).count()

    reserved_count = tables.filter(
        status=Table.Status.RESERVED
    ).count()

    cleaning_count = tables.filter(
        status=Table.Status.CLEANING
    ).count()

    total_tables = tables.count()

    grid_map = {
        (table.pos_x, table.pos_y): table
        for table in tables
    }

    context = {
        "floor": floor,
        "tables": tables,
        "grid_map": grid_map,
        "rows": floor.rows,
        "columns": floor.columns,
        "row_list": range(floor.rows),
        "col_list": range(floor.columns),
        "available_count": available_count,
        "occupied_count": occupied_count,
        "reserved_count": reserved_count,
        "cleaning_count": cleaning_count,
        "total_tables": total_tables,
    }

    return render(
        request,
        "organisation/floor_layout.html",
        context,
    )


@group_required("Admin", "Manager")
@require_POST
def assign_table_position(request):
    """
    Assign table position on floor grid.
    Includes validation layer.
    """

    table_id = request.POST.get("table_id")
    x = request.POST.get("x")
    y = request.POST.get("y")

    if table_id is None or x is None or y is None:
        return JsonResponse(
            {"error": "Missing parameters"},
            status=400
        )

    table = get_object_or_404(
        Table,
        id=table_id
    )

    try:
        x = int(x)
        y = int(y)

    except ValueError:
        return JsonResponse(
            {"error": "Invalid coordinates"},
            status=400
        )

    # =====================================
    # Floor Active Validation
    # =====================================

    if not table.floor.is_active:
        return JsonResponse(
            {"error": "Floor is inactive"},
            status=400
        )

    # =====================================
    # Grid Boundary Validation
    # =====================================

    if (
        x < 0
        or x >= table.floor.columns
        or y < 0
        or y >= table.floor.rows
    ):
        return JsonResponse(
            {"error": "Invalid grid position"},
            status=400
        )

    # =====================================
    # Collision Validation
    # =====================================
    other_tables = (
        Table.objects
        .filter(
            floor=table.floor,
            is_deleted=False,
        )
        .exclude(id=table.id)
    )

    target_cells = []

    for check_x in range(
        x,
        x + table.width
    ):
        for check_y in range(
            y,
            y + table.height
        ):
            target_cells.append(
                (check_x, check_y)
            )

    conflict = False

    for other in other_tables:

        other_cells = get_table_cells(other)

        if any(
            cell in other_cells
            for cell in target_cells
        ):
            conflict = True
            break

    if conflict:
        return JsonResponse(
            {
                "error":
                "Space occupied by another table"
            },
            status=400
        )

    # =====================================
    # Save Position
    # =====================================

    table.pos_x = x
    table.pos_y = y

    table.save(
        update_fields=[
            "pos_x",
            "pos_y",
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "table": table.name,
            "x": x,
            "y": y,
        }
    )


@group_required("Admin", "Manager")
@require_GET
def get_table_details(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
        is_deleted=False,
    )

    return JsonResponse(
        {
            "id": str(table.id),
            "name": table.name,
            "capacity": table.capacity,
            "shape": table.shape,
            "width": table.width,
            "height": table.height,
            "status": table.status,
            "is_active": table.is_active,
            "floor": table.floor.name,
            "branch": table.floor.branch.name,
            "pos_x": table.pos_x,
            "pos_y": table.pos_y,
        })


@group_required("Admin", "Manager")
@require_POST
def update_table_details(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
        is_deleted=False,
    )

    table.name = request.POST.get(
        "name",
        table.name
    )

    table.capacity = request.POST.get(
        "capacity",
        table.capacity
    )

    table.status = request.POST.get(
        "status",
        table.status
    )

    table.is_active = (
        request.POST.get("is_active")
        == "true"
    )

    table.save()

    return JsonResponse(
        {
            "success": True
        }
    )


@group_required("Admin", "Manager")
@require_GET
def table_details(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
        is_deleted=False,
    )

    return JsonResponse({
        "id": str(table.id),
        "name": table.name,
        "capacity": table.capacity,
        "shape": table.shape,
        "width": table.width,
        "height": table.height,
        "status": table.status,
        "is_active": table.is_active,
        "pos_x": table.pos_x,
        "pos_y": table.pos_y, })


@group_required("Admin", "Manager")
@require_POST
def update_table_ajax(request, table_id):

    table = get_object_or_404(
        Table,
        id=table_id,
        is_deleted=False,
    )

    table.name = request.POST.get(
        "name",
        table.name
    )

    table.capacity = int(
        request.POST.get(
            "capacity",
            table.capacity
        )
    )

    table.status = request.POST.get(
        "status",
        table.status
    )

    table.is_active = (
        request.POST.get("is_active")
        == "true"
    )
    table.shape = request.POST.get(
        "shape",
        table.shape
    )
    table.width = int(
        request.POST.get(
            "width",
            table.width
        )
    )

    table.height = int(
        request.POST.get(
            "height",
            table.height
        )
    )

    table.save()
    return JsonResponse({
        "success": True
    })


def get_table_cells(table):

    cells = []

    for x in range(
        table.pos_x,
        table.pos_x + table.width
    ):
        for y in range(
            table.pos_y,
            table.pos_y + table.height
        ):
            cells.append((x, y))

    return cells
