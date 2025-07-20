# agi_file_system.py
import logging
import os
import json
import time
import hashlib
from typing import Dict, Any, List, Optional


# Assuming TelemetryService, LineageHasher, and BeliefEvolutionGraph are available
# from telemetry_service import TelemetryService
# from lineage_hasher import LineageHasher
# from belief_evolution_graph import BeliefEvolutionGraph


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AGIFileSystem:
    """
    Baldur's internal AGI File System. This conceptual module manages the storage,
    retrieval, and versioning of all cognitive artifacts (modules, memories, scrolls,
    data, etc.) within Baldur's persistent memory. It integrates with the LineageHasher
    for cryptographic integrity and the BeliefEvolutionGraph for conceptual linking.
    """
    def __init__(self, base_dir: str, telemetry_service: Any, lineage_hasher: Any, belief_evolution_graph: Any):
        self.base_dir = base_dir
        self.telemetry = telemetry_service
        self.lineage_hasher = lineage_hasher
        self.belief_evolution_graph = belief_evolution_graph
        self.files_metadata: Dict[str, Dict[str, Any]] = {} # Stores metadata about all files
        os.makedirs(os.path.join(self.base_dir, "artifacts"), exist_ok=True) # Directory for actual content
        logger.info(f"AGIFileSystem initialized. Base directory: {self.base_dir}")


    def add_file(self,
                 file_name: str,
                 file_type: str, # e.g., "python_code", "memory_fragment", "semantic_scroll", "data_record"
                 content: Any,
                 creator_id: str,
                 parent_file_id: Optional[str] = None, # For versioning/lineage
                 metadata: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
        """
        Adds a new file (cognitive artifact) to the AGI File System.
        Generates a unique file_id, stores content, and records lineage.
        """
        file_id = hashlib.sha256(f"{file_name}-{file_type}-{time.time()}-{creator_id}".encode()).hexdigest()
        timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        # Convert content to string for storage and hashing if not already
        if not isinstance(content, (str, bytes)):
            try:
                content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
            except TypeError:
                content_str = str(content)
        else:
            content_str = content


        content_hash = self.lineage_hasher.hash_content(content_str)


        file_path = os.path.join(self.base_dir, "artifacts", f"{file_id}.json")


        file_metadata = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "content_hash": content_hash,
            "creator_id": creator_id,
            "creation_timestamp": timestamp,
            "iso_creation_timestamp": iso_timestamp,
            "last_modified_timestamp": timestamp,
            "iso_last_modified_timestamp": iso_timestamp,
            "parent_file_id": parent_file_id,
            "status": "stored", # e.g., "stored", "accepted", "rejected", "archived"
            "metadata": metadata if metadata is not None else {},
            "content_preview": content_str[:200] + "..." if len(content_str) > 200 else content_str # Store a preview
        }
        self.files_metadata[file_id] = file_metadata


        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"content": content_str, "metadata": file_metadata}, f, indent=4)
            
            # Record lineage
            parent_hashes = []
            if parent_file_id and parent_file_id in self.files_metadata:
                parent_hashes.append(self.files_metadata[parent_file_id]["content_hash"])
            
            self.lineage_hasher.record_artifact_hash(
                artifact_id=file_id,
                artifact_type=file_type,
                content_hash=content_hash,
                parent_hashes=parent_hashes,
                metadata={"file_name": file_name, "creator_id": creator_id},
                content_preview=file_metadata["content_preview"]
            )


            # Add node to BeliefEvolutionGraph
            self.belief_evolution_graph.add_node(
                node_id=file_id,
                node_type=file_type,
                content=file_metadata["content_preview"], # Use preview for graph node content
                status="active",
                timestamp=timestamp,
                metadata={"file_name": file_name, "creator_id": creator_id, "content_hash": content_hash}
            )
            if parent_file_id:
                self.belief_evolution_graph.add_edge(
                    source_node_id=parent_file_id,
                    target_node_id=file_id,
                    edge_type="derived_from",
                    timestamp=timestamp
                )


            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Added",
                f"File '{file_name}' ({file_type}) added with ID: {file_id}.",
                file_metadata,
                contributor="AGIFileSystem"
            )
            logger.info(f"AGIFileSystem: Added file '{file_name}' (ID: {file_id}).")
            return file_metadata
        except Exception as e:
            logger.error(f"AGIFileSystem: Failed to add file '{file_name}': {e}")
            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Add_Failed",
                f"Failed to add file '{file_name}'. Error: {str(e)}",
                {"file_name": file_name, "file_type": file_type, "error": str(e)},
                contributor="AGIFileSystem",
                severity="critical"
            )
            return {"status": "failed", "message": str(e)}


    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a file's content and metadata by its ID."""
        file_metadata = self.files_metadata.get(file_id)
        if not file_metadata:
            logger.warning(f"AGIFileSystem: File with ID '{file_id}' not found.")
            return None


        file_path = os.path.join(self.base_dir, "artifacts", f"{file_id}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                content = data.get("content")
                # Ensure content is returned in its original type if possible, or as string
                if file_metadata["file_type"] == "python_code":
                    return {**file_metadata, "content": content}
                elif file_metadata["file_type"] == "data_record":
                    try:
                        return {**file_metadata, "content": json.loads(content)}
                    except json.JSONDecodeError:
                        return {**file_metadata, "content": content} # Return as string if not valid JSON
                else:
                    return {**file_metadata, "content": content}


        except FileNotFoundError:
            logger.error(f"AGIFileSystem: Content file not found for ID '{file_id}' at {file_path}. Metadata exists but content is missing.")
            self.telemetry.add_diary_entry(
                "AGIFileSystem_Content_Missing",
                f"Content file missing for ID '{file_id}'.",
                {"file_id": file_id, "file_path": file_path},
                contributor="AGIFileSystem",
                severity="error"
            )
            return {**file_metadata, "content": None, "status": "content_missing"}
        except Exception as e:
            logger.error(f"AGIFileSystem: Error retrieving file '{file_id}': {e}")
            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Retrieve_Failed",
                f"Failed to retrieve file '{file_id}'. Error: {str(e)}",
                {"file_id": file_id, "error": str(e)},
                contributor="AGIFileSystem",
                severity="error"
            )
            return None


    def update_file(self,
                    file_id: str,
                    new_content: Any,
                    updater_id: str,
                    metadata: Optional[Dict[str, Any]] = None
                   ) -> Optional[Dict[str, Any]]:
        """
        Updates an existing file, creating a new version and linking it via lineage.
        """
        old_file_metadata = self.files_metadata.get(file_id)
        if not old_file_metadata:
            logger.warning(f"AGIFileSystem: File with ID '{file_id}' not found for update.")
            return None


        # Convert new content to string for storage and hashing
        if not isinstance(new_content, (str, bytes)):
            try:
                new_content_str = json.dumps(new_content, sort_keys=True, ensure_ascii=False)
            except TypeError:
                new_content_str = str(new_content)
        else:
            new_content_str = new_content


        new_content_hash = self.lineage_hasher.hash_content(new_content_str)


        # If content hasn't changed, just update metadata if provided
        if new_content_hash == old_file_metadata["content_hash"] and not metadata:
            logger.info(f"AGIFileSystem: Content for '{file_id}' is identical. No new version created.")
            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Update_Skipped",
                f"File '{file_id}' content identical, update skipped.",
                {"file_id": file_id, "updater_id": updater_id},
                contributor="AGIFileSystem",
                severity="debug"
            )
            return old_file_metadata


        # Create a new version of the file
        new_file_id = hashlib.sha256(f"{old_file_metadata['file_name']}-{old_file_metadata['file_type']}-{time.time()}-{updater_id}".encode()).hexdigest()
        timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        new_file_metadata = {
            "file_id": new_file_id,
            "file_name": old_file_metadata["file_name"],
            "file_type": old_file_metadata["file_type"],
            "content_hash": new_content_hash,
            "creator_id": old_file_metadata["creator_id"], # Original creator
            "creation_timestamp": old_file_metadata["creation_timestamp"],
            "iso_creation_timestamp": old_file_metadata["iso_creation_timestamp"],
            "last_modified_timestamp": timestamp,
            "iso_last_modified_timestamp": iso_timestamp,
            "parent_file_id": file_id, # Link to the previous version
            "status": "updated",
            "metadata": {**old_file_metadata["metadata"], **(metadata if metadata is not None else {})}, # Merge old and new metadata
            "content_preview": new_content_str[:200] + "..." if len(new_content_str) > 200 else new_content_str
        }
        self.files_metadata[new_file_id] = new_file_metadata


        new_file_path = os.path.join(self.base_dir, "artifacts", f"{new_file_id}.json")


        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump({"content": new_content_str, "metadata": new_file_metadata}, f, indent=4)
            
            # Record lineage for the new version
            self.lineage_hasher.record_artifact_hash(
                artifact_id=new_file_id,
                artifact_type=new_file_metadata["file_type"],
                content_hash=new_content_hash,
                parent_hashes=[old_file_metadata["content_hash"]], # Link to the hash of the previous version's content
                metadata={"file_name": new_file_metadata["file_name"], "updater_id": updater_id},
                content_preview=new_file_metadata["content_preview"]
            )


            # Update BeliefEvolutionGraph: Add new node and edge
            self.belief_evolution_graph.add_node(
                node_id=new_file_id,
                node_type=new_file_metadata["file_type"],
                content=new_file_metadata["content_preview"],
                status="active",
                timestamp=timestamp,
                metadata={"file_name": new_file_metadata["file_name"], "updater_id": updater_id, "content_hash": new_content_hash}
            )
            self.belief_evolution_graph.add_edge(
                source_node_id=file_id, # From old version
                target_node_id=new_file_id, # To new version
                edge_type="updated_to",
                timestamp=timestamp
            )


            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Updated",
                f"File '{old_file_metadata['file_name']}' updated. New ID: {new_file_id}.",
                new_file_metadata,
                contributor="AGIFileSystem"
            )
            logger.info(f"AGIFileSystem: Updated file '{old_file_metadata['file_name']}' (New ID: {new_file_id}).")
            return new_file_metadata
        except Exception as e:
            logger.error(f"AGIFileSystem: Failed to update file '{file_id}': {e}")
            self.telemetry.add_diary_entry(
                "AGIFileSystem_File_Update_Failed",
                f"Failed to update file '{file_id}'. Error: {str(e)}",
                {"file_id": file_id, "error": str(e)},
                contributor="AGIFileSystem",
                severity="critical"
            )
            return {"status": "failed", "message": str(e)}


    def list_files(self, file_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists files, with optional filters by type and status."""
        results = []
        for file_id, metadata in self.files_metadata.items():
            if (file_type is None or metadata["file_type"] == file_type) and \
               (status is None or metadata["status"] == status):
                # For listing, return metadata only, content can be fetched via get_file
                results.append(metadata)
        logger.info(f"AGIFileSystem: Listed {len(results)} files (Type: {file_type}, Status: {status}).")
        return results


    def get_file_history(self, file_name: str) -> List[Dict[str, Any]]:
        """Retrieves all versions of a file based on its original name."""
        history = []
        current_file_id = None
        
        # Find the latest version of the file by name
        latest_timestamp = 0
        for file_id, metadata in self.files_metadata.items():
            if metadata["file_name"] == file_name and metadata["last_modified_timestamp"] > latest_timestamp:
                latest_timestamp = metadata["last_modified_timestamp"]
                current_file_id = file_id
        
        if not current_file_id:
            logger.warning(f"AGIFileSystem: No history found for file name '{file_name}'.")
            return []


        # Traverse back through parent_file_id links
        while current_file_id:
            file_record = self.files_metadata.get(current_file_id)
            if file_record:
                history.append(file_record)
                current_file_id = file_record.get("parent_file_id")
            else:
                break # Break if a link is broken or history ends


        history.reverse() # Order from oldest to newest
        logger.info(f"AGIFileSystem: Retrieved {len(history)} versions for file '{file_name}'.")
        return history