from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from django.db.models import Sum, Q
from staff.models import TimeEntry
from .models import PayrollPeriod, Payslip, SalaryStructure, PayslipAllowance, PayslipDeduction, AllowanceType, DeductionType, LeaveRequest, LeaveBalance, LeaveType


class PayrollService:
    @staticmethod
    @transaction.atomic
    def process_period(period_id):
        period = PayrollPeriod.objects.select_for_update().get(pk=period_id)
        if period.status != PayrollPeriod.Status.OPEN:
            raise ValueError("Period is not open for processing.")
        period.status = PayrollPeriod.Status.PROCESSING
        period.save(update_fields=["status"])

        from staff.models import StaffProfile
        staff_list = StaffProfile.objects.filter(branch=period.branch, status=StaffProfile.Status.ACTIVE)

        for staff in staff_list:
            salary = SalaryStructure.objects.filter(staff=staff, is_active=True).first()
            if not salary:
                continue

            entries = TimeEntry.objects.filter(
                staff=staff,
                clock_in__date__gte=period.start_date,
                clock_in__date__lte=period.end_date,
            )

            total_hours = sum((e.total_hours or 0) for e in entries)
            overtime_hours = sum((e.overtime_hours or 0) for e in entries)
            working_days = entries.values("clock_in__date").distinct().count()

            base_salary = Decimal(str(salary.base_salary))
            per_day = base_salary / Decimal("30")
            per_day_pay = per_day * Decimal(str(working_days))

            hourly = base_salary / Decimal("208") if base_salary else Decimal("0")
            overtime_pay = Decimal(str(overtime_hours)) * hourly * Decimal("1.5")

            approved_leaves = LeaveRequest.objects.filter(
                staff=staff,
                status=LeaveRequest.Status.APPROVED,
                start_date__lte=period.end_date,
                end_date__gte=period.start_date,
            ).select_related("leave_type")

            total_leave_days = 0
            unpaid_leave_days = 0
            for leave in approved_leaves:
                leave_start = max(leave.start_date, period.start_date)
                leave_end = min(leave.end_date, period.end_date)
                days = (leave_end - leave_start).days + 1
                total_leave_days += days
                if not leave.leave_type.is_paid:
                    unpaid_leave_days += days

            base_pay = base_salary
            if not salary.staff.is_full_time:
                base_pay = per_day_pay + overtime_pay

            if unpaid_leave_days > 0:
                unpaid_deduction = per_day * Decimal(str(unpaid_leave_days))
                base_pay = base_pay - unpaid_deduction

            if base_pay < 0:
                base_pay = Decimal("0")

            payslip, created = Payslip.objects.get_or_create(
                staff=staff, period=period,
                defaults={
                    "base_pay": base_pay,
                    "overtime_pay": overtime_pay,
                    "hours_worked": total_hours,
                    "status": Payslip.Status.DRAFT,
                },
            )

            if not created:
                payslip.base_pay = base_pay
                payslip.overtime_pay = overtime_pay
                payslip.hours_worked = total_hours
                payslip.save(update_fields=["base_pay", "overtime_pay", "hours_worked"])

            if created:
                for at in AllowanceType.objects.filter(is_active=True):
                    PayslipAllowance.objects.create(
                        payslip=payslip,
                        allowance_type=at,
                        amount=0,
                        description=f"Auto-created allowance: {at.name}",
                    )

                for dt in DeductionType.objects.filter(is_active=True):
                    amt = Decimal("0")
                    desc = f"Auto-created deduction: {dt.name}"
                    if "leave" in dt.name.lower() and unpaid_leave_days > 0:
                        amt = per_day * Decimal(str(unpaid_leave_days))
                        desc = f"Unpaid leave deduction ({unpaid_leave_days} days)"
                    PayslipDeduction.objects.create(
                        payslip=payslip,
                        deduction_type=dt,
                        amount=amt,
                        description=desc,
                    )

            tax_rate = Decimal("0.01")
            if base_pay > Decimal("50000"):
                tax_rate = Decimal("0.15")
            elif base_pay > Decimal("25000"):
                tax_rate = Decimal("0.05")

            payslip.tax_amount = base_pay * tax_rate
            PayrollService.calculate_payslip(payslip.id)

        period.status = PayrollPeriod.Status.CLOSED
        period.processed_at = timezone.now()
        period.save(update_fields=["status", "processed_at"])

    @staticmethod
    @transaction.atomic
    def calculate_payslip(payslip_id):
        payslip = Payslip.objects.select_for_update().get(pk=payslip_id)
        total_allowances = payslip.allowances.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        total_deductions = payslip.deductions.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        payslip.total_allowances = total_allowances
        payslip.total_deductions = total_deductions
        payslip.net_pay = payslip.base_pay + payslip.overtime_pay + total_allowances - total_deductions - payslip.tax_amount
        if payslip.net_pay < 0:
            payslip.net_pay = Decimal("0")
        payslip.save(update_fields=["total_allowances", "total_deductions", "net_pay"])
        return payslip
