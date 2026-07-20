from decimal import Decimal
from datetime import date, datetime
from django.db import transaction
from django.db.models import Sum, Q, Count, Avg, F as djF
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from organisation.models import Branch, Floor, Table, TableSession
from menu.models import MenuItem, MenuCategory, ModifierGroup, Modifier, TaxCategory
from orders.models import Order, OrderItem, OrderItemModifier
from orders.services import OrderService
from billing.models import Bill, Payment
from billing.services import BillingService
from billing.workflows import SessionWorkflowService
from crm.models import Customer, CustomerFeedback, CustomerLoyalty
from crm.services import CRMService
from coupons.models import Coupon
from coupons.services import CouponService
from kds.models import KDSDisplay, KDSStation, KDSItem
from kds.services import KDSService
from inventory.models import InventoryItem, StockCategory, StockUnit, StockMovement, MenuItemRecipe, StockTransfer
from inventory.services import InventoryService
from reservations.models import Reservation, WaitlistEntry
from reservations.services import ReservationService
from staff.models import StaffProfile, Department, ShiftTemplate, ShiftAssignment, TimeEntry
from payroll.models import PayrollPeriod, Payslip, LeaveRequest, LeaveType, SalaryStructure
from suppliers.models import Supplier, PurchaseOrder, GoodsReceipt, SupplierPricing
from operations.models import Expense, ExpenseCategory, CashRegister, DayEndSummary
from reports.models import ReportTemplate, ScheduledReport
from .serializers import (
    BranchSerializer, FloorSerializer, TableSerializer,
    MenuCategorySerializer, MenuItemSerializer, ModifierGroupSerializer, ModifierSerializer, TaxCategorySerializer,
    OrderSerializer, OrderItemSerializer, OrderItemModifierSerializer,
    TableSessionSerializer, BillSerializer, PaymentSerializer, QuickSaleItemSerializer,
    CustomerSerializer, CustomerLoyaltySerializer, CustomerFeedbackSerializer,
    ReservationSerializer, WaitlistEntrySerializer,
    CouponSerializer, KDSDisplaySerializer, KDSStationSerializer, KDSItemSerializer,
    InventoryItemSerializer, StockCategorySerializer, StockUnitSerializer,
    StockMovementSerializer, MenuItemRecipeSerializer,
    DepartmentSerializer, StaffProfileSerializer, ShiftTemplateSerializer,
    ShiftAssignmentSerializer, TimeEntrySerializer,
    SalaryStructureSerializer, PayrollPeriodSerializer, PayslipSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer,
    SupplierSerializer, SupplierPricingSerializer, PurchaseOrderSerializer, GoodsReceiptSerializer,
    ExpenseCategorySerializer, ExpenseSerializer, CashRegisterSerializer, DayEndSummarySerializer,
    ReportTemplateSerializer, ScheduledReportSerializer,
    ApplyCouponSerializer, CreateOrderItemSerializer,
)


class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Branch.objects.filter(is_deleted=False, is_active=True)
    serializer_class = BranchSerializer


class FloorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FloorSerializer

    def get_queryset(self):
        qs = Floor.objects.filter(is_deleted=False, is_active=True)
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs


class TableViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TableSerializer

    def get_queryset(self):
        qs = Table.objects.filter(is_deleted=False)
        floor_id = self.request.query_params.get("floor_id")
        status_filter = self.request.query_params.get("status")
        if floor_id:
            qs = qs.filter(floor_id=floor_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class MenuCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuCategory.objects.filter(is_active=True, is_deleted=False)
    serializer_class = MenuCategorySerializer


class ModifierGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModifierGroup.objects.filter(is_active=True)
    serializer_class = ModifierGroupSerializer


class ModifierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Modifier.objects.filter(is_active=True)
    serializer_class = ModifierSerializer

    def get_queryset(self):
        qs = Modifier.objects.filter(is_active=True)
        group_id = self.request.query_params.get("group_id")
        if group_id:
            qs = qs.filter(group_id=group_id)
        return qs


class TaxCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaxCategory.objects.filter(is_active=True)
    serializer_class = TaxCategorySerializer


class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        qs = MenuItem.objects.filter(is_deleted=False).select_related("category", "tax_category")
        category_id = self.request.query_params.get("category_id")
        available = self.request.query_params.get("available")
        if category_id:
            qs = qs.filter(category_id=category_id)
        if available:
            qs = qs.filter(is_available=True)
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.select_related("session__table__floor__branch", "customer").prefetch_related(
            "items__menu_item", "items__modifiers__modifier"
        )
        session_id = self.request.query_params.get("session_id")
        status_filter = self.request.query_params.get("status")
        order_type = self.request.query_params.get("order_type")
        if session_id:
            qs = qs.filter(session_id=session_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if order_type:
            qs = qs.filter(order_type=order_type)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        session_id = self.request.data.get("session_id")
        if session_id:
            session = TableSession.objects.get(pk=session_id)
            order = OrderService.create_order(session)
        else:
            order_type = self.request.data.get("order_type", "TAKEAWAY")
            order = Order.objects.create(order_type=order_type)
        serializer.instance = order

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        order = self.get_object()
        ser = CreateOrderItemSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            menu_item = MenuItem.objects.get(pk=ser.validated_data["menu_item_id"])
            OrderService.add_item(
                order=order, menu_item=menu_item,
                quantity=ser.validated_data["quantity"],
                notes=ser.validated_data.get("notes", ""),
            )
            return Response({"status": "item added"}, status=status.HTTP_201_CREATED)
        except (MenuItem.DoesNotExist, ValueError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.submit_order(order)
            KDSService.create_kds_entry(order)
            return Response({"status": "submitted", "order_number": order.order_number})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.accept_order(order)
            return Response({"status": "accepted"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            OrderService.cancel_order(order)
            return Response({"status": "cancelled"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TableSessionSerializer

    def get_queryset(self):
        qs = TableSession.objects.select_related("table__floor__branch")
        status_filter = self.request.query_params.get("status", "OPEN")
        qs = qs.filter(status=status_filter)
        return qs.order_by("-opened_at")

    @action(detail=False, methods=["post"])
    def start(self, request):
        table_id = request.data.get("table_id")
        from operations.services import SessionService
        try:
            table = Table.objects.get(pk=table_id)
            session = SessionService.start_session(table)
            return Response({"id": str(session.id), "status": "started"}, status=status.HTTP_201_CREATED)
        except (Table.DoesNotExist, ValueError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_object()
        try:
            session, bill = SessionWorkflowService.close_session(session)
            return Response({"session_id": str(session.id), "bill_id": str(bill.id)})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BillSerializer

    def get_queryset(self):
        qs = Bill.objects.select_related("session__table__floor__branch", "customer", "branch").prefetch_related(
            "payments", "quick_items"
        )
        branch_id = self.request.query_params.get("branch_id")
        status_filter = self.request.query_params.get("status")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-generated_at")

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        bill = self.get_object()
        method = request.data.get("method", "CASH")
        amount = request.data.get("amount", str(bill.grand_total))
        reference = request.data.get("reference_number", "")
        try:
            BillingService.record_payment(
                bill=bill, amount_paid=Decimal(amount),
                payment_method=method, reference_number=reference,
            )
            return Response({"status": "paid"})
        except (ValueError, DecimalException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def quick_sale(self, request):
        branch_id = request.data.get("branch_id")
        items = request.data.get("items", [])
        try:
            bill = BillingService.create_quick_sale(branch_id, items)
            return Response({"bill_id": str(bill.id), "bill_number": bill.bill_number})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-created_at")
    serializer_class = CustomerSerializer
    search_fields = ("name", "phone", "email")

    def get_queryset(self):
        qs = Customer.objects.all()
        search = self.request.query_params.get("search")
        vip = self.request.query_params.get("vip")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search))
        if vip:
            qs = qs.filter(is_vip=True)
        return qs.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def record_visit(self, request, pk=None):
        amount = request.data.get("amount", 0)
        branch_id = request.data.get("branch_id")
        branch = Branch.objects.filter(pk=branch_id).first() if branch_id else None
        CRMService.record_visit(pk, amount_spent=amount, branch=branch)
        return Response({"status": "visit recorded"})


class CustomerLoyaltyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomerLoyaltySerializer

    def get_queryset(self):
        return CustomerLoyalty.objects.select_related("customer", "program").all()


class CustomerFeedbackViewSet(viewsets.ModelViewSet):
    queryset = CustomerFeedback.objects.all()
    serializer_class = CustomerFeedbackSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        qs = Reservation.objects.select_related("customer", "branch")
        status_filter = self.request.query_params.get("status")
        date_filter = self.request.query_params.get("date")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_filter:
            qs = qs.filter(reservation_date=date_filter)
        return qs.order_by("reservation_date", "reservation_time")

    def perform_create(self, serializer):
        from organisation.models import Branch as Br
        customer_data = {
            "name": self.request.data.get("customer_name", ""),
            "phone": self.request.data.get("customer_phone", ""),
            "email": self.request.data.get("customer_email", ""),
        }
        reservation_data = {
            "branch": Br.objects.get(pk=self.request.data["branch_id"]),
            "guest_count": self.request.data["guest_count"],
            "reservation_date": datetime.strptime(self.request.data["reservation_date"], "%Y-%m-%d").date(),
            "reservation_time": datetime.strptime(self.request.data["reservation_time"], "%H:%M").time(),
            "duration_minutes": self.request.data.get("duration_minutes", 120),
            "special_requests": self.request.data.get("special_requests", ""),
            "table_ids": self.request.data.get("table_ids"),
        }
        reservation = ReservationService.create_reservation(customer_data, reservation_data)
        serializer.instance = reservation

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            ReservationService.confirm_reservation(pk)
            return Response({"status": "confirmed"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        try:
            ReservationService.cancel_reservation(pk, request.data.get("reason", ""))
            return Response({"status": "cancelled"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WaitlistEntryViewSet(viewsets.ModelViewSet):
    queryset = WaitlistEntry.objects.all()
    serializer_class = WaitlistEntrySerializer

    @action(detail=True, methods=["post"])
    def notify(self, request, pk=None):
        entry = self.get_object()
        entry.status = WaitlistEntry.Status.NOTIFIED
        entry.notified_at = timezone.now()
        entry.save(update_fields=["status", "notified_at"])
        return Response({"status": "notified"})


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer

    @action(detail=False, methods=["post"])
    def validate(self, request):
        ser = ApplyCouponSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            discount = CouponService.validate_and_apply(
                ser.validated_data["code"], ser.validated_data["subtotal"],
            )
            return Response({"valid": True, "discount": str(discount)})
        except ValueError as e:
            return Response({"valid": False, "error": str(e)})


class KDSStationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KDSStation.objects.filter(is_active=True)
    serializer_class = KDSStationSerializer

    def get_queryset(self):
        qs = KDSStation.objects.filter(is_active=True)
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs


class KDSViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = KDSDisplaySerializer

    def get_queryset(self):
        qs = KDSDisplay.objects.select_related(
            "order__session__table__floor__branch", "branch", "station"
        ).prefetch_related("kds_items")
        status_filter = self.request.query_params.get("status")
        branch_id = self.request.query_params.get("branch_id")
        station_id = self.request.query_params.get("station_id")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if station_id:
            qs = qs.filter(station_id=station_id)
        return qs.order_by("-is_urgent", "priority", "created_at")

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        try:
            KDSService.start_preparing(pk)
            return Response({"status": "preparing"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def ready(self, request, pk=None):
        try:
            KDSService.mark_ready(pk)
            return Response({"status": "ready"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def served(self, request, pk=None):
        try:
            KDSService.mark_served(pk)
            return Response({"status": "served"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockCategory.objects.all()
    serializer_class = StockCategorySerializer


class StockUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockUnit.objects.all()
    serializer_class = StockUnitSerializer


class InventoryItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        qs = InventoryItem.objects.select_related("category", "unit", "branch").filter(is_active=True)
        branch_id = self.request.query_params.get("branch_id")
        low_stock = self.request.query_params.get("low_stock")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if low_stock:
            qs = qs.filter(quantity_in_stock__lte=djF("low_stock_threshold"))
        return qs

    @action(detail=True, methods=["post"])
    def restock(self, request, pk=None):
        try:
            qty = Decimal(request.data.get("quantity", 0))
            item = InventoryService.restock(pk, qty, request.data.get("notes", ""), request.user)
            return Response({"status": "restocked", "new_quantity": str(item.quantity_in_stock)})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        qs = StockMovement.objects.select_related("item").all()
        item_id = self.request.query_params.get("item_id")
        if item_id:
            qs = qs.filter(item_id=item_id)
        return qs.order_by("-created_at")


class MenuItemRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MenuItemRecipeSerializer

    def get_queryset(self):
        qs = MenuItemRecipe.objects.select_related("menu_item", "inventory_item").all()
        menu_item_id = self.request.query_params.get("menu_item_id")
        if menu_item_id:
            qs = qs.filter(menu_item_id=menu_item_id)
        return qs


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class StaffProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StaffProfileSerializer

    def get_queryset(self):
        qs = StaffProfile.objects.select_related("user", "department", "branch").all()
        branch_id = self.request.query_params.get("branch_id")
        status_filter = self.request.query_params.get("status")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ShiftAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShiftAssignmentSerializer

    def get_queryset(self):
        qs = ShiftAssignment.objects.select_related("staff__user", "template").all()
        date_filter = self.request.query_params.get("date")
        staff_id = self.request.query_params.get("staff_id")
        if date_filter:
            qs = qs.filter(date=date_filter)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs.order_by("date", "template__start_time")


class TimeEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        qs = TimeEntry.objects.select_related("staff__user").all()
        date_filter = self.request.query_params.get("date")
        staff_id = self.request.query_params.get("staff_id")
        if date_filter:
            qs = qs.filter(clock_in__date=date_filter)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs.order_by("-clock_in")


class PayrollPeriodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PayrollPeriod.objects.select_related("branch").all()
    serializer_class = PayrollPeriodSerializer


class PayslipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PayslipSerializer

    def get_queryset(self):
        qs = Payslip.objects.select_related("staff__user", "period").all()
        period_id = self.request.query_params.get("period_id")
        staff_id = self.request.query_params.get("staff_id")
        if period_id:
            qs = qs.filter(period_id=period_id)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs


class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related("staff__user", "leave_type").all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = LeaveRequest.Status.APPROVED
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save(update_fields=["status", "approved_by", "approved_at"])
        return Response({"status": "approved"})


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get_queryset(self):
        qs = Supplier.objects.all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("name")


class SupplierPricingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierPricingSerializer

    def get_queryset(self):
        qs = SupplierPricing.objects.select_related("supplier", "item").all()
        supplier_id = self.request.query_params.get("supplier_id")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs


class PurchaseOrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related("supplier", "branch").all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-order_date")


class GoodsReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GoodsReceiptSerializer

    def get_queryset(self):
        qs = GoodsReceipt.objects.select_related("purchase_order").all()
        po_id = self.request.query_params.get("po_id")
        if po_id:
            qs = qs.filter(purchase_order_id=po_id)
        return qs.order_by("-received_date")


class ExpenseCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExpenseCategory.objects.filter(is_active=True)
    serializer_class = ExpenseCategorySerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = Expense.objects.select_related("category", "branch").all()
        branch_id = self.request.query_params.get("branch_id")
        category_id = self.request.query_params.get("category_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs.order_by("-expense_date")


class CashRegisterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CashRegisterSerializer

    def get_queryset(self):
        qs = CashRegister.objects.select_related("branch").all()
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs


class DayEndSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DayEndSummarySerializer

    def get_queryset(self):
        qs = DayEndSummary.objects.select_related("branch").all()
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs.order_by("-summary_date")


class ReportTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportTemplate.objects.filter(is_active=True)
    serializer_class = ReportTemplateSerializer

    def get_queryset(self):
        qs = ReportTemplate.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class ScheduledReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScheduledReport.objects.select_related("report").all()
    serializer_class = ScheduledReportSerializer



