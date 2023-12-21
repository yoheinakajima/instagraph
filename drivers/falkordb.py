import logging
import os
from typing import Any

from falkordb import FalkorDB as FalkorDBDriver

from .driver import Driver


class FalkorDB(Driver):
    def __init__(self):
        url = os.environ.get("FALKORDB_URL", "redis://localhost:6379")

        self.driver = FalkorDBDriver.from_url(url).select_graph("falkordb")

        # Check if connection is successful
        try:
            logging.info("FalkorDB database connected successfully!")
        except ValueError as ve:
            logging.error("FalkorDB database: {}".format(ve))
            raise

    def get_graph_data(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        nodes = self.driver.query(
            """
        MATCH (n)
        RETURN {data: {id: n.id, label: n.label, color: n.color}}
        """
        )
        nodes = [el[0] for el in nodes.result_set]

        edges = self.driver.query(
            """
        MATCH (s)-[r]->(t)
        return {data: {source: s.id, target: t.id, label:r.type, color: r.color}}
        """
        )
        edges = [el[0] for el in edges.result_set]

        return (nodes, edges)

    def get_graph_history(self, skip, per_page) -> dict[str, Any]:
        # Getting the total number of graphs
        result = self.driver.query(
            """
        MATCH (n)-[r]->(m)
        RETURN count(n) as total_count
        """
        )

        total_count = result.result_set[0][0]

        # If there is no history, return an empty list
        if total_count == 0:
            return {"graph_history": [], "remaining": 0, "graph": True}

        # Fetching 10 most recent graphs
        result = self.driver.query(
            """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        ORDER BY r.timestamp DESC
        SKIP {skip}
        LIMIT {per_page}
        """.format(
                skip=skip, per_page=per_page
            )
        )

        # Process the 'result' to format it as a list of graphs
        graph_history = [
            FalkorDB._process_graph_data(record) for record in result.result_set
        ]
        remaining = max(0, total_count - skip - per_page)

        return {"graph_history": graph_history, "remaining": remaining, "graph": True}

    def get_response_data(
        self, response_data
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        # Import nodes
        nodes = self.driver.query(
            """
            UNWIND $nodes AS node
            MERGE (n:Node {id: node.id})
            SET n.type = node.type, n.label = node.label, n.color = node.color
            """,
            {"nodes": response_data["nodes"]},
        )
        # Import relationships
        relationships = self.driver.query(
            """
            UNWIND $rels AS rel
            MATCH (s:Node {id: rel.from})
            MATCH (t:Node {id: rel.to})
            MERGE (s)-[r:RELATIONSHIP {type:rel.relationship}]->(t)
            SET r.direction = rel.direction,
                r.color = rel.color,
                r.timestamp = timestamp()
            """,
            {"rels": response_data["edges"]},
        )
        return (nodes.result_set, relationships.result_set)

    @staticmethod
    def _process_graph_data(record) -> dict[str, Any]:
        """
        This function processes a record from the FalkorDB query result
        and formats it as a dictionary with the node details and the relationship.

        :param record: A record from the FalkorDB query result
        :return: A dictionary representing the graph data
        """
        try:
            node_from = record[0].properties
            relationship = record[1].properties
            node_to = record[2].properties

            graph_data = {
                "from_node": node_from,
                "relationship": relationship,
                "to_node": node_to,
            }

            return graph_data
        except Exception as e:
            return {"error": str(e)}
