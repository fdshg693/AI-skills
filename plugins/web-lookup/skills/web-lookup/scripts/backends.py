"""Minimal calls for the five backends. No MCP passthrough, no Tavily extras.

grep / ms / aws use fastmcp against public MCP servers. tav uses `tavily-python`.
ctx uses Context7 REST with `requests`. 202 polling / 429 backoff / 301 follow
are not implemented — failures surface as-is (aws rate limits are only
relabelled so the message says so).
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

import requests

GREP_ENDPOINT = "https://mcp.grep.app"
# Cold-start grep.app can 504 around 20s and succeed near 40s (same as tools/grepapp).
GREP_TIMEOUT = 45.0
GREP_TOOL = "searchGitHub"

MS_ENDPOINT = "https://learn.microsoft.com/api/mcp"
MS_TIMEOUT = 30.0
MS_SEARCH_TOOL = "microsoft_docs_search"
MS_FETCH_TOOL = "microsoft_docs_fetch"

AWS_ENDPOINT = "https://knowledge-mcp.global.api.aws"
AWS_TIMEOUT = 60.0
AWS_SEARCH_TOOL = "aws___search_documentation"
AWS_READ_TOOL = "aws___read_documentation"
# The server silently ignores unknown topics (falls back to `general`), so the CLI
# validates against this list (same as tools/awsdocs).
AWS_TOPICS = (
    "reference_documentation",
    "current_awareness",
    "troubleshooting",
    "amplify_docs",
    "cdk_docs",
    "cdk_constructs",
    "cloudformation",
    "strands_docs",
    "agent_skills",
    "general",
)
AWS_MAX_TOPICS = 3
AWS_SEARCH_LIMIT = 10
AWS_MAX_READ_ROUNDS = 100
_AWS_RATE_LIMIT_CODE = -32004
_AWS_RATE_LIMIT_MARKER = "too many requests"
_AWS_RATE_LIMIT_MESSAGE = (
    "rate limited by the AWS Knowledge MCP server (HTTP 429 / -32004 / throttled); "
    "wait a while and retry"
)
_AWS_URL_LABELS = (
    ("aws.amazon.com/blogs/", "[Blog] "),
    ("aws.amazon.com/about-aws/whats-new/", "[What's New] "),
    ("repost.aws/", "[re:Post] "),
)

TAV_TIMEOUT = 60.0
CTX_TIMEOUT = 30.0
CTX_BASE_URL = "https://context7.com/api/v2/"
CTX_SEARCH_PATH = "libs/search"
CTX_CONTEXT_PATH = "context"

_REPO_LINE = re.compile(r"^Repository: (.+)$", re.MULTILINE)
_PATH_LINE = re.compile(r"^Path: (.+)$", re.MULTILINE)
_MARKDOWN_TITLE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_URL_LINE = re.compile(r"^URL:\s+\S+", re.MULTILINE)


def _content_text(result: Any) -> str:
    return "\n".join(block.text for block in result.content if hasattr(block, "text"))


def _call_mcp(endpoint: str, timeout: float, tool_name: str, arguments: dict[str, Any]) -> Any:
    from fastmcp import Client

    async def _run() -> Any:
        client = Client(endpoint, timeout=timeout)
        async with client:
            return await client.call_tool(tool_name, arguments, raise_on_error=False)

    return asyncio.run(_run())


def _clean_title(text: str) -> str:
    return " ".join(text.split()) or "(untitled)"


def grep_search(
    query: str,
    *,
    language: list[str] | None = None,
    repo: str | None = None,
    path: str | None = None,
    match_case: bool = False,
    match_whole_words: bool = False,
    use_regexp: bool = False,
) -> list[tuple[str, str]]:
    arguments: dict[str, Any] = {"query": query}
    if language:
        arguments["language"] = language
    if repo:
        arguments["repo"] = repo
    if path:
        arguments["path"] = path
    if match_case:
        arguments["matchCase"] = True
    if match_whole_words:
        arguments["matchWholeWords"] = True
    if use_regexp:
        arguments["useRegexp"] = True

    result = _call_mcp(GREP_ENDPOINT, GREP_TIMEOUT, GREP_TOOL, arguments)
    if result.is_error:
        raise RuntimeError(f"{GREP_TOOL} failed: {_content_text(result)}")

    blocks = [block.text for block in result.content if hasattr(block, "text")]
    if len(blocks) == 1 and not blocks[0].startswith("Repository: "):
        return []

    items: list[tuple[str, str]] = []
    for position, text in enumerate(blocks, start=1):
        repo_match = _REPO_LINE.search(text)
        path_match = _PATH_LINE.search(text)
        if repo_match and path_match:
            title = f"{repo_match.group(1)} — {path_match.group(1)}"
        else:
            title = f"result-{position}"
        items.append((title, f"# {title}\n\n{text}"))
    return items


def ms_search(query: str) -> list[tuple[str, str]]:
    result = _call_mcp(MS_ENDPOINT, MS_TIMEOUT, MS_SEARCH_TOOL, {"query": query})
    if result.is_error:
        raise RuntimeError(f"{MS_SEARCH_TOOL} failed: {_content_text(result)}")

    items: list[tuple[str, str]] = []
    for raw in (result.structured_content or {}).get("results", []):
        title = _clean_title(raw.get("title") or "(untitled)")
        url = raw.get("contentUrl", "")
        content = f"# {title}\n\nURL: {url}\n\n{raw.get('content', '')}"
        items.append((title, content))
    return items


def _with_source_url(markdown: str, url: str) -> str:
    head = "\n".join(markdown.splitlines()[:15])
    if _URL_LINE.search(head):
        return markdown
    url_line = f"URL: {url}"
    heading_match = _MARKDOWN_TITLE.search(markdown)
    if heading_match is None:
        return f"{url_line}\n\n{markdown}"
    before = markdown[: heading_match.end()]
    after = markdown[heading_match.end() :].lstrip("\n")
    return f"{before}\n\n{url_line}\n\n{after}"


def ms_fetch(url: str) -> list[tuple[str, str]]:
    result = _call_mcp(MS_ENDPOINT, MS_TIMEOUT, MS_FETCH_TOOL, {"url": url})
    if result.is_error:
        raise RuntimeError(f"{MS_FETCH_TOOL} failed: {_content_text(result)}")

    markdown = _content_text(result)
    if not markdown.strip():
        return []
    title_match = _MARKDOWN_TITLE.search(markdown)
    raw_title = title_match.group(1) if title_match else url.rstrip("/").rsplit("/", 1)[-1]
    title = _clean_title(raw_title)
    return [(title, _with_source_url(markdown, url))]


class _AwsEmptyResponse(RuntimeError):
    """No content block / blank text (seen on some ranges of long pages)."""


def _aws_unwrap(result: Any) -> Any:
    """Return the `content` object, judging the body (the server's `is_error` is always False)."""
    text = _content_text(result)
    if not text.strip():
        raise _AwsEmptyResponse("the server returned an empty response")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"unexpected non-JSON response: {text[:500]}") from exc
    if isinstance(data, dict):
        if data.get("errorMessage"):
            raise RuntimeError(str(data["errorMessage"]))
        if "content" in data:
            return data["content"]
    return data


def _is_rate_limit_error(exc: BaseException) -> bool:
    """True if `exc` or anything it wraps (ExceptionGroup, cause, context) is a 429 / -32004."""
    seen: set[int] = set()
    stack: list[BaseException | None] = [exc]
    while stack:
        current = stack.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        if getattr(getattr(current, "response", None), "status_code", None) == 429:
            return True
        if getattr(getattr(current, "error", None), "code", None) == _AWS_RATE_LIMIT_CODE:
            return True
        if _AWS_RATE_LIMIT_MARKER in str(current).lower():
            return True
        stack.extend(getattr(current, "exceptions", ()) or ())
        stack.append(current.__cause__)
        stack.append(current.__context__)
    return False


def _aws_session(body: Callable[[Any], Awaitable[Any]]) -> Any:
    """Run `body(client)` on one connection so continuation reads share one handshake."""
    from fastmcp import Client

    async def _run() -> Any:
        client = Client(AWS_ENDPOINT, timeout=AWS_TIMEOUT)
        async with client:
            return await body(client)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        if _is_rate_limit_error(exc):
            raise RuntimeError(_AWS_RATE_LIMIT_MESSAGE) from exc
        raise


def _aws_title_label(url: str) -> str:
    for marker, label in _AWS_URL_LABELS:
        if marker in url:
            return label
    return ""


def aws_search(query: str, *, topics: list[str] | None = None) -> list[tuple[str, str]]:
    arguments: dict[str, Any] = {"search_phrase": query, "limit": AWS_SEARCH_LIMIT}
    if topics:
        arguments["topics"] = topics

    async def _body(client: Any) -> Any:
        return await client.call_tool(AWS_SEARCH_TOOL, arguments, raise_on_error=False)

    content = _aws_unwrap(_aws_session(_body))
    items: list[tuple[str, str]] = []
    for raw in (content or {}).get("result") or []:
        url = raw.get("url") or ""
        if not url and raw.get("skill_name"):
            title = "[Skill] " + _clean_title(raw.get("title") or raw["skill_name"])
            body = f"Skill: {raw['skill_name']}\n\n{raw.get('skill_description', '')}"
        else:
            title = _aws_title_label(url) + _clean_title(raw.get("title") or "(untitled)")
            body = f"URL: {url}\n\n{raw.get('context', '')}"
        items.append((title, f"# {title}\n\n{body}"))
    return items


def _aws_chunk_body(item: dict[str, Any]) -> str:
    """Page text of a continuation chunk without the server-prepended TOC / redirect note.

    The slice is exactly `end_index - start_index` chars, so it is the tail of `content`.
    """
    content = item.get("content") or ""
    start = item.get("start_index") or 0
    end = item.get("end_index")
    if isinstance(end, int) and end > start and len(content) >= end - start:
        return content[len(content) - (end - start) :]
    return content


def _aws_with_header(markdown: str, url: str, header_lines: list[str]) -> str:
    """Put `URL:` (and `> ` notes) right after the page H1, or under a synthesized H1.

    Truncated reads open with a server-added TOC instead of the H1, so the TOC is
    kept verbatim below a synthesized title.
    """
    block = "\n".join([f"URL: {url}", *header_lines])
    stripped = markdown.lstrip("\n")
    first_line = stripped.split("\n", 1)[0]
    if _MARKDOWN_TITLE.fullmatch(first_line):
        after = stripped[len(first_line) :].lstrip("\n")
        return f"{first_line}\n\n{block}\n\n{after}"
    title_match = _MARKDOWN_TITLE.search(markdown)
    title = title_match.group(1) if title_match else url.rstrip("/").rsplit("/", 1)[-1]
    return f"# {_clean_title(title)}\n\n{block}\n\n{markdown}"


def aws_fetch(url: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Read one page, following truncation in the same session; return (items, warnings).

    Warnings (redirect, stopped mid-page) are also written as `> ` lines at the top of
    the file. A failure before the first chunk raises; a later one keeps what was read.
    """
    state: dict[str, Any] = {
        "content": "",
        "chunks": 0,
        "end_index": None,
        "total_length": None,
        "truncated": False,
        "redirected_url": None,
        "failure": None,
    }

    def _fail(message: str) -> None:
        if state["chunks"] == 0:
            raise RuntimeError(message)
        state["failure"] = message

    async def _body(client: Any) -> None:
        next_start = 0
        for _ in range(AWS_MAX_READ_ROUNDS):
            request: dict[str, Any] = {"url": url}
            if next_start:
                request["start_index"] = next_start
            result = await client.call_tool(
                AWS_READ_TOOL, {"requests": [request]}, raise_on_error=False
            )
            try:
                items = (_aws_unwrap(result) or {}).get("result") or []
            except _AwsEmptyResponse:
                items = [{"status": "SUCCESS", "content": ""}]
            except RuntimeError as exc:  # top-level errorMessage (off-allowlist URL etc.)
                return _fail(str(exc))
            item = items[0] if items else {"status": "SUCCESS", "content": ""}

            if item.get("status") != "SUCCESS":
                code = item.get("error_code")
                if code == "throttled":
                    return _fail(_AWS_RATE_LIMIT_MESSAGE)
                message = item.get("content") or ""
                return _fail(": ".join(p for p in (code, message) if p) or "unknown error")
            if not (item.get("content") or "").strip():
                return _fail(
                    "the server returned no content for this range "
                    "(a known server-side quirk on some long pages)"
                )

            state["content"] += item["content"] if state["chunks"] == 0 else _aws_chunk_body(item)
            state["chunks"] += 1
            state["redirected_url"] = state["redirected_url"] or item.get("redirected_url")
            state["total_length"] = item.get("total_length")
            start = item.get("start_index") or 0
            end = item.get("end_index")
            state["end_index"] = end
            state["truncated"] = bool(item.get("truncated"))
            if not (state["truncated"] and isinstance(end, int) and end > start):
                return
            next_start = end

    _aws_session(_body)

    warnings: list[str] = []
    if state["redirected_url"]:
        warnings.append(
            f"Warning: redirected to {state['redirected_url']} -- the requested page may not exist."
        )
    if state["failure"]:
        warnings.append(
            f"Incomplete: reading stopped at char {state['end_index']} ({state['failure']})."
        )
    elif state["truncated"]:
        warnings.append(
            f"Stopped after {AWS_MAX_READ_ROUNDS} reads at char {state['end_index']} "
            f"of {state['total_length']}."
        )

    markdown = state["content"]
    title_match = _MARKDOWN_TITLE.search(markdown)
    raw_title = title_match.group(1) if title_match else url.rstrip("/").rsplit("/", 1)[-1]
    content = _aws_with_header(markdown, url, [f"> {w}" for w in warnings])
    return [(_clean_title(raw_title), content)], warnings


def _tavily_client(api_key: str) -> Any:
    from tavily import TavilyClient

    return TavilyClient(api_key=api_key)


def tav_search(
    query: str,
    *,
    api_key: str,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> list[tuple[str, str]]:
    response = _tavily_client(api_key).search(
        query=query,
        search_depth="advanced",
        topic="general",
        max_results=5,
        chunks_per_source=3,
        include_answer=False,
        include_raw_content=False,
        include_images=False,
        include_favicon=False,
        include_usage=False,
        timeout=TAV_TIMEOUT,
        include_domains=include_domains or None,
        exclude_domains=exclude_domains or None,
    )
    items: list[tuple[str, str]] = []
    for position, raw in enumerate(response.get("results") or [], start=1):
        title = _clean_title(raw.get("title") or raw.get("url") or f"result-{position}")
        url = raw.get("url", "")
        score = raw.get("score", "")
        body = raw.get("content") or ""
        content = f"# {title}\n\nURL: {url}\nScore: {score}\n\n{body}"
        items.append((title, content))
    return items


def tav_extract(
    urls: list[str], *, api_key: str, query: str | None = None
) -> list[tuple[str, str]]:
    options: dict[str, Any] = {
        "extract_depth": "advanced",
        "format": "markdown",
        "timeout": TAV_TIMEOUT,
        "include_images": False,
        "include_favicon": False,
        "include_usage": False,
    }
    if query:
        options["chunks_per_source"] = 3
    response = _tavily_client(api_key).extract(urls=urls, query=query, **options)
    items: list[tuple[str, str]] = []
    for position, raw in enumerate(response.get("results") or [], start=1):
        url = raw.get("url", "")
        title = _clean_title(raw.get("title") or url or f"result-{position}")
        body = raw.get("raw_content") or ""
        items.append((title, f"# {title}\n\nURL: {url}\n\n{body}"))
    return items


def _ctx_headers(api_key: str) -> dict[str, str]:
    return {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}


def ctx_library(name: str, query: str, *, api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        CTX_BASE_URL + CTX_SEARCH_PATH,
        params={"libraryName": name, "query": query, "fast": "false"},
        headers=_ctx_headers(api_key),
        timeout=CTX_TIMEOUT,
    )
    response.raise_for_status()
    return (response.json() or {}).get("results") or []


def ctx_docs(library_id: str, query: str, *, api_key: str) -> str:
    response = requests.get(
        CTX_BASE_URL + CTX_CONTEXT_PATH,
        params={"libraryId": library_id, "query": query, "type": "txt", "fast": "false"},
        headers=_ctx_headers(api_key),
        timeout=CTX_TIMEOUT,
    )
    response.raise_for_status()
    return response.text
