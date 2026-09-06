from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.service_node import ServiceNode
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status_filter: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_status_filter: None | str | Unset
    if isinstance(status_filter, Unset):
        json_status_filter = UNSET
    else:
        json_status_filter = status_filter
    params["status_filter"] = json_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/services",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[ServiceNode] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ServiceNode.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[ServiceNode]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status_filter: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[ServiceNode]]:
    """List Services

     Get all services from the graph database

    Args:
        status_filter (None | str | Unset): Filter by status

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ServiceNode]]
    """

    kwargs = _get_kwargs(
        status_filter=status_filter,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    status_filter: None | str | Unset = UNSET,
) -> HTTPValidationError | list[ServiceNode] | None:
    """List Services

     Get all services from the graph database

    Args:
        status_filter (None | str | Unset): Filter by status

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ServiceNode]
    """

    return sync_detailed(
        client=client,
        status_filter=status_filter,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status_filter: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[ServiceNode]]:
    """List Services

     Get all services from the graph database

    Args:
        status_filter (None | str | Unset): Filter by status

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ServiceNode]]
    """

    kwargs = _get_kwargs(
        status_filter=status_filter,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status_filter: None | str | Unset = UNSET,
) -> HTTPValidationError | list[ServiceNode] | None:
    """List Services

     Get all services from the graph database

    Args:
        status_filter (None | str | Unset): Filter by status

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ServiceNode]
    """

    return (
        await asyncio_detailed(
            client=client,
            status_filter=status_filter,
        )
    ).parsed
