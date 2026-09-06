from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.mark_read_request import MarkReadRequest
from ...models.notifications_mark_read_response_notifications_mark_read import (
    NotificationsMarkReadResponseNotificationsMarkRead,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: MarkReadRequest | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/notifications/read",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead | None:
    if response.status_code == 200:
        response_200 = NotificationsMarkReadResponseNotificationsMarkRead.from_dict(
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
) -> Response[HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MarkReadRequest | Unset = UNSET,
) -> Response[HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead]:
    """Mark Read

     Mark notifications read (specific ids, or all). Admin only.

    Args:
        body (MarkReadRequest | Unset): Mark specific notifications read, or all of them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: MarkReadRequest | Unset = UNSET,
) -> HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead | None:
    """Mark Read

     Mark notifications read (specific ids, or all). Admin only.

    Args:
        body (MarkReadRequest | Unset): Mark specific notifications read, or all of them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MarkReadRequest | Unset = UNSET,
) -> Response[HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead]:
    """Mark Read

     Mark notifications read (specific ids, or all). Admin only.

    Args:
        body (MarkReadRequest | Unset): Mark specific notifications read, or all of them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: MarkReadRequest | Unset = UNSET,
) -> HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead | None:
    """Mark Read

     Mark notifications read (specific ids, or all). Admin only.

    Args:
        body (MarkReadRequest | Unset): Mark specific notifications read, or all of them.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | NotificationsMarkReadResponseNotificationsMarkRead
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
