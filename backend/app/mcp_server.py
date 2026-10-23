"""Local read-only MCP server: python -m app.mcp_server (stdio only)."""
from mcp.server.fastmcp import FastMCP
from app.schemas.toolkit import ResearchQuery, ResearchResult
from app.services.research import execute_query

server = FastMCP("Civil Atlas")


@server.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
def historical_research(query: ResearchQuery) -> ResearchResult:
    """Query public, dated Civil Atlas records. Area, event, boundary and source operations return citations and coverage limits. No editorial or browser-control actions."""
    return execute_query(query)


@server.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
def discover_episodes() -> ResearchResult:
    """Find reviewed, published historical episodes with valid dependencies."""
    return execute_query(ResearchQuery(operation="episodes"))


@server.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
def build_atlas_link(year: int = 117, feature_id: str | None = None) -> ResearchResult:
    """Build a relative atlas link for an explicit year and optional feature."""
    return execute_query(ResearchQuery(operation="atlas_link", year=year, feature_id=feature_id))


if __name__ == "__main__":
    server.run(transport="stdio")
