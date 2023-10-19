from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    createdDate: str = Field(
        ..., description="The date the knowledge graph was created"
    )
    lastUpdated: str = Field(
        ..., description="The date the knowledge graph was last updated"
    )
    description: str = Field(..., description="Description of the knowledge graph")


class Node(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Label for the node")
    type: str = Field(..., description="Type of the node")
    color: str = Field(..., description="Color for the node")
    properties: Dict[str, Any] = Field(
        {}, description="Additional attributes for the node"
    )


class Edge(BaseModel):
    # WARING: Notice that this is "from_", not "from"
    from_: str = Field(..., alias="from", description="Origin node ID")
    to: str = Field(..., description="Destination node ID")
    relationship: str = Field(..., description="Type of relationship between the nodes")
    direction: str = Field(..., description="Direction of the relationship")
    color: str = Field(..., description="Color for the edge")
    properties: Dict[str, Any] = Field(
        {}, description="Additional attributes for the edge"
    )


class KnowledgeGraph(BaseModel):
    """Generate a knowledge graph with entities and relationships.
    Use the colors to help differentiate between different node or edge types/categories.
    Always provide light pastel colors that work well with black font.
    """

    metadata: Metadata = Field(..., description="Metadata for the knowledge graph")
    nodes: List[Node] = Field(..., description="List of nodes in the knowledge graph")
    edges: List[Edge] = Field(..., description="List of edges in the knowledge graph")
