from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool

search = DuckDuckGoSearchRun()

@tool
def search_the_web(query: str) -> str:
    """
    Search the web for current and up-to-date information based on a query.
    """
    results = search(query, max_results=3)

    summaries = []
    for r in results:
        summaries.append(
            f"{r['title']}: {r['body'][:250]}"
        )

    return "\n".join(summaries)
