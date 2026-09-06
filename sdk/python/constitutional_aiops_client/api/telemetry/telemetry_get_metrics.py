from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metrics_response import MetricsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    range_: str | Unset = "1h",
    step: str | Unset = "1m",
    query: None | str | Unset = UNSET,
    metric: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["range"] = range_

    params["step"] = step

    json_query: None | str | Unset
    if isinstance(query, Unset):
        json_query = UNSET
    else:
        json_query = query
    params["query"] = json_query

    json_metric: None | str | Unset
    if isinstance(metric, Unset):
        json_metric = UNSET
    else:
        json_metric = metric
    params["metric"] = json_metric

    json_service: None | str | Unset
    if isinstance(service, Unset):
        json_service = UNSET
    else:
        json_service = service
    params["service"] = json_service

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/telemetry/metrics",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MetricsResponse | None:
    if response.status_code == 200:
        response_200 = MetricsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MetricsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    range_: str | Unset = "1h",
    step: str | Unset = "1m",
    query: None | str | Unset = UNSET,
    metric: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | MetricsResponse]:
    """Get Metrics

     Query metrics from Prometheus

    Args:
        range_ (str | Unset): Time range (e.g., 1h, 6h, 24h) Default: '1h'.
        step (str | Unset): Step interval (e.g., 1m, 5m) Default: '1m'.
        query (None | str | Unset): PromQL query
        metric (None | str | Unset): Specific metric name
        service (None | str | Unset): Filter by service/container

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsResponse]
    """

    kwargs = _get_kwargs(
        range_=range_,
        step=step,
        query=query,
        metric=metric,
        service=service,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    range_: str | Unset = "1h",
    step: str | Unset = "1m",
    query: None | str | Unset = UNSET,
    metric: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
) -> HTTPValidationError | MetricsResponse | None:
    """Get Metrics

     Query metrics from Prometheus

    Args:
        range_ (str | Unset): Time range (e.g., 1h, 6h, 24h) Default: '1h'.
        step (str | Unset): Step interval (e.g., 1m, 5m) Default: '1m'.
        query (None | str | Unset): PromQL query
        metric (None | str | Unset): Specific metric name
        service (None | str | Unset): Filter by service/container

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsResponse
    """

    return sync_detailed(
        client=client,
        range_=range_,
        step=step,
        query=query,
        metric=metric,
        service=service,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    range_: str | Unset = "1h",
    step: str | Unset = "1m",
    query: None | str | Unset = UNSET,
    metric: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | MetricsResponse]:
    """Get Metrics

     Query metrics from Prometheus

    Args:
        range_ (str | Unset): Time range (e.g., 1h, 6h, 24h) Default: '1h'.
        step (str | Unset): Step interval (e.g., 1m, 5m) Default: '1m'.
        query (None | str | Unset): PromQL query
        metric (None | str | Unset): Specific metric name
        service (None | str | Unset): Filter by service/container

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsResponse]
    """

    kwargs = _get_kwargs(
        range_=range_,
        step=step,
        query=query,
        metric=metric,
        service=service,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    range_: str | Unset = "1h",
    step: str | Unset = "1m",
    query: None | str | Unset = UNSET,
    metric: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
) -> HTTPValidationError | MetricsResponse | None:
    """Get Metrics

     Query metrics from Prometheus

    Args:
        range_ (str | Unset): Time range (e.g., 1h, 6h, 24h) Default: '1h'.
        step (str | Unset): Step interval (e.g., 1m, 5m) Default: '1m'.
        query (None | str | Unset): PromQL query
        metric (None | str | Unset): Specific metric name
        service (None | str | Unset): Filter by service/container

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            range_=range_,
            step=step,
            query=query,
            metric=metric,
            service=service,
        )
    ).parsed
