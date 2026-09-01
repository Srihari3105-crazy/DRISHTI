"""
Doctor Verification Service — matches registration number against local CSV.
"""
import csv
import os
from typing import Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# In-memory cache of valid doctor registrations
_doctor_registry: dict[str, dict] = {}


def load_doctor_csv():
    """Load doctor registry from CSV file into memory."""
    global _doctor_registry
    csv_path = settings.DOCTOR_CSV_PATH

    if not os.path.exists(csv_path):
        logger.warning(f"Doctor CSV not found at {csv_path}. Using empty registry.")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reg_no = row.get("reg_no", "").strip().upper()
            if reg_no:
                _doctor_registry[reg_no] = {
                    "name": row.get("name", ""),
                    "reg_no": reg_no,
                    "specialization": row.get("specialization", "Ophthalmology"),
                    "hospital_id": row.get("hospital_id", ""),
                    "phone": row.get("phone", ""),
                    "council": row.get("council", "State Medical Council"),
                }

    logger.info(f"Loaded {len(_doctor_registry)} doctor registrations from CSV")


def verify_registration(reg_no: str) -> Optional[dict]:
    """
    Check if a registration number exists in the CSV.
    Returns the matched record or None.
    """
    normalized = reg_no.strip().upper()
    match = _doctor_registry.get(normalized)

    if match:
        logger.info(f"Doctor registration verified: {normalized}")
    else:
        logger.warning(f"Doctor registration NOT found: {normalized}")

    return match


def get_all_registered_doctors() -> list[dict]:
    """Return all registered doctors from CSV."""
    return list(_doctor_registry.values())
