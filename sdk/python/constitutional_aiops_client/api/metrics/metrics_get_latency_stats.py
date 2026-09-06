from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metrics_get_latency_stats_response_metrics_get_latency_stats import (
    MetricsGetLatencyStatsResponseMetricsGetLatencyStats,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    agent: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_agent: None | str | Unset
    if isinstance(agent, Unset):
        json_agent = UNSET
    else:
        json_agent = agent
    params["agent"] = json_agent

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/metrics/latency",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats | None:
    if response.status_code == 200:
        response_200 = MetricsGetLatencyStatsResponseMetricsGetLatencyStats.from_dict(
            response.json()
        )

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
) -> Response[
    HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats
]:
    """Get Latency Statistics

     Get latency statistics optionally filtered by agent

    Args:
        agent (None | str | Unset): Filter by agent: 'fast' or 'reasoning'

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats]
    """

    kwargs = _get_kwargs(
        agent=agent,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    agent: None | str | Unset = UNSET,
) -> HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats | None:
    """Get Latency Statistics

     Get latency statistics optionally filtered by agent

    Args:
        agent (None | str | Unset): Filter by agent: 'fast' or 'reasoning'

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats
    """

    return sync_detailed(
        client=client,
        agent=agent,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    agent: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats
]:
    """Get Latency Statistics

     Get latency statistics optionally filtered by agent

    Args:
        agent (None | str | Unset): Filter by agent: 'fast' or 'reasoning'

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats]
    """

    kwargs = _get_kwargs(
        agent=agent,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    agent: None | str | Unset = UNSET,
) -> HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats | None:
    """Get Latency Statistics

     Get latency statistics optionally filtered by agent

    Args:
        agent (None | str | Unset): Filter by agent: 'fast' or 'reasoning'

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsGetLatencyStatsResponseMetricsGetLatencyStats
    """

    return (
        await asyncio_detailed(
            client=client,
            agent=agent,
        )
    ).parsed
