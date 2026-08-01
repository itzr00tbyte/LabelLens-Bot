import random
import re
from typing import Tuple

ZIP_CITY_STATE_MAP = {
    "90210": ("Beverly Hills", "CA"),
    "10001": ("New York", "NY"),
    "10002": ("New York", "NY"),
    "30301": ("Atlanta", "GA"),
    "60601": ("Chicago", "IL"),
    "75001": ("Dallas", "TX"),
    "94102": ("San Francisco", "CA"),
    "33101": ("Miami", "FL"),
    "02108": ("Boston", "MA"),
    "98101": ("Seattle", "WA"),
    "80202": ("Denver", "CO"),
    "37201": ("Nashville", "TN"),
    "70112": ("New Orleans", "LA"),
    "89101": ("Las Vegas", "NV"),
    "19102": ("Philadelphia", "PA"),
    "85001": ("Phoenix", "AZ"),
    "97201": ("Portland", "OR"),
    "55401": ("Minneapolis", "MN"),
    "63101": ("St. Louis", "MO"),
    "20001": ("Washington", "DC"),
    "43215": ("Columbus", "OH"),
    "48226": ("Detroit", "MI"),
    "77002": ("Houston", "TX"),
    "30309": ("Atlanta", "GA"),
    "90001": ("Los Angeles", "CA"),
    "90012": ("Los Angeles", "CA"),
}

STREET_NAMES = [
    "Main Street",
    "Oak Avenue",
    "Maple Drive",
    "Washington Boulevard",
    "Park Avenue",
    "Cedar Lane",
    "Pine Road",
    "Elm Street",
    "Sunset Boulevard",
    "Highland Drive",
    "Broadway",
    "Lakeview Drive",
    "River Road",
    "Center Street",
    "Valley View Road",
    "Market Street",
]

REGION_STATE_MAP = {
    "0": ("Springfield", "MA"),
    "1": ("New York", "NY"),
    "2": ("Richmond", "VA"),
    "3": ("Atlanta", "GA"),
    "4": ("Columbus", "OH"),
    "5": ("Minneapolis", "MN"),
    "6": ("Chicago", "IL"),
    "7": ("Dallas", "TX"),
    "8": ("Denver", "CO"),
    "9": ("Los Angeles", "CA"),
}


class AddressGenerator:
    @staticmethod
    def generate_from_input(user_input: str) -> str:
        clean = user_input.strip()
        # Check if input is a 5-digit zip code (or 5+4 format)
        zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", clean)
        if zip_match:
            zip_code = zip_match.group(1)
            street_num = random.randint(100, 9999)
            street_name = random.choice(STREET_NAMES)
            
            if zip_code in ZIP_CITY_STATE_MAP:
                city, state = ZIP_CITY_STATE_MAP[zip_code]
            else:
                region = zip_code[0]
                city, state = REGION_STATE_MAP.get(region, ("Springfield", "US"))

            return f"{street_num} {street_name}, {city}, {state} {zip_code}"

        return clean
