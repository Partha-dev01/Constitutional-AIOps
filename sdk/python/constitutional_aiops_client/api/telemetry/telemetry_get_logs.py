from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.logs_response import LogsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 50,
    level: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    json_level: None | str | Unset
    if isinstance(level, Unset):
        json_level = UNSET
    else:
        json_level = level
    params["level"] = json_level

    json_service: None | str | Unset
    if isinstance(service, Unset):
        json_service = UNSET
    else:
        json_service = service
    params["service"] = json_service

    json_query: None | str | Unset
    if isinstance(query, Unset):
        json_query = UNSET
    else:
        json_query = query
    params["query"] = json_query

    params["since_minutes"] = since_minutes

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/telemetry/logs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | LogsResponse | None:
    if response.status_code == 200:
        response_200 = LogsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | LogsResponse]:
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
    level: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> Response[HTTPValidationError | LogsResponse]:
    """Get Logs

     Query logs from Loki

    Args:
        limit (int | Unset):  Default: 50.
        level (None | str | Unset): Filter by log level
        service (None | str | Unset): Filter by service name
        query (None | str | Unset): LogQL query
        since_minutes (int | Unset): Get logs from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LogsResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        level=level,
        service=service,
        query=query,
        since_minutes=since_minutes,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    level: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> HTTPValidationError | LogsResponse | None:
    """Get Logs

     Query logs from Loki

    Args:
        limit (int | Unset):  Default: 50.
        level (None | str | Unset): Filter by log level
        service (None | str | Unset): Filter by service name
        query (None | str | Unset): LogQL query
        since_minutes (int | Unset): Get logs from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LogsResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        level=level,
        service=service,
        query=query,
        since_minutes=since_minutes,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    level: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> Response[HTTPValidationError | LogsResponse]:
    """Get Logs

     Query logs from Loki

    Args:
        limit (int | Unset):  Default: 50.
        level (None | str | Unset): Filter by log level
        service (None | str | Unset): Filter by service name
        query (None | str | Unset): LogQL query
        since_minutes (int | Unset): Get logs from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | LogsResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        level=level,
        service=service,
        query=query,
        since_minutes=since_minutes,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    level: None | str | Unset = UNSET,
    service: None | str | Unset = UNSET,
    query: None | str | Unset = UNSET,
    since_minutes: int | Unset = 60,
) -> HTTPValidationError | LogsResponse | None:
    """Get Logs

     Query logs from Loki

    Args:
        limit (int | Unset):  Default: 50.
        level (None | str | Unset): Filter by log level
        service (None | str | Unset): Filter by service name
        query (None | str | Unset): LogQL query
        since_minutes (int | Unset): Get logs from last N minutes Default: 60.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | LogsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            level=level,
            service=service,
            query=query,
            since_minutes=since_minutes,
        )
    ).parsed
