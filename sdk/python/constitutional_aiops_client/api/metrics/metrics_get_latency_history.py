from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metrics_get_latency_history_response_metrics_get_latency_history import (
    MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 100,
    agent: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    json_agent: None | str | Unset
    if isinstance(agent, Unset):
        json_agent = UNSET
    else:
        json_agent = agent
    params["agent"] = json_agent

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/metrics/history",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
    | None
):
    if response.status_code == 200:
        response_200 = (
            MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory.from_dict(
                response.json()
            )
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
    HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
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
    limit: int | Unset = 100,
    agent: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
]:
    """Get Latency History

     Get recent latency records for detailed analysis

    Args:
        limit (int | Unset): Number of records Default: 100.
        agent (None | str | Unset): Filter by agent

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory]
    """

    kwargs = _get_kwargs(
        limit=limit,
        agent=agent,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    agent: None | str | Unset = UNSET,
) -> (
    HTTPValidationError
    | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
    | None
):
    """Get Latency History

     Get recent latency records for detailed analysis

    Args:
        limit (int | Unset): Number of records Default: 100.
        agent (None | str | Unset): Filter by agent

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
    """

    return sync_detailed(
        client=client,
        limit=limit,
        agent=agent,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    agent: None | str | Unset = UNSET,
) -> Response[
    HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
]:
    """Get Latency History

     Get recent latency records for detailed analysis

    Args:
        limit (int | Unset): Number of records Default: 100.
        agent (None | str | Unset): Filter by agent

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory]
    """

    kwargs = _get_kwargs(
        limit=limit,
        agent=agent,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    agent: None | str | Unset = UNSET,
) -> (
    HTTPValidationError
    | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
    | None
):
    """Get Latency History

     Get recent latency records for detailed analysis

    Args:
        limit (int | Unset): Number of records Default: 100.
        agent (None | str | Unset): Filter by agent

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsGetLatencyHistoryResponseMetricsGetLatencyHistory
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            agent=agent,
        )
    ).parsed
