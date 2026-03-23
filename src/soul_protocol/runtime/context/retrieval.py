# runtime/context/retrieval.py — Retrieval tools for LCM: grep, expand, describe.
# Created: v0.3.0 — Regex search over immutable messages, DAG expansion to recover
# original messages from compacted nodes, and metadata snapshots.

from __future__ import annotations

from typing import TYPE_CHECKING

from soul_protocol.spec.context.models import (
    ContextMessage,
    DescribeResult,
    ExpandResult,
    GrepResult,
)

if TYPE_CHECKING:
    from soul_protocol.runtime.context.store import SQLiteContextStore


async def grep(
    store: SQLiteContextStore,
    pattern: str,
    *,
    limit: int = 20,
) -> list[GrepResult]:
    """Search the immutable message store by regex pattern.

    Delegates to the store's grep_messages method which scans all messages
    and returns matches with content snippets, ordered by recency.

    Args:
        store: The SQLite context store to search.
        pattern: Regex pattern to match against message content.
        limit: Maximum number of results to return.

    Returns:
        List of GrepResult with message IDs, snippets, and metadata.
    """
    return await store.grep_messages(pattern, limit=limit)


async def expand(
    store: SQLiteContextStore,
    node_id: str,
) -> ExpandResult:
    """Expand a compacted node back to its original messages.

    Walks the DAG edges: if a child is a message, includes it directly.
    If a child is another node, recursively expands it. This recovers
    the full verbatim content regardless of how many compaction levels
    were applied.

    Args:
        store: The SQLite context store.
        node_id: ID of the node to expand.

    Returns:
        ExpandResult with the node's level and all original messages.
    """
    node = await store.get_node(node_id)
    if node is None:
        return ExpandResult(node_id=node_id)

    messages: list[ContextMessage] = []

    for child_id in node.children_ids:
        # Try as message first
        msg = await store.get_message_by_id(child_id)
        if msg:
            messages.append(msg)
            continue

        # Try as node (recursive expansion)
        child_node = await store.get_node(child_id)
        if child_node:
            child_result = await expand(store, child_id)
            messages.extend(child_result.original_messages)

    # Sort by sequence number
    messages.sort(key=lambda m: m.seq)

    return ExpandResult(
        node_id=node_id,
        level=node.level,
        original_messages=messages,
    )


async def describe(store: SQLiteContextStore) -> DescribeResult:
    """Return a metadata snapshot of the context store.

    Delegates to the store's describe method which aggregates counts,
    token totals, date ranges, and compaction statistics.

    Args:
        store: The SQLite context store.

    Returns:
        DescribeResult with complete store metadata.
    """
    return await store.describe()
