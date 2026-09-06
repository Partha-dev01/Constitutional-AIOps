from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.traces_response import TracesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 20,
    service: None | str | Unset = UNSET,
    trace_id: None | str | Unset = UNSET,
    min_duration_ms: int | None | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    json_service: None | str | Unset
    if isinstance(service, Unset):
        json_service = UNSET
    else:
        json_service = service
    params["service"] = json_service

    json_trace_id: None | str | Unset
    if isinstance(trace_id, Unset):
        json_trace_id = UNSET
    else:
        json_trace_id = trace_id
    params["trace_id"] = json_trace_id

    json_min_duration_ms: int | None | Unset
    if isinstance(min_duration_ms, Unset):
        json_min_duration_ms = UNSET
    else:
        json_min_duration_ms = min_duration_ms
    params["min_duration_ms"] = json_min_duration_ms

    params["since_minutes"] = since_minutes

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/telemetry/traces",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TracesResponse | None:
    if response.status_code == 200:
        response_200 = TracesResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TracesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    service: None | str | Unset = UNSET,
    trace_id: None | str | Unset = UNSET,
    min_duration_ms: int | None | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> Response[HTTPValidationError | TracesResponse]:
    """Get Traces

     Query traces from Tempo

    Args:
        limit (int | Unset):  Default: 20.
        service (None | str | Unset): Filter by service name
        trace_id (None | str | Unset): Get specific trace
        min_duration_ms (int | None | Unset): Minimum duration filter
        since_minutes (int | Unset): Get traces from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TracesResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        service=service,
        trace_id=trace_id,
        min_duration_ms=min_duration_ms,
        since_minutes=since_minutes,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    service: None | str | Unset = UNSET,
    trace_id: None | str | Unset = UNSET,
    min_duration_ms: int | None | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> HTTPValidationError | TracesResponse | None:
    """Get Traces

     Query traces from Tempo

    Args:
        limit (int | Unset):  Default: 20.
        service (None | str | Unset): Filter by service name
        trace_id (None | str | Unset): Get specific trace
        min_duration_ms (int | None | Unset): Minimum duration filter
        since_minutes (int | Unset): Get traces from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TracesResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        service=service,
        trace_id=trace_id,
        min_duration_ms=min_duration_ms,
        since_minutes=since_minutes,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    service: None | str | Unset = UNSET,
    trace_id: None | str | Unset = UNSET,
    min_duration_ms: int | None | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> Response[HTTPValidationError | TracesResponse]:
    """Get Traces

     Query traces from Tempo

    Args:
        limit (int | Unset):  Default: 20.
        service (None | str | Unset): Filter by service name
        trace_id (None | str | Unset): Get specific trace
        min_duration_ms (int | None | Unset): Minimum duration filter
        since_minutes (int | Unset): Get traces from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TracesResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        service=service,
        trace_id=trace_id,
        min_duration_ms=min_duration_ms,
        since_minutes=since_minutes,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    service: None | str | Unset = UNSET,
    trace_id: None | str | Unset = UNSET,
    min_duration_ms: int | None | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> HTTPValidationError | TracesResponse | None:
    """Get Traces

     Query traces from Tempo

    Args:
        limit (int | Unset):  Default: 20.
        service (None | str | Unset): Filter by service name
        trace_id (None | str | Unset): Get specific trace
        min_duration_ms (int | None | Unset): Minimum duration filter
        since_minutes (int | Unset): Get traces from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TracesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            service=service,
            trace_id=trace_id,
            min_duration_ms=min_duration_ms,
            since_minutes=since_minutes,
        )
    ).parsed
