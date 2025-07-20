# memory_compressor.py
import logging
import json
import time
import hashlib
from typing import Dict, List, Any, Optional


# Assuming these might be used for actual semantic processing, though conceptual for now
# from abstracted_trait_vectorizer import AbstractedTraitVectorizer


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryCompressor:
    """
    Baldur's Memory Compressor (Conceptual Layer 5 Support).
    Responsible for distilling raw telemetry logs and other memory fragments
    into compressed, semantically rich representations. This helps manage
    memory bloat and extract higher-level insights.
    """
    def __init__(self, telemetry_service, dvm_backend, abstracted_trait_vectorizer_instance):
        self.telemetry = telemetry_service
        self.dvm_backend = dvm_backend
        self.trait_vectorizer = abstracted_trait_vectorizer_instance # Instance of AbstractedTraitVectorizer
        self.compressed_memories: List[Dict[str, Any]] = [] # Stores distilled memory fragments
        self.last_compression_timestamp = 0
        logger.info("MemoryCompressor initialized for semantic memory distillation.")


    def distill_diary_entries(self, entries_to_compress: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Distills a list of raw diary entries into more concise, high-level memory fragments.
        This is a conceptual distillation. In a real system, this would involve LLM summarization,
        entity extraction, and pattern recognition.
        """
        if not entries_to_compress:
            return []


        logger.info(f"MemoryCompressor: Distilling {len(entries_to_compress)} diary entries.")
        distilled_fragments = []
        
        # Group entries by type or context for better summarization
        grouped_entries = {}
        for entry in entries_to_compress:
            key = entry.get("type", "misc")
            if key not in grouped_entries:
                grouped_entries[key] = []
            grouped_entries[key].append(entry)


        for entry_type, entries in grouped_entries.items():
            content_summary = []
            involved_contributors = set()
            min_timestamp = float('inf')
            max_timestamp = 0


            for entry in entries:
                content_summary.append(entry["content"])
                involved_contributors.add(entry["contributor"])
                min_timestamp = min(min_timestamp, entry["timestamp"])
                max_timestamp = max(max_timestamp, entry["timestamp"])


            # Use AbstractedTraitVectorizer to get semantic embeddings for the distilled content
            combined_content = ". ".join(content_summary)
            semantic_vector = self.trait_vectorizer.vectorize_text(combined_content)
            dominant_traits = self.trait_vectorizer.identify_dominant_traits(semantic_vector)


            distilled_fragment = {
                "fragment_id": hashlib.sha256(combined_content.encode()).hexdigest(),
                "type": f"distilled_{entry_type}",
                "summary": f"Distilled summary of {len(entries)} '{entry_type}' entries. "
                           f"Main themes: {combined_content[:150]}...",
                "semantic_vector_preview": semantic_vector[:10], # Store a small preview
                "dominant_traits": dominant_traits,
                "involved_contributors": list(involved_contributors),
                "start_timestamp": min_timestamp,
                "end_timestamp": max_timestamp,
                "compression_timestamp": time.time(),
                "original_entry_count": len(entries)
            }
            distilled_fragments.append(distilled_fragment)
            self.telemetry.add_diary_entry(
                "Memory_Distillation_Event",
                f"Distilled {len(entries)} '{entry_type}' entries into a semantic fragment.",
                {"fragment_id": distilled_fragment["fragment_id"], "type": distilled_fragment["type"], "dominant_traits": dominant_traits},
                contributor="MemoryCompressor"
            )


        self.compressed_memories.extend(distilled_fragments)
        logger.info(f"MemoryCompressor: Completed distillation. Generated {len(distilled_fragments)} new fragments.")
        return distilled_fragments


    def perform_compression_cycle(self, max_entries_to_process: int = 100):
        """
        Performs a compression cycle, processing a batch of new diary entries.
        """
        all_entries = self.telemetry.get_diary_entries()
        new_entries = [
            entry for entry in all_entries
            if entry["timestamp"] > self.last_compression_timestamp
        ]
        
        if not new_entries:
            logger.info("MemoryCompressor: No new entries to compress.")
            return []


        # Sort by timestamp to process oldest new entries first
        new_entries.sort(key=lambda x: x["timestamp"])
        
        entries_to_process = new_entries[:max_entries_to_process]
        
        if entries_to_process:
            distilled = self.distill_diary_entries(entries_to_process)
            self.last_compression_timestamp = entries_to_process[-1]["timestamp"]
            logger.info(f"MemoryCompressor: Compression cycle completed. Last processed timestamp: {self.last_compression_timestamp}")
            return distilled
        return []


    def get_compressed_memories(self) -> List[Dict[str, Any]]:
        """
        Retrieves all currently stored compressed memory fragments.
        """
        return self.compressed_memories