from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.topology_response import TopologyResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    window_hours: int | Unset = 168,
    buckets: int | Unset = 28,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["window_hours"] = window_hours

    params["buckets"] = buckets

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/topology",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TopologyResponse | None:
    if response.status_code == 200:
        response_200 = TopologyResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TopologyResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    window_hours: int | Unset = 168,
    buckets: int | Unset = 28,
) -> Response[HTTPValidationError | TopologyResponse]:
    """Get Platform Topology

     Layered platform architecture with live health and per-node episode evolution buckets. Falls back to
    the static seed topology when Neo4j is empty or unreachable (never 5xx).

    Args:
        window_hours (int | Unset): Episode window in hours Default: 168.
        buckets (int | Unset): Number of evolution buckets Default: 28.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TopologyResponse]
    """

    kwargs = _get_kwargs(
        window_hours=window_hours,
        buckets=buckets,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    window_hours: int | Unset = 168,
    buckets: int | Unset = 28,
) -> HTTPValidationError | TopologyResponse | None:
    """Get Platform Topology

     Layered platform architecture with live health and per-node episode evolution buckets. Falls back to
    the static seed topology when Neo4j is empty or unreachable (never 5xx).

    Args:
        window_hours (int | Unset): Episode window in hours Default: 168.
        buckets (int | Unset): Number of evolution buckets Default: 28.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TopologyResponse
    """

    return sync_detailed(
        client=client,
        window_hours=window_hours,
        buckets=buckets,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    window_hours: int | Unset = 168,
    buckets: int | Unset = 28,
) -> Response[HTTPValidationError | TopologyResponse]:
    """Get Platform Topology

     Layered platform architecture with live health and per-node episode evolution buckets. Falls back to
    the static seed topology when Neo4j is empty or unreachable (never 5xx).

    Args:
        window_hours (int | Unset): Episode window in hours Default: 168.
        buckets (int | Unset): Number of evolution buckets Default: 28.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TopologyResponse]
    """

    kwargs = _get_kwargs(
        window_hours=window_hours,
        buckets=buckets,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    window_hours: int | Unset = 168,
    buckets: int | Unset = 28,
) -> HTTPValidationError | TopologyResponse | None:
    """Get Platform Topology

     Layered platform architecture with live health and per-node episode evolution buckets. Falls back to
    the static seed topology when Neo4j is empty or unreachable (never 5xx).

    Args:
        window_hours (int | Unset): Episode window in hours Default: 168.
        buckets (int | Unset): Number of evolution buckets Default: 28.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TopologyResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            window_hours=window_hours,
            buckets=buckets,
        )
    ).parsed
