# belief_evolution_graph_viewer.py
import logging
import json
import os
from typing import Dict, Any, List, Tuple


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BeliefEvolutionGraphViewer:
    """
    Baldur's Belief Evolution Graph Viewer (Conceptual Phase I: Cultivate Belief Dynamics).
    This module provides tools to analyze, summarize, and export the data from
    Baldur's BeliefEvolutionGraph, enabling conceptual visualization and deeper
    understanding of his cognitive evolution.
    """
    def __init__(self, belief_evolution_graph_instance, telemetry_service):
        self.belief_graph = belief_evolution_graph_instance
        self.telemetry = telemetry_service
        logger.info("BeliefEvolutionGraphViewer initialized for cognitive mapping.")


    def summarize_graph(self) -> Dict[str, Any]:
        """
        Provides a high-level textual summary of the current state of the belief graph.
        """
        graph_data = self.belief_graph.get_graph_data()
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])


        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types_count": {},
            "edge_types_count": {},
            "key_nodes_by_connections": [],
            "recent_activity_nodes": []
        }


        # Count node types
        for node in nodes:
            node_type = node.get("type", "unknown")
            summary["node_types_count"][node_type] = summary["node_types_count"].get(node_type, 0) + 1
        
        # Count edge types
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            summary["edge_types_count"][edge_type] = summary["edge_types_count"].get(edge_type, 0) + 1


        # Identify key nodes by connection count (degree centrality - conceptual)
        node_connections: Dict[str, int] = {}
        for edge in edges:
            node_connections[edge["source"]] = node_connections.get(edge["source"], 0) + 1
            node_connections[edge["target"]] = node_connections.get(edge["target"], 0) + 1
        
        sorted_connections = sorted(node_connections.items(), key=lambda item: item[1], reverse=True)
        
        # Get top 5 most connected nodes and their types/content
        for node_id, count in sorted_connections[:5]:
            node_info = next((n for n in nodes if n["id"] == node_id), None)
            if node_info:
                summary["key_nodes_by_connections"].append({
                    "node_id": node_id,
                    "type": node_info.get("type"),
                    "content_preview": node_info.get("content_preview"),
                    "connections": count
                })


        # Identify recent activity (last 10 nodes added/updated)
        recent_nodes = sorted(nodes, key=lambda x: x.get("last_updated", x.get("timestamp", 0)), reverse=True)[:10]
        for node in recent_nodes:
            summary["recent_activity_nodes"].append({
                "node_id": node.get("id"),
                "type": node.get("type"),
                "status": node.get("status"),
                "content_preview": node.get("content_preview"),
                "last_updated": node.get("last_updated")
            })




        self.telemetry.add_diary_entry(
            "BeliefGraph_Summary_Generated",
            f"Generated summary of BeliefEvolutionGraph. Nodes: {summary['total_nodes']}, Edges: {summary['total_edges']}.",
            summary,
            contributor="BeliefEvolutionGraphViewer"
        )
        logger.info("BeliefEvolutionGraphViewer: Graph summary generated.")
        return summary


    def export_graph_data(self, export_dir: str = "graph_exports") -> str:
        """
        Exports the raw graph data (nodes and edges) to a JSON file for external visualization.
        """
        os.makedirs(export_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
        filename = f"belief_evolution_graph_{timestamp}.json"
        filepath = os.path.join(export_dir, filename)


        graph_data = self.belief_graph.get_graph_data()


        try:
            with open(filepath, 'w') as f:
                json.dump(graph_data, f, indent=4)
            
            self.telemetry.add_diary_entry(
                "BeliefGraph_Exported",
                f"BeliefEvolutionGraph data exported to {filepath}.",
                {"filepath": filepath, "nodes": len(graph_data.get('nodes', [])), "edges": len(graph_data.get('edges', []))},
                contributor="BeliefEvolutionGraphViewer"
            )
            logger.info(f"BeliefEvolutionGraphViewer: Graph data exported to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"BeliefEvolutionGraphViewer: Failed to export graph data: {e}")
            self.telemetry.add_diary_entry(
                "BeliefGraph_Export_Failed",
                f"Failed to export BeliefEvolutionGraph data. Error: {str(e)}",
                {"error": str(e)},
                contributor="BeliefEvolutionGraphViewer"
            )
            return f"ERROR: Failed to export graph data: {e}"


    # Future methods could include:
    # - detect_stagnant_beliefs(): Identify nodes with no outgoing edges or updates over time.
    # - identify_mutation_points(): Find nodes with multiple "derived_from" or "conflicts_with" edges leading to new resolutions.
    # - calculate_trait_dominance_over_time(): (Requires integration with AbstractedTraitVectorizer and historical data)