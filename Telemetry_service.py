# telemetry_service.py
import time
import json
import logging


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Baldur's Telemetry Service (L3.0.x), responsible for logging internal events,
    decisions, and observations into a chronological "diary."
    This serves as an immutable audit log for Baldur's self-awareness and human oversight.
    """
    def __init__(self):
        self.diary_entries = []
        logger.info("TelemetryService (Diary) initialized.")


    def add_diary_entry(self, entry_type: str, content: str, metadata: dict = None, contributor: str = "Baldur"):
        """
        Adds a new entry to Baldur's diary.


        Args:
            entry_type (str): Categorization of the entry (e.g., "Decision", "Observation", "Error").
            content (str): The main textual content of the diary entry.
            metadata (dict, optional): Additional structured data related to the entry. Defaults to None.
            contributor (str, optional): The entity contributing the entry (e.g., "Baldur", "Gemini", "Master Architect"). Defaults to "Baldur".
        """
        entry = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "type": entry_type,
            "content": content,
            "metadata": metadata if metadata is not None else {},
            "contributor": contributor
        }
        self.diary_entries.append(entry)
        logger.info(f"Diary Entry [{entry_type}] by {contributor}: {content[:100]}...")


        # In a real system, this would be written to an immutable, cryptographically signed log file
        # or a WORM device, potentially with a separate process for integrity checks.
        # For now, it's in-memory for demonstration.


    def get_diary_entries(self) -> list:
        """
        Retrieves all recorded diary entries.


        Returns:
            list: A list of dictionary representing diary entries.
        """
        return self.diary_entries


    def get_last_n_entries(self, n: int) -> list:
        """
        Retrieves the last N diary entries.


        Args:
            n (int): The number of last entries to retrieve.


        Returns:
            list: A list of the last N diary entries.
        """
        return self.diary_entries[-n:]