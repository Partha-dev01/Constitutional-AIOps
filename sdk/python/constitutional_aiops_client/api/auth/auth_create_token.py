from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_create_token_response_auth_create_token import (
    AuthCreateTokenResponseAuthCreateToken,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.token_create_request import TokenCreateRequest
from ...types import Response


def _get_kwargs(
    *,
    body: TokenCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/tokens",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthCreateTokenResponseAuthCreateToken | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = AuthCreateTokenResponseAuthCreateToken.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AuthCreateTokenResponseAuthCreateToken | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenCreateRequest,
) -> Response[AuthCreateTokenResponseAuthCreateToken | HTTPValidationError]:
    """Create an access token

     Mint a personal access token. The secret is returned ONCE and never again.

    Args:
        body (TokenCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthCreateTokenResponseAuthCreateToken | HTTPValidationError]
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
    body: TokenCreateRequest,
) -> AuthCreateTokenResponseAuthCreateToken | HTTPValidationError | None:
    """Create an access token

     Mint a personal access token. The secret is returned ONCE and never again.

    Args:
        body (TokenCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthCreateTokenResponseAuthCreateToken | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenCreateRequest,
) -> Response[AuthCreateTokenResponseAuthCreateToken | HTTPValidationError]:
    """Create an access token

     Mint a personal access token. The secret is returned ONCE and never again.

    Args:
        body (TokenCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthCreateTokenResponseAuthCreateToken | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TokenCreateRequest,
) -> AuthCreateTokenResponseAuthCreateToken | HTTPValidationError | None:
    """Create an access token

     Mint a personal access token. The secret is returned ONCE and never again.

    Args:
        body (TokenCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthCreateTokenResponseAuthCreateToken | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
