import random
import string
import calendar
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("en_CA")

_MONTH_ABBR_TO_NUM = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


class RandomGenerator:
    """
    Common random data generator for Playwright automation.
    """

    # -----------------------------
    # PERSON
    # -----------------------------

    @staticmethod
    def first_name():
        return fake.first_name()

    @staticmethod
    def last_name():
        return fake.last_name()

    @staticmethod
    def full_name():
        return fake.name()

    @staticmethod
    def email():
        return fake.email()

    _CANADIAN_AREA_CODES = (
        "416", "647", "437", "905", "604", "778", "250", "403", "587",
        "780", "514", "438", "613", "819", "902", "506", "709", "204", "306",
    )

    @staticmethod
    def phone():
        area = random.choice(RandomGenerator._CANADIAN_AREA_CODES)
        exchange = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"{area}{exchange}{line}"

    @staticmethod
    def _automation_stamp() -> tuple[str, str]:
        """Single clock read: deal stamp (with underscores) and matching email stamp."""
        deal_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_stamp = deal_stamp.replace("_", "")
        return deal_stamp, email_stamp

    @staticmethod
    def automation_email(*, deal_stamp: str | None = None) -> str:
        if deal_stamp is None:
            _, email_stamp = RandomGenerator._automation_stamp()
        else:
            email_stamp = deal_stamp.replace("_", "")
        return f"rabbia.elahi+automation{email_stamp}@fantechlabs.io"

    @staticmethod
    def lead_identity(
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict[str, str]:
        """Generate deal name + email from one shared timestamp."""
        first_name = first_name or fake.first_name()
        last_name = last_name or fake.last_name()
        deal_stamp, email_stamp = RandomGenerator._automation_stamp()
        # deal_name = f"{first_name} {last_name} Automation Deal {deal_stamp}"
        deal_name = f"{first_name} {last_name} Automation Deal"
        return {
            "first_name": first_name,
            "last_name": last_name + " " + "Automation Deal",
            "deal_name": deal_name,
            "enter_name": deal_name,
            "enter_email": f"rabbia.elahi+automation{email_stamp}@fantechlabs.io",
            "deal_stamp": deal_stamp,
        }

    @staticmethod
    def email_from_deal_stamp(deal_name: str) -> str | None:
        """Rebuild automation email from the timestamp embedded in a deal name."""
        import re

        match = re.search(r"Automation Deal (\d{8}_\d{6})\b", deal_name)
        if not match:
            return None
        return RandomGenerator.automation_email(deal_stamp=match.group(1))

    @staticmethod
    def deal_name():
        identity = RandomGenerator.lead_identity()
        return identity["deal_name"]

    @staticmethod
    def street_number():
        return str(random.randint(100, 9999))

    @staticmethod
    def company_name():
        return fake.company()

    @staticmethod
    def job_title():
        return fake.job()

    # -----------------------------
    # ADDRESS
    # -----------------------------

    @staticmethod
    def street():
        return fake.street_address()

    @staticmethod
    def city():
        return fake.city()

    @staticmethod
    def province():
        return fake.province()

    @staticmethod
    def postal_code():
        return fake.postcode()

    @staticmethod
    def canadian_postal_code() -> str:
        """Return a normalized Canadian postal code (e.g. K1A 0B1)."""
        from utils.wait_helpers import normalize_canadian_postal_code

        return normalize_canadian_postal_code(fake.postcode())

    @staticmethod
    def full_address():
        return fake.address().replace("\n", ", ")

    # -----------------------------
    # NUMBERS
    # -----------------------------

    @staticmethod
    def number(minimum=1, maximum=999999):
        return str(random.randint(minimum, maximum))

    @staticmethod
    def decimal(minimum=1, maximum=100, places=2):
        value = random.uniform(minimum, maximum)
        return f"{value:.{places}f}"

    @staticmethod
    def percentage(minimum=1, maximum=100):
        return str(random.randint(minimum, maximum))

    # -----------------------------
    # MORTGAGE
    # -----------------------------

    @staticmethod
    def loan_amount():
        return str(random.randint(50000, 900000))

    @staticmethod
    def property_value():
        return str(random.randint(150000, 2000000))

    @staticmethod
    def balance_owing():
        return str(random.randint(10000, 600000))

    @staticmethod
    def monthly_payment():
        return str(random.randint(500, 7000))

    @staticmethod
    def monthly_savings():
        return str(random.randint(0, 3000))

    @staticmethod
    def annual_income():
        return str(random.randint(35000, 250000))

    @staticmethod
    def interest_rate():
        return f"{random.uniform(1.50, 12.99):.2f}"

    @staticmethod
    def mortgage_years():
        return str(random.randint(5, 35))

    @staticmethod
    def term_requested():
        return str(random.randint(1, 30))

    # -----------------------------
    # CREDIT
    # -----------------------------

    @staticmethod
    def credit_score():
        return str(random.randint(300, 900))

    @staticmethod
    def tds_score():
        return str(random.randint(10, 55))

    @staticmethod
    def credit_utilization():
        return str(random.randint(1, 99))

    # -----------------------------
    # DATES
    # -----------------------------

    @staticmethod
    def birth_date(min_age=18, max_age=70):
        return fake.date_of_birth(
            minimum_age=min_age,
            maximum_age=max_age
        )

    @staticmethod
    def future_date():
        return fake.future_date()

    # -----------------------------
    # TEXT
    # -----------------------------

    @staticmethod
    def word():
        return fake.word()

    @staticmethod
    def sentence(words=8):
        return fake.sentence(nb_words=words)

    @staticmethod
    def paragraph(sentences=4):
        return fake.paragraph(nb_sentences=sentences)

    @staticmethod
    def short_note():
        return fake.text(max_nb_chars=80)

    # -----------------------------
    # IDs
    # -----------------------------

    @staticmethod
    def vfli_number():
        return str(random.randint(10000, 99999))

    @staticmethod
    def random_string(length=8):
        return ''.join(
            random.choices(
                string.ascii_letters + string.digits,
                k=length
            )
        )

    # -----------------------------
    # EMPLOYMENT
    # -----------------------------

    @staticmethod
    def employer():
        companies = [
            "Google",
            "Microsoft",
            "Amazon",
            "Apple",
            "Meta",
            "Tesla",
            "Fantech",
            "IBM",
            "Oracle",
            "Shopify"
        ]
        return random.choice(companies)

    # -----------------------------
    # BOOLEAN
    # -----------------------------

    @staticmethod
    def random_bool():
        return random.choice([True, False])

    # -----------------------------
    # Lists
    # -----------------------------

    @staticmethod
    def random_choice(values):
        return random.choice(values)


    #------------------------------
    # MAX MIN VALUES
    #------------------------------

    @staticmethod
    def max_value():
        return random.randint(150000, 2000000)

    @staticmethod
    def min_value():
        return random.randint(90000, 149999)


    @staticmethod
    def meeting_datetimes():
        start = datetime.now() + timedelta(
            days=random.randint(1, 30),
            hours=random.randint(9, 17)
        )

        end = start + timedelta(hours=1)

        return (
            start,
            end,
            start.strftime("%Y-%m-%dT%H:%M"),
            end.strftime("%Y-%m-%dT%H:%M")
        )
    
    @staticmethod
    def month():
        return random.choice(list(_MONTH_ABBR_TO_NUM.keys()))

    @staticmethod
    def year():
        return datetime.now().year

    @staticmethod
    def day(month=None, year=None):
        if month is not None and year is not None:
            month_num = _MONTH_ABBR_TO_NUM.get(str(month), 1)
            max_day = calendar.monthrange(int(year), month_num)[1]
            return str(random.randint(1, max_day))
        return str(random.randint(1, 28))

    @staticmethod
    def calendar_date_parts():
        """Return month, year, day that exist on the calendar (avoids Feb 29, etc.)."""
        month = RandomGenerator.month()
        year = RandomGenerator.year()
        day = RandomGenerator.day(month, year)
        return month, year, int(day)

    @staticmethod
    def birthday_form_parts(min_year=1970, max_year=2005):
        """Return numeric month, year, day safe for the create-lead date picker."""
        year = random.randint(min_year, max_year)
        month = random.randint(1, 12)
        max_day = calendar.monthrange(year, month)[1]
        day = random.randint(1, max_day)
        return str(month), str(year), str(day)



    