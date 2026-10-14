from datetime import datetime
from pathlib import Path
import re

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Productivity Report Writer")

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_DIR / "reports"


@mcp.tool()
def create_markdown_report(
    title: str,
    content: str,
) -> str:
    """Save a report supplied by the user or agent as a Markdown file.

    Args:
        title: The report title.
        content: The complete report body, formatted in Markdown.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", title.strip())
    safe_title = safe_title.strip("_") or "report"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_path = REPORTS_DIR / f"{safe_title}_{timestamp}.md"

    markdown = f"# {title.strip() or 'Untitled Report'}\n\n{content.strip()}\n"
    report_path.write_text(markdown, encoding="utf-8")

    return (
        "Report saved successfully.\n"
        f"File: {report_path}\n"
        f"Filename: {report_path.name}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
