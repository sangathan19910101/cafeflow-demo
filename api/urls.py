from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BranchViewSet, FloorViewSet, TableViewSet,
    MenuCategoryViewSet, MenuItemViewSet, ModifierGroupViewSet, ModifierViewSet, TaxCategoryViewSet,
    OrderViewSet, SessionViewSet, BillViewSet,
    CustomerViewSet, CustomerLoyaltyViewSet, CustomerFeedbackViewSet,
    ReservationViewSet, WaitlistEntryViewSet,
    CouponViewSet, KDSViewSet, KDSStationViewSet,
    StockCategoryViewSet, StockUnitViewSet, InventoryItemViewSet,
    StockMovementViewSet, MenuItemRecipeViewSet,
    DepartmentViewSet, StaffProfileViewSet, ShiftAssignmentViewSet, TimeEntryViewSet,
    PayrollPeriodViewSet, PayslipViewSet, LeaveTypeViewSet, LeaveRequestViewSet,
    SupplierViewSet, SupplierPricingViewSet, PurchaseOrderViewSet, GoodsReceiptViewSet,
    ExpenseCategoryViewSet, ExpenseViewSet, CashRegisterViewSet, DayEndSummaryViewSet,
    ReportTemplateViewSet, ScheduledReportViewSet,
)

router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="api-branch")
router.register(r"floors", FloorViewSet, basename="api-floor")
router.register(r"tables", TableViewSet, basename="api-table")
router.register(r"menu-categories", MenuCategoryViewSet, basename="api-menucategory")
router.register(r"menu-items", MenuItemViewSet, basename="api-menuitem")
router.register(r"modifier-groups", ModifierGroupViewSet, basename="api-modifiergroup")
router.register(r"modifiers", ModifierViewSet, basename="api-modifier")
router.register(r"tax-categories", TaxCategoryViewSet, basename="api-taxcategory")
router.register(r"orders", OrderViewSet, basename="api-order")
router.register(r"sessions", SessionViewSet, basename="api-session")
router.register(r"bills", BillViewSet, basename="api-bill")
router.register(r"customers", CustomerViewSet, basename="api-customer")
router.register(r"customer-loyalty", CustomerLoyaltyViewSet, basename="api-customerloyalty")
router.register(r"customer-feedback", CustomerFeedbackViewSet, basename="api-customerfeedback")
router.register(r"reservations", ReservationViewSet, basename="api-reservation")
router.register(r"waitlist", WaitlistEntryViewSet, basename="api-waitlist")
router.register(r"coupons", CouponViewSet, basename="api-coupon")
router.register(r"kds", KDSViewSet, basename="api-kds")
router.register(r"kds-stations", KDSStationViewSet, basename="api-kdsstation")
router.register(r"stock-categories", StockCategoryViewSet, basename="api-stockcategory")
router.register(r"stock-units", StockUnitViewSet, basename="api-stockunit")
router.register(r"inventory", InventoryItemViewSet, basename="api-inventory")
router.register(r"stock-movements", StockMovementViewSet, basename="api-stockmovement")
router.register(r"menu-item-recipes", MenuItemRecipeViewSet, basename="api-menuitemrecipe")
router.register(r"departments", DepartmentViewSet, basename="api-department")
router.register(r"staff", StaffProfileViewSet, basename="api-staff")
router.register(r"shift-assignments", ShiftAssignmentViewSet, basename="api-shiftassignment")
router.register(r"time-entries", TimeEntryViewSet, basename="api-timeentry")
router.register(r"payroll-periods", PayrollPeriodViewSet, basename="api-payrollperiod")
router.register(r"payslips", PayslipViewSet, basename="api-payslip")
router.register(r"leave-types", LeaveTypeViewSet, basename="api-leavetype")
router.register(r"leave-requests", LeaveRequestViewSet, basename="api-leaverequest")
router.register(r"suppliers", SupplierViewSet, basename="api-supplier")
router.register(r"supplier-pricing", SupplierPricingViewSet, basename="api-supplierpricing")
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="api-purchaseorder")
router.register(r"goods-receipts", GoodsReceiptViewSet, basename="api-goodsreceipt")
router.register(r"expense-categories", ExpenseCategoryViewSet, basename="api-expensecategory")
router.register(r"expenses", ExpenseViewSet, basename="api-expense")
router.register(r"cash-registers", CashRegisterViewSet, basename="api-cashregister")
router.register(r"day-end-summaries", DayEndSummaryViewSet, basename="api-dayend")
router.register(r"report-templates", ReportTemplateViewSet, basename="api-reporttemplate")
router.register(r"scheduled-reports", ScheduledReportViewSet, basename="api-scheduledreport")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
]
