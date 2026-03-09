from django.core.management.base import BaseCommand

from transactions.models import Category

# (parent_name, icon), [(child_name, icon), ...]
CATEGORY_TREE = [
    (
        ("Income", "dollar-sign"),
        [
            ("Salary", "briefcase"),
            ("Freelance", "edit"),
            ("Investment Income", "trending-up"),
            ("Rental Income", "home"),
            ("Refunds", "rotate-ccw"),
            ("Other Income", "plus-circle"),
        ],
    ),
    (
        ("Housing", "home"),
        [
            ("Rent/Mortgage", "key"),
            ("Property Tax", "landmark"),
            ("Home Insurance", "shield"),
            ("Maintenance", "wrench"),
            ("Utilities", "zap"),
        ],
    ),
    (
        ("Transportation", "car"),
        [
            ("Gas", "fuel"),
            ("Car Payment", "credit-card"),
            ("Car Insurance", "shield"),
            ("Parking", "square"),
            ("Public Transit", "train-front"),
            ("Rideshare", "map-pin"),
        ],
    ),
    (
        ("Food", "utensils"),
        [
            ("Groceries", "shopping-cart"),
            ("Restaurants", "utensils-crossed"),
            ("Coffee Shops", "coffee"),
            ("Delivery", "package"),
        ],
    ),
    (
        ("Healthcare", "heart-pulse"),
        [
            ("Doctor", "stethoscope"),
            ("Dentist", "smile"),
            ("Pharmacy", "pill"),
            ("Health Insurance", "shield-plus"),
        ],
    ),
    (
        ("Entertainment", "gamepad-2"),
        [
            ("Streaming", "tv"),
            ("Events", "ticket"),
            ("Hobbies", "palette"),
            ("Books", "book-open"),
        ],
    ),
    (
        ("Shopping", "shopping-bag"),
        [
            ("Clothing", "shirt"),
            ("Electronics", "smartphone"),
            ("Home Goods", "lamp"),
        ],
    ),
    (
        ("Financial", "landmark"),
        [
            ("Bank Fees", "alert-circle"),
            ("Interest", "percent"),
            ("Insurance", "shield-check"),
        ],
    ),
    (
        ("Travel", "plane"),
        [
            ("Flights", "plane-takeoff"),
            ("Hotels", "bed"),
            ("Activities", "compass"),
        ],
    ),
    (
        ("Education", "graduation-cap"),
        [
            ("Tuition", "school"),
            ("Courses", "book"),
            ("Supplies", "pencil"),
        ],
    ),
    (
        ("Personal", "user"),
        [
            ("Gifts", "gift"),
            ("Donations", "heart"),
            ("Subscriptions", "repeat"),
        ],
    ),
]


class Command(BaseCommand):
    help = "Seed default transaction categories"

    def handle(self, *args, **options):
        created_count = 0

        for (parent_name, parent_icon), children in CATEGORY_TREE:
            parent, created = Category.objects.get_or_create(
                name=parent_name,
                parent=None,
                defaults={"icon": parent_icon},
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created parent: {parent_name}")

            for child_name, child_icon in children:
                child, created = Category.objects.get_or_create(
                    name=child_name,
                    parent=parent,
                    defaults={"icon": child_icon},
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"    Created: {child_name}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {created_count} categories created.")
        )
