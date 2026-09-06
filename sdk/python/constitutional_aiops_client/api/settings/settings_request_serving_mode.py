from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.serving_mode_request import ServingModeRequest
from ...models.serving_mode_status import ServingModeStatus
from ...types import Response


def _get_kwargs(
    *,
    body: ServingModeRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/settings/serving-mode",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ServingModeStatus | None:
    if response.status_code == 202:
        response_202 = ServingModeStatus.from_dict(response.json())

        return response_202

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | ServingModeStatus]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ServingModeRequest,
) -> Response[HTTPValidationError | ServingModeStatus]:
    """Request Serving Mode Swap

     Write a mode-swap request for the host-side watcher. Admin only. The stack restarts (~3-5 min) while
    the swap runs.

    Args:
        body (ServingModeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ServingModeStatus]
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
    body: ServingModeRequest,
) -> HTTPValidationError | ServingModeStatus | None:
    """Request Serving Mode Swap

     Write a mode-swap request for the host-side watcher. Admin only. The stack restarts (~3-5 min) while
    the swap runs.

    Args:
        body (ServingModeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ServingModeStatus
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ServingModeRequest,
) -> Response[HTTPValidationError | ServingModeStatus]:
    """Request Serving Mode Swap

     Write a mode-swap request for the host-side watcher. Admin only. The stack restarts (~3-5 min) while
    the swap runs.

    Args:
        body (ServingModeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ServingModeStatus]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ServingModeRequest,
) -> HTTPValidationError | ServingModeStatus | None:
    """Request Serving Mode Swap

     Write a mode-swap request for the host-side watcher. Admin only. The stack restarts (~3-5 min) while
    the swap runs.

    Args:
        body (ServingModeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ServingModeStatus
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
