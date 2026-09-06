from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_change_own_password_response_auth_change_own_password import (
    AuthChangeOwnPasswordResponseAuthChangeOwnPassword,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.self_password_change_request import SelfPasswordChangeRequest
from ...types import Response


def _get_kwargs(
    *,
    body: SelfPasswordChangeRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/password",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthChangeOwnPasswordResponseAuthChangeOwnPassword.from_dict(
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
) -> Response[AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SelfPasswordChangeRequest,
) -> Response[AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError]:
    """Change your own password

     Self-service password change for the signed-in user: verifies the current password, then applies the
    store's password policy to the new one.

    Args:
        body (SelfPasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError]
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
    body: SelfPasswordChangeRequest,
) -> AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError | None:
    """Change your own password

     Self-service password change for the signed-in user: verifies the current password, then applies the
    store's password policy to the new one.

    Args:
        body (SelfPasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SelfPasswordChangeRequest,
) -> Response[AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError]:
    """Change your own password

     Self-service password change for the signed-in user: verifies the current password, then applies the
    store's password policy to the new one.

    Args:
        body (SelfPasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SelfPasswordChangeRequest,
) -> AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError | None:
    """Change your own password

     Self-service password change for the signed-in user: verifies the current password, then applies the
    store's password policy to the new one.

    Args:
        body (SelfPasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthChangeOwnPasswordResponseAuthChangeOwnPassword | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
