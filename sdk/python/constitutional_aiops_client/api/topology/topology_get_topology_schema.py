from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.topology_schema_response import TopologySchemaResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/topology/schema",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> TopologySchemaResponse | None:
    if response.status_code == 200:
        response_200 = TopologySchemaResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[TopologySchemaResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[TopologySchemaResponse]:
    """Get Editable Topology Schema

     Return the current editable platform-topology schema — the persisted custom schema when mode is
    custom, otherwise the auto-discovered seed topology as an editable starting point — plus the active
    mode.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TopologySchemaResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> TopologySchemaResponse | None:
    """Get Editable Topology Schema

     Return the current editable platform-topology schema — the persisted custom schema when mode is
    custom, otherwise the auto-discovered seed topology as an editable starting point — plus the active
    mode.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TopologySchemaResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[TopologySchemaResponse]:
    """Get Editable Topology Schema

     Return the current editable platform-topology schema — the persisted custom schema when mode is
    custom, otherwise the auto-discovered seed topology as an editable starting point — plus the active
    mode.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TopologySchemaResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> TopologySchemaResponse | None:
    """Get Editable Topology Schema

     Return the current editable platform-topology schema — the persisted custom schema when mode is
    custom, otherwise the auto-discovered seed topology as an editable starting point — plus the active
    mode.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TopologySchemaResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
