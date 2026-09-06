from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_admin_set_password_response_auth_admin_set_password import (
    AuthAdminSetPasswordResponseAuthAdminSetPassword,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.password_change_request import PasswordChangeRequest
from ...types import Response


def _get_kwargs(
    username: str,
    *,
    body: PasswordChangeRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/users/{username}/password".format(
            username=quote(str(username), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthAdminSetPasswordResponseAuthAdminSetPassword.from_dict(
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
) -> Response[AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    username: str,
    *,
    client: AuthenticatedClient | Client,
    body: PasswordChangeRequest,
) -> Response[AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError]:
    """Set a user's password (admin)

    Args:
        username (str):
        body (PasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        username=username,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    username: str,
    *,
    client: AuthenticatedClient | Client,
    body: PasswordChangeRequest,
) -> AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError | None:
    """Set a user's password (admin)

    Args:
        username (str):
        body (PasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError
    """

    return sync_detailed(
        username=username,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    username: str,
    *,
    client: AuthenticatedClient | Client,
    body: PasswordChangeRequest,
) -> Response[AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError]:
    """Set a user's password (admin)

    Args:
        username (str):
        body (PasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        username=username,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    *,
    client: AuthenticatedClient | Client,
    body: PasswordChangeRequest,
) -> AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError | None:
    """Set a user's password (admin)

    Args:
        username (str):
        body (PasswordChangeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthAdminSetPasswordResponseAuthAdminSetPassword | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            username=username,
            client=client,
            body=body,
        )
    ).parsed
