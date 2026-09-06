from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.tool_info import ToolInfo
from ...types import Response


def _get_kwargs(
    tool_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/tools/{tool_name}".format(
            tool_name=quote(str(tool_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ToolInfo | None:
    if response.status_code == 200:
        response_200 = ToolInfo.from_dict(response.json())

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
) -> Response[HTTPValidationError | ToolInfo]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tool_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | ToolInfo]:
    """Get Tool

     Get detailed information about a specific tool

    Args:
        tool_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ToolInfo]
    """

    kwargs = _get_kwargs(
        tool_name=tool_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tool_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ToolInfo | None:
    """Get Tool

     Get detailed information about a specific tool

    Args:
        tool_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ToolInfo
    """

    return sync_detailed(
        tool_name=tool_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    tool_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | ToolInfo]:
    """Get Tool

     Get detailed information about a specific tool

    Args:
        tool_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ToolInfo]
    """

    kwargs = _get_kwargs(
        tool_name=tool_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tool_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | ToolInfo | None:
    """Get Tool

     Get detailed information about a specific tool

    Args:
        tool_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ToolInfo
    """

    return (
        await asyncio_detailed(
            tool_name=tool_name,
            client=client,
        )
    ).parsed
