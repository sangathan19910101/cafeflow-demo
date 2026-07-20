from django.db import migrations


def seed_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("payroll", "LeaveType")
    types = [
        ("Annual Leave", "Paid annual leave", 20, True),
        ("Sick Leave", "Paid sick leave", 12, True),
        ("Personal Leave", "Leave for personal reasons", 5, True),
        ("Maternity Leave", "Maternity leave as per policy", 90, True),
        ("Paternity Leave", "Paternity leave as per policy", 10, True),
        ("Bereavement Leave", "Leave on loss of family member", 5, True),
        ("Unpaid Leave", "Leave without pay", 0, False),
    ]
    for name, desc, days, paid in types:
        LeaveType.objects.get_or_create(
            name=name,
            defaults={
                "description": desc,
                "days_per_year": days,
                "is_paid": paid,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("payroll", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(seed_leave_types),
    ]
