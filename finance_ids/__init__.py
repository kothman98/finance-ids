import hashlib
import re
from datetime import date

# Known bank description aliases — all map to their canonical name so that
# re-labelled transactions produce the same deterministic ID.
_DESCRIPTION_ALIASES: dict[str, str] = {
    "SUNDRY CREDIT": "STAFF - PAYROLL",
}

# RBC CSV exports append a city/location after the store number, e.g.
# "DAIRY QUEEN #11980 TORONTO", while RBC email alerts omit the city:
# "DAIRY QUEEN #11980".  Strip the trailing location so both sources
# produce the same canonical description.
_LOCATION_SUFFIX_RE = re.compile(r'(#\d+)\s+[A-Z][A-Z ]*$')


def _normalize_description(desc: str) -> str:
    """Remove trailing city/location suffix that RBC appends in CSV exports."""
    return _LOCATION_SUFFIX_RE.sub(r'\1', desc)


def generate_transaction_id(
    account_number: str,
    transaction_date: date,
    amount_cad: float,
    description_1: str,
) -> str:
    """
    Generate a deterministic 16-character transaction ID.

    Uses the last 4 digits of the account number so that the same transaction
    produces the same ID regardless of which pipeline (email or CSV) calls this.

    Normalization applied:
    - account_number:  last 4 characters only
    - description_1:   stripped, uppercased, trailing location suffix removed
    - amount_cad:      absolute value formatted to 2 decimal places
                       (CSV exports use negative for debits; email alerts use
                        positive — both represent the same transaction)
    - transaction_date: ISO format (YYYY-MM-DD)
    """
    account_last4 = account_number.strip()[-4:]
    date_str = transaction_date.isoformat()
    amount_str = f"{abs(float(amount_cad)):.2f}"
    desc = description_1.strip().upper()
    desc = _normalize_description(desc)
    desc = _DESCRIPTION_ALIASES.get(desc, desc)

    raw = f"{account_last4}|{date_str}|{amount_str}|{desc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
