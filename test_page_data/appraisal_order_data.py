from faker import Faker
from datetime import datetime, timedelta
import random
from test_page_data.random_gen_data import RandomGenerator as RG
from utils.wait_helpers import RELIABLE_PLACES_QUERIES

fake = Faker()

# Full address — short numeric queries (e.g. "724") fail Places autocomplete and leave city empty.
APPRAISAL_LOCATION_QUERY = RELIABLE_PLACES_QUERIES[0]


class AppraisalOrderData:

    def __init__(self):

        # NO Flow
        self.reason = fake.sentence(nb_words=6)

        # YES Flow
        self.company = fake.company()

        # self.location = "724"

        self.location = APPRAISAL_LOCATION_QUERY

        self.ltv = str(random.randint(30, 90))

        self.ordered_date = datetime.now() + timedelta(
            days=random.randint(1, 5)
        )
        

        self.completed_date = self.ordered_date + timedelta(
            days=random.randint(1, 10)
        )

        self.month, self.year, self.day = RG.calendar_date_parts()