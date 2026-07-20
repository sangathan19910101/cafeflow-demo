from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):

    help = "Create CafeFlow system roles."

    ROLES = [
        "Admin",
        "Manager",
        "Cashier",
        "Kitchen",
        "Waiter",
    ]

    def handle(self, *args, **options):

        for role_name in self.ROLES:

            group, created = Group.objects.get_or_create(
                name=role_name
            )

            if created:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created role: {role_name}"
                    )
                )

            else:

                self.stdout.write(
                    self.style.WARNING(
                        f"Already exists: {role_name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Role setup completed."
            )
        )
