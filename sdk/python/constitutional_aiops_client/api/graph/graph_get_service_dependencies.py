from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.dependency_graph import DependencyGraph
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    depth: int | Unset = 2,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["depth"] = depth

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/services/{name}/dependencies".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DependencyGraph | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DependencyGraph.from_dict(response.json())

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
) -> Response[DependencyGraph | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 2,
) -> Response[DependencyGraph | HTTPValidationError]:
    """Get Service Dependencies

     Get dependency graph for a specific service

    Args:
        name (str):
        depth (int | Unset): Depth of dependency traversal Default: 2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DependencyGraph | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        name=name,
        depth=depth,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 2,
) -> DependencyGraph | HTTPValidationError | None:
    """Get Service Dependencies

     Get dependency graph for a specific service

    Args:
        name (str):
        depth (int | Unset): Depth of dependency traversal Default: 2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DependencyGraph | HTTPValidationError
    """

    return sync_detailed(
        name=name,
        client=client,
        depth=depth,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 2,
) -> Response[DependencyGraph | HTTPValidationError]:
    """Get Service Dependencies

     Get dependency graph for a specific service

    Args:
        name (str):
        depth (int | Unset): Depth of dependency traversal Default: 2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DependencyGraph | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        name=name,
        depth=depth,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    depth: int | Unset = 2,
) -> DependencyGraph | HTTPValidationError | None:
    """Get Service Dependencies

     Get dependency graph for a specific service

    Args:
        name (str):
        depth (int | Unset): Depth of dependency traversal Default: 2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DependencyGraph | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            depth=depth,
        )
    ).parsed
