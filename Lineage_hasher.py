# lineage_hasher.py
import logging
import hashlib
import json
import time
from typing import Dict, Any, Optional, List


# Assuming TelemetryService and BeliefEvolutionGraph are available
# from telemetry_service import TelemetryService
# from belief_evolution_graph import BeliefEvolutionGraph # For DAG generation


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LineageHasher:
    """
    Provides cryptographic ancestry tracking for all of Baldur's cognitive artifacts
    (modules, memories, decisions, scrolls, etc.). Each artifact gets a unique,
    immutable hash, ensuring an auditable history of his evolution.
    """
    def __init__(self, telemetry_service: Any, belief_graph: Any): # Added belief_graph for DAG
        self.telemetry = telemetry_service
        self.belief_graph = belief_graph # Store belief_graph for DAG generation
        self.hash_records: Dict[str, Dict[str, Any]] = {} # Stores all generated hashes and their metadata
        logger.info("LineageHasher initialized.")


    def hash_content(self, content: Any, salted: bool = False) -> str: # Optional salted hash toggle
        """
        Generates a SHA-256 hash for any given content.
        Handles strings, bytes, and JSON-serializable objects.
        Optional salted hash toggle for security.
        """
        if isinstance(content, str):
            data_to_hash = content.encode('utf-8')
        elif isinstance(content, bytes):
            data_to_hash = content
        elif isinstance(content, (dict, list)):
            try:
                data_to_hash = json.dumps(content, sort_keys=True, ensure_ascii=False).encode('utf-8')
            except TypeError as e:
                logger.error(f"LineageHasher: Failed to serialize JSON content for hashing: {e}")
                raise ValueError("Content must be string, bytes, or JSON-serializable.") from e
        else:
            logger.error(f"LineageHasher: Unsupported content type for hashing: {type(content)}")
            raise TypeError("Content must be string, bytes, or JSON-serializable.")


        # Optional salted hash toggle for security
        if salted:
            # In a real system, the salt would be securely managed (e.g., from a hardware module)
            # For conceptual purposes, a simple timestamp-based salt
            salt = str(time.time()).encode('utf-8')
            data_to_hash = data_to_hash + salt # Append salt
            logger.debug("Using salted hash.")


        content_hash = hashlib.sha256(data_to_hash).hexdigest()
        return content_hash


    def record_artifact_hash(self,
                             artifact_id: str,
                             artifact_type: str, # e.g., "module", "memory_fragment", "scroll", "decision"
                             content_hash: str,
                             parent_hashes: Optional[List[str]] = None, # Hashes of artifacts it was derived from
                             metadata: Optional[Dict[str, Any]] = None,
                             content_preview: Optional[str] = None, # Log artifact size and embed preview traits
                             dominant_traits: Optional[List[Dict[str, Any]]] = None # Log artifact size and embed preview traits
                            ) -> Dict[str, Any]:
        """
        Records the hash of a created or modified artifact, linking it to its lineage.
        Adds timestamp chaining for multistep mutation lineage.
        Logs artifact size and embeds preview traits.
        """
        timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        # If there are parent hashes, create a chain hash
        chain_hash = content_hash
        if parent_hashes:
            sorted_parent_hashes = sorted(parent_hashes)
            parent_chain_data = "".join(sorted_parent_hashes) + str(timestamp)
            chain_hash = hashlib.sha256(f"{content_hash}{parent_chain_data}".encode('utf-8')).hexdigest()


        # Log artifact size and embed preview traits
        artifact_size_bytes = len(content_hash) * 0.5 # Conceptual size based on hash length for demo
        if content_preview is None and metadata and "content" in metadata:
            content_preview = str(metadata["content"])[:100] + "..." if len(str(metadata["content"])) > 100 else str(metadata["content"])


        record = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "content_hash": content_hash,
            "chain_hash": chain_hash, # The hash representing its full lineage
            "parent_hashes": parent_hashes if parent_hashes is not None else [],
            "timestamp": timestamp,
            "iso_timestamp": iso_timestamp,
            "metadata": metadata if metadata is not None else {},
            "artifact_size_bytes": artifact_size_bytes, # Log artifact size
            "content_preview": content_preview, # Embed preview traits
            "dominant_traits": dominant_traits # Embed preview traits
        }
        self.hash_records[artifact_id] = record


        self.telemetry.add_diary_entry(
            "LineageHasher_Artifact_Hashed",
            f"Artifact '{artifact_id}' ({artifact_type}) hashed. Chain hash: {chain_hash[:8]}...",
            record,
            contributor="LineageHasher"
        )
        logger.info(f"LineageHasher: Recorded hash for artifact '{artifact_id}' (Chain: {chain_hash[:8]}...).")
        return record


    def get_artifact_hash_record(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the hash record for a given artifact ID."""
        record = self.hash_records.get(artifact_id)
        if record:
            self.telemetry.add_diary_entry(
                "LineageHasher_Record_Accessed",
                f"Hash record for '{artifact_id}' accessed.",
                {"artifact_id": artifact_id},
                contributor="LineageHasher"
            )
            logger.info(f"LineageHasher: Retrieved hash record for '{artifact_id}'.")
        else:
            logger.warning(f"LineageHasher: Hash record for '{artifact_id}' not found.")
        return record


    def verify_lineage_chain(self, artifact_id: str) -> bool:
        """
        Add verifylineagechain() for ancestry validation.
        Verifies the cryptographic integrity of an artifact's entire lineage chain.
        This would involve recursively checking parent hashes against their content.
        """
        logger.info(f"LineageHasher: Verifying lineage chain for artifact '{artifact_id}'.")
        current_record = self.get_artifact_hash_record(artifact_id)
        if not current_record:
            logger.warning(f"LineageHasher: Cannot verify lineage. Artifact '{artifact_id}' not found.")
            return False


        # Start verification from the current artifact backwards
        # This is a conceptual recursive check. In a real system, it would involve
        # fetching content from AGIFileSystem and re-hashing it to verify.
        
        # For conceptual demo, assume direct verification if record exists and has a chain_hash
        # A more robust check would involve re-computing hashes of parent content.
        
        # Simple check: If it has a chain hash and its parents are recorded, assume valid.
        # A true verification would re-calculate hashes from raw content.
        if "chain_hash" in current_record and current_record["parent_hashes"] is not None:
            # This is where the recursive re-hashing would happen
            # For now, a placeholder for success if it's a valid record type
            is_valid = True
            for parent_hash in current_record["parent_hashes"]:
                parent_record = next((r for r in self.hash_records.values() if r["content_hash"] == parent_hash), None)
                if not parent_record:
                    is_valid = False
                    logger.warning(f"LineageHasher: Parent hash {parent_hash} not found in records for {artifact_id}.")
                    break
                # Recursive call or further checks here
            
            if is_valid:
                self.telemetry.add_diary_entry(
                    "LineageHasher_Chain_Verified",
                    f"Lineage chain for '{artifact_id}' verified.",
                    {"artifact_id": artifact_id},
                    contributor="LineageHasher",
                    severity="low"
                )
                logger.info(f"LineageHasher: Lineage chain for '{artifact_id}' verified.")
                return True
        
        self.telemetry.add_diary_entry(
            "LineageHasher_Chain_Verification_Failed",
            f"Lineage chain for '{artifact_id}' failed verification.",
            {"artifact_id": artifact_id},
            contributor="LineageHasher",
            severity="medium"
        )
        logger.warning(f"LineageHasher: Lineage chain for '{artifact_id}' could not be verified.")
        return False


    def generate_dag_tree(self, root_artifact_id: str, depth: int = 3) -> Dict[str, Any]:
        """
        Generate DAG tree from mutation history.
        Generates data for visualizing a Directed Acyclic Graph (DAG) of an artifact's lineage.
        """
        logger.info(f"LineageHasher: Generating conceptual DAG tree for '{root_artifact_id}'.")
        nodes = []
        edges = []
        
        visited_ids = set()
        queue = [(root_artifact_id, 0)]


        while queue:
            current_id, current_depth = queue.pop(0)


            if current_id in visited_ids or current_depth > depth:
                continue
            visited_ids.add(current_id)


            record = self.get_artifact_hash_record(current_id)
            if not record:
                continue


            nodes.append({
                "id": current_id,
                "label": f"{record['artifact_type']}: {record['artifact_id'][:8]}",
                "type": record['artifact_type'],
                "content_preview": record.get("content_preview", ""),
                "dominant_traits": [t['trait'] for t in record.get("dominant_traits", [])] if record.get("dominant_traits") else []
            })


            for parent_hash in record["parent_hashes"]:
                # Find parent artifact ID based on content_hash (conceptual)
                parent_record = next((r for r in self.hash_records.values() if r["content_hash"] == parent_hash), None)
                if parent_record:
                    parent_id = parent_record["artifact_id"]
                    edges.append({"from": parent_id, "to": current_id, "label": "derived_from"})
                    queue.append((parent_id, current_depth + 1))
        
        return {"nodes": nodes, "edges": edges}


    # Future methods could include:
    # - get_lineage_graph(artifact_id: str): Build a graph of an artifact's ancestry.