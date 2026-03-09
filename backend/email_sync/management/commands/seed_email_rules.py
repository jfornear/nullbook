from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from email_sync.default_rules import DEFAULT_RULES
from email_sync.models import EmailRule

User = get_user_model()


class Command(BaseCommand):
    help = "Seed default email rules for a user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="Username to create rules for. Defaults to the first user.",
        )

    def handle(self, *args, **options):
        username = options["username"]

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist.')
        else:
            user = User.objects.first()
            if not user:
                raise CommandError("No users found. Create a user first.")

        created_count = 0

        for rule_data in DEFAULT_RULES:
            rule, created = EmailRule.objects.get_or_create(
                user=user,
                name=rule_data["name"],
                defaults={
                    "from_pattern": rule_data.get("from_pattern", ""),
                    "subject_pattern": rule_data.get("subject_pattern", ""),
                    "action": rule_data["action"],
                    "priority": rule_data["priority"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created rule: {rule.name}")
            else:
                self.stdout.write(f"  Skipped (exists): {rule.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_count} email rules created for user '{user.username}'."
            )
        )
