import os
import json
import openai
import requests
from bs4 import BeautifulSoup
from graphviz import Digraph
import networkx as nx
from neo4j import GraphDatabase
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
response_data = ""

# If Neo4j credentials are set, then Neo4j is used to store information
neo4j_username = os.environ.get("NEO4J_USERNAME")
neo4j_password = os.environ.get("NEO4J_PASSWORD")
neo4j_url = os.environ.get("NEO4J_URL")
neo4j_driver = None
if neo4j_username and neo4j_password and neo4j_url:
    neo4j_driver = GraphDatabase.driver(
        neo4j_url, auth=(neo4j_username, neo4j_password))

# Function to scrape text from a website
def scrape_text_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Error: Could not retrieve content from URL."
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = " ".join([p.get_text() for p in paragraphs])
    print("web scrape done")
    return text


@app.route("/get_response_data", methods=["POST"])
def get_response_data():
    global response_data
    user_input = request.json.get("user_input", "")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    print("starting openai call")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role": "user",
                "content": f"Help me understand following by describing as a detailed knowledge graph: {user_input}",
            }
        ],
        functions=[
            {
                "name": "knowledge_graph",
                "description": "Generate a knowledge graph with entities and relationships. Use the colors to help differentiate between different node or edge types/categories. Always provide light pastel colors that work well with black font.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "createdDate": {"type": "string"},
                                "lastUpdated": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                        "nodes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"},
                                    "type": {"type": "string"},
                                    "color": {"type": "string"},  # Added color property
                                    "properties": {
                                        "type": "object",
                                        "description": "Additional attributes for the node",
                                    },
                                },
                                "required": [
                                    "id",
                                    "label",
                                    "type",
                                    "color",
                                ],  # Added color to required
                            },
                        },
                        "edges": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "from": {"type": "string"},
                                    "to": {"type": "string"},
                                    "relationship": {"type": "string"},
                                    "direction": {"type": "string"},
                                    "color": {"type": "string"},  # Added color property
                                    "properties": {
                                        "type": "object",
                                        "description": "Additional attributes for the edge",
                                    },
                                },
                                "required": [
                                    "from",
                                    "to",
                                    "relationship",
                                    "color",
                                ],  # Added color to required
                            },
                        },
                    },
                    "required": ["nodes", "edges"],
                },
            }
        ],
        function_call={"name": "knowledge_graph"},
    )

    response_data = completion.choices[0]["message"]["function_call"]["arguments"]
    print(response_data)
    if neo4j_driver:
        # Import nodes
        neo4j_driver.execute_query("""
        UNWIND $nodes AS node
        MERGE (n:Node {id:toLower(node.id)})
        SET n.type = node.type, n.label = node.label, n.color = node.color""",
            {"nodes": json.loads(response_data)['nodes']})
        # Import relationships
        neo4j_driver.execute_query("""
        UNWIND $rels AS rel
        MATCH (s:Node {id: toLower(rel.from)})
        MATCH (t:Node {id: toLower(rel.to)})
        MERGE (s)-[r:RELATIONSHIP {type:rel.relationship}]->(t)
        SET r.direction = rel.direction,
            r.color = rel.color;
        """, {"rels": json.loads(response_data)['edges']})

    return response_data


# Function to visualize the knowledge graph using Graphviz
@app.route("/graphviz", methods=["POST"])
def visualize_knowledge_graph_with_graphviz():
    global response_data
    dot = Digraph(comment="Knowledge Graph")
    response_dict = json.loads(response_data)

    # Add nodes to the graph
    for node in response_dict.get("nodes", []):
        dot.node(node["id"], f"{node['label']} ({node['type']})")

    # Add edges to the graph
    for edge in response_dict.get("edges", []):
        dot.edge(edge["from"], edge["to"], label=edge["relationship"])

    # Render and visualize
    dot.render("knowledge_graph.gv", view=False)
    # Render to PNG format and save it
    dot.format = "png"
    dot.render("static/knowledge_graph", view=False)

    # Construct the URL pointing to the generated PNG
    png_url = f"{request.url_root}static/knowledge_graph.png"

    return jsonify({"png_url": png_url}), 200


@app.route("/get_graph_data", methods=["POST"])
def get_graph_data():
    try:
        if neo4j_driver:
            nodes, _, _ = neo4j_driver.execute_query("""
            MATCH (n)
            WITH collect(
                {data: {id: n.id, label: n.label, color: n.color}}) AS node
            RETURN node
            """)
            nodes = [el['node'] for el in nodes][0]

            edges, _, _ = neo4j_driver.execute_query("""
            MATCH (s)-[r]->(t)
            WITH collect(
                {data: {source: s.id, target: t.id, label:r.type, color: r.color}}
            ) AS rel
            RETURN rel
            """)
            edges = [el['rel'] for el in edges][0]
        else:
            global response_data
            print(response_data)
            response_dict = json.loads(response_data)
            # Assume response_data is global or passed appropriately
            nodes = [
                {
                    "data": {
                        "id": node["id"],
                        "label": node["label"],
                        "color": node.get("color", "defaultColor"),
                    }
                }
                for node in response_dict["nodes"]
            ]
            edges = [
                {
                    "data": {
                        "source": edge["from"],
                        "target": edge["to"],
                        "label": edge["relationship"],
                        "color": edge.get("color", "defaultColor"),
                    }
                }
                for edge in response_dict["edges"]
            ]
        return jsonify({"elements": {"nodes": nodes, "edges": edges}})
    except:
        return jsonify({"elements": {"nodes": [], "edges": []}})


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
