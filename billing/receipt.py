from datetime import datetime
from django.conf import settings
from pathlib import Path


class ReceiptService:
    @staticmethod
    def generate_receipt_text(bill):
        lines = []
        lines.append("=" * 40)
        lines.append("          CAFEFLOW POS")
        lines.append("=" * 40)
        lines.append(f"Bill #: {bill.id}")
        lines.append(f"Date: {bill.generated_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Table: {bill.session.table.name}")
        lines.append(f"Branch: {bill.session.table.floor.branch.name}")
        lines.append("-" * 40)
        lines.append(f"{'Item':<25} {'Qty':>5} {'Price':>8}")
        lines.append("-" * 40)

        for order in bill.session.orders.filter(status="ACCEPTED"):
            for item in order.items.all():
                name = item.menu_item.name[:24]
                lines.append(f"{name:<25} {item.quantity:>5} {item.line_total:>8.2f}")

        lines.append("-" * 40)
        lines.append(f"{'Subtotal:':<30} {bill.subtotal:>8.2f}")
        if bill.discount_amount:
            lines.append(f"{'Discount:':<30} -{bill.discount_amount:>7.2f}")
        lines.append(f"{'Tax (13%):':<30} {bill.tax_amount:>8.2f}")
        lines.append("=" * 40)
        lines.append(f"{'TOTAL DUE:':<30} {bill.grand_total:>8.2f}")
        lines.append("=" * 40)

        payment = getattr(bill, "payment", None)
        if payment:
            lines.append(f"Paid via: {payment.payment_method}")
            lines.append(f"Amount: {payment.amount_paid}")
            lines.append(f"Change: {payment.amount_paid - bill.grand_total:.2f}")

        lines.append("")
        lines.append("         Thank you!")
        lines.append("      Visit us again!")
        lines.append("=" * 40)
        return "\n".join(lines)

    @staticmethod
    def print_receipt(bill):
        text = ReceiptService.generate_receipt_text(bill)
        enabled = getattr(settings, "RECEIPT_PRINTER_ENABLED", False)
        if not enabled:
            return text

        printer_iface = getattr(settings, "RECEIPT_PRINTER_INTERFACE", "FILE")
        printer_path = getattr(settings, "RECEIPT_PRINTER_PATH", None)

        if printer_iface == "FILE" and printer_path:
            Path(printer_path).mkdir(parents=True, exist_ok=True)
            filename = f"receipt_{bill.id}_{datetime.now():%Y%m%d_%H%M%S}.txt"
            filepath = Path(printer_path) / filename
            filepath.write_text(text, encoding="utf-8")

        elif printer_iface == "THERMAL":
            try:
                import win32print
                printer = win32print.GetDefaultPrinter()
                win32print.StartDocPrinter(printer, 1, ("receipt", None, "RAW"))
                win32print.WritePrinter(printer, text.encode("utf-8"))
                win32print.EndDocPrinter(printer)
            except ImportError:
                pass

        return text
