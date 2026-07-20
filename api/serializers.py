from rest_framework import serializers
from organisation.models import Branch, Floor, Table, TableSession
from menu.models import MenuItem, MenuCategory, ModifierGroup, Modifier, TaxCategory
from orders.models import Order, OrderItem, OrderItemModifier
from billing.models import Bill, Payment, QuickSaleItem
from crm.models import Customer, CustomerFeedback, CustomerLoyalty, LoyaltyProgram
from coupons.models import Coupon
from kds.models import KDSDisplay, KDSStation, KDSItem
from inventory.models import InventoryItem, StockCategory, StockUnit, StockMovement, MenuItemRecipe
from reservations.models import Reservation, WaitlistEntry
from staff.models import StaffProfile, Department, ShiftTemplate, ShiftAssignment, TimeEntry
from payroll.models import PayrollPeriod, Payslip, LeaveRequest, LeaveType, SalaryStructure
from suppliers.models import Supplier, PurchaseOrder, GoodsReceipt, SupplierPricing
from operations.models import Expense, ExpenseCategory, CashRegister, DayEndSummary
from reports.models import ReportTemplate, ScheduledReport


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class FloorSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Floor
        fields = "__all__"


class TableSerializer(serializers.ModelSerializer):
    floor_name = serializers.CharField(source="floor.name", read_only=True)
    branch_name = serializers.CharField(source="floor.branch.name", read_only=True)

    class Meta:
        model = Table
        fields = "__all__"


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = "__all__"


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = "__all__"


class ModifierGroupSerializer(serializers.ModelSerializer):
    modifiers = ModifierSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = "__all__"


class TaxCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxCategory
        fields = "__all__"


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
    profit_margin = serializers.FloatField(read_only=True)

    class Meta:
        model = MenuItem
        fields = "__all__"


class OrderItemModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemModifier
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    modifiers = OrderItemModifierSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def get_table_name(self, obj):
        return obj.session.table.name if obj.session else None

    def get_branch_name(self, obj):
        if obj.session:
            return obj.session.table.floor.branch.name
        return None


class TableSessionSerializer(serializers.ModelSerializer):
    table_name = serializers.CharField(source="table.name", read_only=True)
    branch_name = serializers.CharField(source="table.floor.branch.name", read_only=True)
    bill_id = serializers.SerializerMethodField()

    class Meta:
        model = TableSession
        fields = "__all__"

    def get_bill_id(self, obj) -> str | None:
        return str(getattr(obj, "bill_id", "")) or None


class QuickSaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickSaleItem
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class BillSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    quick_items = QuickSaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class CustomerLoyaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerLoyalty
        fields = "__all__"


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"


class WaitlistEntrySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = WaitlistEntry
        fields = "__all__"


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class KDSStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = KDSStation
        fields = "__all__"


class KDSItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = KDSItem
        fields = "__all__"


class KDSDisplaySerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source="order", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    kds_items = KDSItemSerializer(many=True, read_only=True)

    class Meta:
        model = KDSDisplay
        fields = "__all__"


class StockCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCategory
        fields = "__all__"


class StockUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockUnit
        fields = "__all__"


class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    unit_name = serializers.CharField(source="unit.abbreviation", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = "__all__"


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = "__all__"


class MenuItemRecipeSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source="inventory_item.name", read_only=True)

    class Meta:
        model = MenuItemRecipe
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class StaffProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = StaffProfile
        fields = "__all__"


class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = "__all__"


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.user.get_full_name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = "__all__"


class TimeEntrySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.user.get_full_name", read_only=True)

    class Meta:
        model = TimeEntry
        fields = "__all__"


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = "__all__"


class PayrollPeriodSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = "__all__"


class PayslipSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.user.get_full_name", read_only=True)
    period_name = serializers.CharField(source="period.name", read_only=True)

    class Meta:
        model = Payslip
        fields = "__all__"


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.user.get_full_name", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class SupplierPricingSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = SupplierPricing
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = "__all__"


class GoodsReceiptSerializer(serializers.ModelSerializer):
    po_number = serializers.CharField(source="purchase_order.po_number", read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = "__all__"


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = "__all__"


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Expense
        fields = "__all__"


class CashRegisterSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = CashRegister
        fields = "__all__"


class DayEndSummarySerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = DayEndSummary
        fields = "__all__"


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"


class ScheduledReportSerializer(serializers.ModelSerializer):
    report_name = serializers.CharField(source="report.name", read_only=True)

    class Meta:
        model = ScheduledReport
        fields = "__all__"


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateOrderItemSerializer(serializers.Serializer):
    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    notes = serializers.CharField(required=False, allow_blank=True)


class DashboardStatsSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    open_sessions = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    active_staff = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
