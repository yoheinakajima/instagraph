import os

from driver import Driver
from flask import jsonify
from neo4j import GraphDatabase


class Neo4j(Driver):

    def __init__(self):
        # If Neo4j credentials are set, then Neo4j is used to store information
        self.neo4j_username = os.environ.get("NEO4J_USERNAME")
        self.neo4j_password = os.environ.get("NEO4J_PASSWORD")
        self.neo4j_url = os.environ.get("NEO4J_URI")
        if self.neo4j_url is None:
            self.neo4j_url = os.environ.get("NEO4J_URL")
            if self.neo4j_url is not None:
                print("Obsolete: Please define NEO4J_URI instead")

        if self.neo4j_username and self.neo4j_password and self.neo4j_url:
            self.driver = GraphDatabase.driver(self.neo4j_url, 
                                          auth=(self.neo4j_username, 
                                                self.neo4j_password))
            # Check if connection is successful
            with self.driver.session() as session:
                try:
                    session.run("RETURN 1")
                    print("Neo4j database connected successfully!")
                except ValueError as ve:
                    print("Neo4j database: {}".format(ve))
                    raise
        else:
            raise Exception("Configuration for Neo4j is missing")

    def get_graph_data(self):
        nodes, _, _ = self.driver.execute_query(
            """
        MATCH (n)
        WITH collect(
            {data: {id: n.id, label: n.label, color: n.color}}) AS node
        RETURN node
        """
        )
        nodes = [el["node"] for el in nodes][0]

        edges, _, _ = self.driver.execute_query(
            """
        MATCH (s)-[r]->(t)
        WITH collect(
            {data: {source: s.id, target: t.id, label:r.type, color: r.color}}
        ) AS rel
        RETURN rel
        """
        )
        edges = [el["rel"] for el in edges][0]

        return (nodes, edges)


    def get_graph_history(self, skip, per_page):
        # Getting the total number of graphs
        total_graphs, _, _ = self.driver.execute_query(
            """
        MATCH (n)-[r]->(m)
        RETURN count(n) as total_count
        """
        )
        total_count = total_graphs[0]["total_count"]

        # Fetching 10 most recent graphs
        result, _, _ = self.driver.execute_query(
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
        graph_history = [Neo4j._process_graph_data(record) for record in result]
        remaining = max(0, total_count - skip - per_page)

        return jsonify(
            {"graph_history": graph_history, "remaining": remaining, "neo4j": True}
        )
    
    def get_response_data(self, response_data):
        # Import nodes
        results = self.driver.execute_query(
            """
            UNWIND $nodes AS node
            MERGE (n:Node {id: node.id})
            SET n.type = node.type, n.label = node.label, n.color = node.color
            """,
            {"nodes": response_data["nodes"]},
        )
        print("Results from Neo4j:", results)
        # Import relationships
        results = self.driver.execute_query(
            """
            UNWIND $rels AS rel
            MATCH (s:Node {id: rel.from})
            MATCH (t:Node {id: rel.to})
            MERGE (s)-[r:RELATIONSHIP {type:rel.relationship}]->(t)
            SET r.direction = rel.direction,
                r.color = rel.color,
                r.timestamp = timestamp();
            """,
            {"rels": response_data["edges"]},
        )
        # print(f"Created {summary.counters.updates().relationshipsCreated} relationships.")
        print("Results from Neo4j:", results)

    
    def _process_graph_data(record):
        """
        This function processes a record from the Neo4j query result
        and formats it as a dictionary with the node details and the relationship.

        :param record: A record from the Neo4j query result
        :return: A dictionary representing the graph data
        """
        try:
            node_from = record["n"].items()
            node_to = record["m"].items()
            relationship = record["r"].items()

            graph_data = {
                "from_node": {key: value for key, value in node_from},
                "to_node": {key: value for key, value in node_to},
                "relationship": {key: value for key, value in relationship},
            }

            return graph_data
        except Exception as e:
            return {"error": str(e)}