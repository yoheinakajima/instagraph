import argparse
import json
import logging
import os
import re

import instructor
import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from graphviz import Digraph

from drivers.neo4j import Neo4j
from models import KnowledgeGraph

instructor.patch()

load_dotenv()

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
response_data = ""

# If a Graph database set, then driver is used to store information
driver = None


# Function to scrape text from a website


def scrape_text_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Error: Could not retrieve content from URL."
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = " ".join([p.get_text() for p in paragraphs])
    logging.info("web scrape done")
    return text


# Function to check user plan


def check_if_free_plan():
    """
    receive USER_PLAN from .env.
    Added default None, as this project won't be in free plan in production mode.

    Returns:
        bool: _description_
    """
    return os.environ.get("USER_PLAN", None) == "free"


# Rate limiting


@app.after_request
def add_header(response):
    """
    add response header if free plan.

    Args:
        response (_type_): _description_

    Returns:
        _type_: _description_
    """
    if check_if_free_plan():
        response.headers["Retry-After"] = 20
    return response


def correct_json(json_str):
    """
    Corrects the JSON response from OpenAI to be valid JSON by removing trailing commas
    """
    while ",\s*}" in json_str or ",\s*]" in json_str:  # noqa: W605
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(
            "SanitizationError: %s for JSON: %s", str(e), json_str, exc_info=True
        )
        return None


@app.route("/get_response_data", methods=["POST"])
def get_response_data():
    global response_data
    user_input = request.json.get("user_input", "")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    if user_input.startswith("http"):
        user_input = scrape_text_from_url(user_input)

    if user_input.startswith("+"):
        prompt = "\n".join(
            [
                "Please update the knowledge graph based on the instruction.",
                json.dumps(
                    dict(instruction=user_input[1:], knowledge_graph=response_data)
                ),
            ]
        )
    else:
        prompt = f"Help me understand following by describing as a detailed knowledge graph: {user_input}"

    logging.info("starting openai call: %s", prompt)
    try:
        completion: KnowledgeGraph = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=KnowledgeGraph,
        )

        # Its now a dict, no need to worry about json loading so many times
        response_data = completion.model_dump()

        # copy "from_" prop to "from" prop on all edges
        edges = response_data["edges"]

        def _restore(e):
            e["from"] = e["from_"]
            return e

        response_data["edges"] = [_restore(e) for e in edges]

    except openai.error.RateLimitError as e:
        # request limit exceeded or something.
        logging.warning("%s", e)
        return jsonify({"error": "rate limitation"}), 429
    except Exception as e:
        # general exception handling
        logging.error("%s", e)
        return jsonify({"error": "unknown error"}), 400

    try:
        if driver:
            results = driver.get_response_data(response_data)
            logging.info("Results from Graph:", results)

    except Exception as e:
        logging.error("An error occurred during the Graph operation: %s", e)
        return (
            jsonify(
                {"error": "An error occurred during the Graph operation: {}".format(e)}
            ),
            500,
        )

    return response_data, 200


# Function to visualize the knowledge graph using Graphviz
@app.route("/graphviz", methods=["POST"])
def visualize_knowledge_graph_with_graphviz():
    global response_data
    dot = Digraph(comment="Knowledge Graph")
    response_dict = response_data
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
        if driver:
            (nodes, edges) = driver.get_graph_data()
        else:
            global response_data
            # print(response_data)
            response_dict = response_data
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
    except Exception:
        return jsonify({"elements": {"nodes": [], "edges": []}})


@app.route("/get_graph_history", methods=["GET"])
def get_graph_history():
    try:
        page = request.args.get("page", default=1, type=int)
        per_page = 10
        skip = (page - 1) * per_page

        result = (
            driver.get_graph_history(skip, per_page)
            if driver
            else {
                "graph_history": [],
                "error": "Graph driver not initialized",
                "graph": False,
            }
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "graph": driver is not None}), 500


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InstaGraph")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--port", type=int, dest="port_num", default=8080)
    parser.add_argument("--graph", type=str, dest="graph_db", default="neo4j")

    args = parser.parse_args()
    port = args.port_num
    graph = args.graph_db

    match graph.lower():
        case "neo4j":
            driver = Neo4j()
        case _:
            # Default try to connect to Neo4j for backward compatibility
            try:
                driver = Neo4j()
            except Exception:
                driver = None

    if args.debug:
        app.run(debug=True, host="0.0.0.0", port=port)
    else:
        app.run(host="0.0.0.0", port=port)
