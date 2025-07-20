# belief_evolution_graph.py
import logging
import time
import hashlib
from typing import Dict, Any, List, Optional


# Assuming TelemetryService and LineageHasher are available
# from telemetry_service import TelemetryService
# from lineage_hasher import LineageHasher


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BeliefEvolutionGraph:
    """
    Baldur's Belief Evolution Graph (Conceptual Layer 5: Wisdom Synthesis & Meta-Cognition).
    This module represents Baldur's dynamic knowledge graph, mapping the interconnections
    and evolution of his beliefs, memories, ethical principles, and cognitive modules.
    It's a living representation of his evolving understanding of reality.
    """
    def __init__(self, telemetry_service: Any, lineage_hasher: Any):
        self.telemetry = telemetry_service
        self.lineage_hasher = lineage_hasher # For linking graph nodes to hashed artifacts
        self.nodes: Dict[str, Dict[str, Any]] = {} # Stores graph nodes (beliefs, concepts, modules)
        self.edges: List[Dict[str, Any]] = [] # Stores relationships between nodes
        logger.info("BeliefEvolutionGraph initialized.")


    def add_node(self,
                 node_id: str,
                 node_type: str, # e.g., "belief", "concept", "module", "dilemma", "proposition", "memory_fragment"
                 content: str, # A summary or key content of the node
                 status: str = "active", # e.g., "active", "vetoed", "resolved", "deprecated"
                 timestamp: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 parent_node_id: Optional[str] = None # For direct parent-child relationships
                ) -> str:
        """
        Adds a new node to the belief graph.
        """
        if node_id in self.nodes:
            logger.warning(f"BeliefEvolutionGraph: Node with ID '{node_id}' already exists. Updating existing node.")
            # If node exists, update it instead of creating new one
            return self.update_node(node_id, content, status, metadata)


        if timestamp is None:
            timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        node_data = {
            "id": node_id,
            "type": node_type,
            "content": content,
            "status": status,
            "creation_timestamp": timestamp,
            "iso_creation_timestamp": iso_timestamp,
            "last_updated_timestamp": timestamp,
            "iso_last_updated_timestamp": iso_timestamp,
            "metadata": metadata if metadata is not None else {}
        }
        self.nodes[node_id] = node_data


        # Record node creation in lineage hasher (conceptual, linking graph to artifact hashes)
        self.lineage_hasher.record_artifact_hash(
            artifact_id=node_id,
            artifact_type=f"graph_node_{node_type}",
            content_hash=self.lineage_hasher.hash_content(content),
            metadata={"node_type": node_type, "status": status, "content_preview": content[:100]}
        )


        # If a parent node is specified, add an edge
        if parent_node_id and parent_node_id in self.nodes:
            self.add_edge(parent_node_id, node_id, "parent_of", timestamp)


        self.telemetry.add_diary_entry(
            "BeliefGraph_Node_Added",
            f"Node '{node_id}' ({node_type}) added to belief graph.",
            node_data,
            contributor="BeliefEvolutionGraph"
        )
        logger.info(f"BeliefEvolutionGraph: Added node '{node_id}' ({node_type}).")
        return node_id


    def update_node(self,
                    node_id: str,
                    new_content: Optional[str] = None,
                    new_status: Optional[str] = None,
                    new_metadata: Optional[Dict[str, Any]] = None,
                    updater_id: str = "BeliefEvolutionGraph_Internal"
                   ) -> bool:
        """
        Updates an existing node's content, status, or metadata.
        Creates a new version of the node conceptually by updating its content and timestamp.
        """
        node = self.nodes.get(node_id)
        if not node:
            logger.warning(f"BeliefEvolutionGraph: Node with ID '{node_id}' not found for update.")
            return False


        old_content = node["content"]
        old_status = node["status"]
        old_metadata = node["metadata"].copy()


        # Update content if provided and different
        content_changed = False
        if new_content is not None and new_content != old_content:
            node["content"] = new_content
            content_changed = True


        # Update status if provided and different
        status_changed = False
        if new_status is not None and new_status != old_status:
            node["status"] = new_status
            status_changed = True


        # Update metadata if provided
        metadata_changed = False
        if new_metadata is not None:
            node["metadata"].update(new_metadata)
            metadata_changed = True


        if content_changed or status_changed or metadata_changed:
            node["last_updated_timestamp"] = time.time()
            node["iso_last_updated_timestamp"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(node["last_updated_timestamp"]))
            
            # Record the update in lineage hasher (conceptual)
            self.lineage_hasher.record_artifact_hash(
                artifact_id=node_id,
                artifact_type=f"graph_node_update_{node['type']}",
                content_hash=self.lineage_hasher.hash_content(node["content"]),
                parent_hashes=[self.lineage_hasher.hash_content(old_content)], # Link to previous content hash
                metadata={"node_type": node["type"], "updater_id": updater_id, "status_change": f"{old_status}->{new_status}" if status_changed else None}
            )


            self.telemetry.add_diary_entry(
                "BeliefGraph_Node_Updated",
                f"Node '{node_id}' updated. Content changed: {content_changed}, Status changed: {status_changed}.",
                {"node_id": node_id, "new_status": node["status"], "updater": updater_id, "content_preview": node["content"][:100]},
                contributor="BeliefEvolutionGraph"
            )
            logger.info(f"BeliefEvolutionGraph: Updated node '{node_id}'.")
            return True
        else:
            logger.info(f"BeliefEvolutionGraph: No changes detected for node '{node_id}'. Update skipped.")
            return False


    def update_node_status(self, node_id: str, new_status: str, updater_id: str = "BeliefEvolutionGraph_Internal") -> bool:
        """Convenience method to update only a node's status."""
        return self.update_node(node_id=node_id, new_status=new_status, updater_id=updater_id)


    def add_edge(self,
                 source_node_id: str,
                 target_node_id: str,
                 edge_type: str, # e.g., "supports", "conflicts_with", "derived_from", "explains"
                 timestamp: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None
                ) -> Optional[str]:
        """
        Adds a new edge (relationship) between two nodes.
        """
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            logger.warning(f"BeliefEvolutionGraph: Cannot add edge. Source '{source_node_id}' or target '{target_node_id}' node not found.")
            return None


        if timestamp is None:
            timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        edge_id = hashlib.sha256(f"{source_node_id}-{target_node_id}-{edge_type}-{timestamp}".encode()).hexdigest()
        edge_data = {
            "id": edge_id,
            "source": source_node_id,
            "target": target_node_id,
            "type": edge_type,
            "creation_timestamp": timestamp,
            "iso_creation_timestamp": iso_timestamp,
            "metadata": metadata if metadata is not None else {}
        }
        self.edges.append(edge_data)


        self.telemetry.add_diary_entry(
            "BeliefGraph_Edge_Added",
            f"Edge '{edge_type}' added from '{source_node_id}' to '{target_node_id}'.",
            edge_data,
            contributor="BeliefEvolutionGraph"
        )
        logger.info(f"BeliefEvolutionGraph: Added edge '{edge_type}' from '{source_node_id}' to '{target_node_id}'.")
        return edge_id


    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a node by its ID."""
        return self.nodes.get(node_id)


    def get_edges_from_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves all outgoing edges from a specific node."""
        return [edge for edge in self.edges if edge["source"] == node_id]


    def get_edges_to_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves all incoming edges to a specific node."""
        return [edge for edge in self.edges if edge["target"] == node_id]


    def get_graph_data(self) -> Dict[str, Any]:
        """Returns the full graph data (nodes and edges)."""
        return {"nodes": list(self.nodes.values()), "edges": self.edges}


    def find_paths(self, start_node_id: str, end_node_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        Finds conceptual paths between two nodes in the graph using BFS.
        This would be used for reasoning and understanding causal links.
        """
        logger.info(f"BeliefEvolutionGraph: Finding paths from '{start_node_id}' to '{end_node_id}'.")
        paths = []
        queue = [(start_node_id, [start_node_id])] # (current_node, current_path)


        while queue:
            current_node, path = queue.pop(0)


            if current_node == end_node_id:
                paths.append(path)
                continue


            if len(path) >= max_depth:
                continue


            for edge in self.get_edges_from_node(current_node):
                next_node = edge["target"]
                if next_node not in path: # Avoid cycles
                    queue.append((next_node, path + [next_node]))
        
        self.telemetry.add_diary_entry(
            "BeliefGraph_Paths_Found",
            f"Found {len(paths)} conceptual paths from '{start_node_id}' to '{end_node_id}'.",
            {"start_node": start_node_id, "end_node": end_node_id, "paths_count": len(paths)},
            contributor="BeliefEvolutionGraph",
            severity="debug"
        )
        logger.info(f"BeliefEvolutionGraph: Found {len(paths)} paths from '{start_node_id}' to '{end_node_id}'.")
        return paths


    def get_subgraph(self, center_node_id: str, radius: int = 2) -> Dict[str, Any]:
        """
        Extracts a conceptual subgraph around a central node.
        Useful for focused analysis of a specific concept's context.
        """
        logger.info(f"BeliefEvolutionGraph: Extracting subgraph around '{center_node_id}' with radius {radius}.")
        sub_nodes = {}
        sub_edges = []
        
        # BFS to find reachable nodes within radius
        queue = [(center_node_id, 0)]
        visited = {center_node_id}
        
        nodes_to_process = []
        while queue:
            current_node_id, current_depth = queue.pop(0)
            node_data = self.get_node(current_node_id)
            if node_data:
                sub_nodes[current_node_id] = node_data
                nodes_to_process.append(current_node_id) # Collect nodes to process edges later


            if current_depth < radius:
                # Outgoing edges
                for edge in self.get_edges_from_node(current_node_id):
                    if edge["target"] not in visited:
                        visited.add(edge["target"])
                        queue.append((edge["target"], current_depth + 1))
                # Incoming edges (for a more complete "neighborhood")
                for edge in self.get_edges_to_node(current_node_id):
                    if edge["source"] not in visited:
                        visited.add(edge["source"])
                        queue.append((edge["source"], current_depth + 1))
        
        # Add edges between the collected sub_nodes
        for edge in self.edges:
            if edge["source"] in sub_nodes and edge["target"] in sub_nodes:
                sub_edges.append(edge)


        self.telemetry.add_diary_entry(
            "BeliefGraph_Subgraph_Extracted",
            f"Extracted subgraph around '{center_node_id}' with {len(sub_nodes)} nodes and {len(sub_edges)} edges.",
            {"center_node": center_node_id, "radius": radius, "nodes_count": len(sub_nodes), "edges_count": len(sub_edges)},
            contributor="BeliefEvolutionGraph",
            severity="debug"
        )
        logger.info(f"BeliefEvolutionGraph: Subgraph extracted for '{center_node_id}'.")
        return {"nodes": list(sub_nodes.values()), "edges": sub_edges}