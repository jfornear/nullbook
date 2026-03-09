import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import UserSettings

User = get_user_model()


class Command(BaseCommand):
    help = "Create a local superuser from environment variables"

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None)
        parser.add_argument("--password", default=None)

    def handle(self, *args, **options):
        username = options["username"] or os.environ.get("NULLBOOK_ADMIN_USER", "dev")
        password = options["password"] or os.environ.get("NULLBOOK_ADMIN_PASSWORD", "nullbook-local")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@localhost",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {username}"))
        else:
            self.stdout.write(f"Superuser '{username}' already exists.")

        settings_obj, settings_created = UserSettings.objects.get_or_create(user=user)
        if settings_created:
            self.stdout.write(self.style.SUCCESS("Created UserSettings for admin."))
