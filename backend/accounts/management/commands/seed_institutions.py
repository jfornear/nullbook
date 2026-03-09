from django.core.management.base import BaseCommand

from accounts.models import Institution

# (name, institution_type, website, logo_url)
INSTITUTIONS = [
    # Banks
    ("Chase", "bank", "https://www.chase.com", "https://logo.clearbit.com/chase.com"),
    ("Bank of America", "bank", "https://www.bankofamerica.com", "https://logo.clearbit.com/bankofamerica.com"),
    ("Wells Fargo", "bank", "https://www.wellsfargo.com", "https://logo.clearbit.com/wellsfargo.com"),
    ("Citibank", "bank", "https://www.citi.com", "https://logo.clearbit.com/citi.com"),
    ("Capital One", "bank", "https://www.capitalone.com", "https://logo.clearbit.com/capitalone.com"),
    ("US Bank", "bank", "https://www.usbank.com", "https://logo.clearbit.com/usbank.com"),
    ("PNC", "bank", "https://www.pnc.com", "https://logo.clearbit.com/pnc.com"),
    ("TD Bank", "bank", "https://www.td.com", "https://logo.clearbit.com/td.com"),
    ("Ally Bank", "bank", "https://www.ally.com", "https://logo.clearbit.com/ally.com"),
    ("Discover", "bank", "https://www.discover.com", "https://logo.clearbit.com/discover.com"),
    ("Marcus (Goldman Sachs)", "bank", "https://www.marcus.com", "https://logo.clearbit.com/marcus.com"),
    ("SoFi", "bank", "https://www.sofi.com", "https://logo.clearbit.com/sofi.com"),
    ("Synchrony", "bank", "https://www.synchrony.com", "https://logo.clearbit.com/synchrony.com"),
    # Credit Unions
    ("USAA", "credit_union", "https://www.usaa.com", "https://logo.clearbit.com/usaa.com"),
    ("Navy Federal", "credit_union", "https://www.navyfederal.org", "https://logo.clearbit.com/navyfederal.org"),
    ("Pentagon Federal", "credit_union", "https://www.penfed.org", "https://logo.clearbit.com/penfed.org"),
    ("BECU", "credit_union", "https://www.becu.org", "https://logo.clearbit.com/becu.org"),
    # Brokerages
    ("Fidelity", "brokerage", "https://www.fidelity.com", "https://logo.clearbit.com/fidelity.com"),
    ("Charles Schwab", "brokerage", "https://www.schwab.com", "https://logo.clearbit.com/schwab.com"),
    ("Vanguard", "brokerage", "https://www.vanguard.com", "https://logo.clearbit.com/vanguard.com"),
    ("Robinhood", "brokerage", "https://www.robinhood.com", "https://logo.clearbit.com/robinhood.com"),
    ("E-Trade", "brokerage", "https://www.etrade.com", "https://logo.clearbit.com/etrade.com"),
    ("Interactive Brokers", "brokerage", "https://www.interactivebrokers.com", "https://logo.clearbit.com/interactivebrokers.com"),
    ("Webull", "brokerage", "https://www.webull.com", "https://logo.clearbit.com/webull.com"),
    ("Merrill Lynch", "brokerage", "https://www.ml.com", "https://logo.clearbit.com/ml.com"),
    ("Betterment", "brokerage", "https://www.betterment.com", "https://logo.clearbit.com/betterment.com"),
    ("Wealthfront", "brokerage", "https://www.wealthfront.com", "https://logo.clearbit.com/wealthfront.com"),
    ("Public", "brokerage", "https://www.public.com", "https://logo.clearbit.com/public.com"),
    ("M1 Finance", "brokerage", "https://www.m1finance.com", "https://logo.clearbit.com/m1finance.com"),
    # Crypto
    ("Coinbase", "crypto", "https://www.coinbase.com", "https://logo.clearbit.com/coinbase.com"),
    ("Kraken", "crypto", "https://www.kraken.com", "https://logo.clearbit.com/kraken.com"),
    ("Gemini", "crypto", "https://www.gemini.com", "https://logo.clearbit.com/gemini.com"),
]


class Command(BaseCommand):
    help = "Seed well-known financial institutions"

    def handle(self, *args, **options):
        created_count = 0

        for name, institution_type, website, logo_url in INSTITUTIONS:
            _, created = Institution.objects.get_or_create(
                name=name,
                defaults={
                    "institution_type": institution_type,
                    "website": website,
                    "logo_url": logo_url,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {name}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {created_count} institutions created.")
        )
