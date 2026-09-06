from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.episodic_graph_data import EpisodicGraphData
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 50,
    since_hours: int | Unset = 168,
    min_similarity: float | Unset = 0.75,
    min_confidence: float | Unset = 0.7,
    include_similar_to: bool | Unset = True,
    include_entities: bool | Unset = True,
    max_edges_per_node: int | Unset = 5,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["since_hours"] = since_hours

    params["min_similarity"] = min_similarity

    params["min_confidence"] = min_confidence

    params["include_similar_to"] = include_similar_to

    params["include_entities"] = include_entities

    params["max_edges_per_node"] = max_edges_per_node

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/episodes",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EpisodicGraphData | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = EpisodicGraphData.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EpisodicGraphData | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    since_hours: int | Unset = 168,
    min_similarity: float | Unset = 0.75,
    min_confidence: float | Unset = 0.7,
    include_similar_to: bool | Unset = True,
    include_entities: bool | Unset = True,
    max_edges_per_node: int | Unset = 5,
) -> Response[EpisodicGraphData | HTTPValidationError]:
    """Get Episodic Memory Graph

     Get complete episodic memory graph with episodes, root causes, actions, and relationships

    Args:
        limit (int | Unset):  Default: 50.
        since_hours (int | Unset): Get episodes from last N hours (default 7 days) Default: 168.
        min_similarity (float | Unset): Minimum similarity threshold for SIMILAR_TO edges (default
            0.75) Default: 0.75.
        min_confidence (float | Unset): Minimum confidence for entity edges (default 0.70)
            Default: 0.7.
        include_similar_to (bool | Unset): Include SIMILAR_TO edges between episodes Default:
            True.
        include_entities (bool | Unset): Include LLM-extracted entity nodes and edges Default:
            True.
        max_edges_per_node (int | Unset): Maximum edges per node to prevent hairball (default 5)
            Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EpisodicGraphData | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        limit=limit,
        since_hours=since_hours,
        min_similarity=min_similarity,
        min_confidence=min_confidence,
        include_similar_to=include_similar_to,
        include_entities=include_entities,
        max_edges_per_node=max_edges_per_node,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    since_hours: int | Unset = 168,
    min_similarity: float | Unset = 0.75,
    min_confidence: float | Unset = 0.7,
    include_similar_to: bool | Unset = True,
    include_entities: bool | Unset = True,
    max_edges_per_node: int | Unset = 5,
) -> EpisodicGraphData | HTTPValidationError | None:
    """Get Episodic Memory Graph

     Get complete episodic memory graph with episodes, root causes, actions, and relationships

    Args:
        limit (int | Unset):  Default: 50.
        since_hours (int | Unset): Get episodes from last N hours (default 7 days) Default: 168.
        min_similarity (float | Unset): Minimum similarity threshold for SIMILAR_TO edges (default
            0.75) Default: 0.75.
        min_confidence (float | Unset): Minimum confidence for entity edges (default 0.70)
            Default: 0.7.
        include_similar_to (bool | Unset): Include SIMILAR_TO edges between episodes Default:
            True.
        include_entities (bool | Unset): Include LLM-extracted entity nodes and edges Default:
            True.
        max_edges_per_node (int | Unset): Maximum edges per node to prevent hairball (default 5)
            Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EpisodicGraphData | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        limit=limit,
        since_hours=since_hours,
        min_similarity=min_similarity,
        min_confidence=min_confidence,
        include_similar_to=include_similar_to,
        include_entities=include_entities,
        max_edges_per_node=max_edges_per_node,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    since_hours: int | Unset = 168,
    min_similarity: float | Unset = 0.75,
    min_confidence: float | Unset = 0.7,
    include_similar_to: bool | Unset = True,
    include_entities: bool | Unset = True,
    max_edges_per_node: int | Unset = 5,
) -> Response[EpisodicGraphData | HTTPValidationError]:
    """Get Episodic Memory Graph

     Get complete episodic memory graph with episodes, root causes, actions, and relationships

    Args:
        limit (int | Unset):  Default: 50.
        since_hours (int | Unset): Get episodes from last N hours (default 7 days) Default: 168.
        min_similarity (float | Unset): Minimum similarity threshold for SIMILAR_TO edges (default
            0.75) Default: 0.75.
        min_confidence (float | Unset): Minimum confidence for entity edges (default 0.70)
            Default: 0.7.
        include_similar_to (bool | Unset): Include SIMILAR_TO edges between episodes Default:
            True.
        include_entities (bool | Unset): Include LLM-extracted entity nodes and edges Default:
            True.
        max_edges_per_node (int | Unset): Maximum edges per node to prevent hairball (default 5)
            Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EpisodicGraphData | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        limit=limit,
        since_hours=since_hours,
        min_similarity=min_similarity,
        min_confidence=min_confidence,
        include_similar_to=include_similar_to,
        include_entities=include_entities,
        max_edges_per_node=max_edges_per_node,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    since_hours: int | Unset = 168,
    min_similarity: float | Unset = 0.75,
    min_confidence: float | Unset = 0.7,
    include_similar_to: bool | Unset = True,
    include_entities: bool | Unset = True,
    max_edges_per_node: int | Unset = 5,
) -> EpisodicGraphData | HTTPValidationError | None:
    """Get Episodic Memory Graph

     Get complete episodic memory graph with episodes, root causes, actions, and relationships

    Args:
        limit (int | Unset):  Default: 50.
        since_hours (int | Unset): Get episodes from last N hours (default 7 days) Default: 168.
        min_similarity (float | Unset): Minimum similarity threshold for SIMILAR_TO edges (default
            0.75) Default: 0.75.
        min_confidence (float | Unset): Minimum confidence for entity edges (default 0.70)
            Default: 0.7.
        include_similar_to (bool | Unset): Include SIMILAR_TO edges between episodes Default:
            True.
        include_entities (bool | Unset): Include LLM-extracted entity nodes and edges Default:
            True.
        max_edges_per_node (int | Unset): Maximum edges per node to prevent hairball (default 5)
            Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EpisodicGraphData | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            since_hours=since_hours,
            min_similarity=min_similarity,
            min_confidence=min_confidence,
            include_similar_to=include_similar_to,
            include_entities=include_entities,
            max_edges_per_node=max_edges_per_node,
        )
    ).parsed
