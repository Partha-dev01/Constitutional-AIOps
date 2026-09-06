from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.seed_topology_response import SeedTopologyResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/graph/seed-topology",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> SeedTopologyResponse | None:
    if response.status_code == 200:
        response_200 = SeedTopologyResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[SeedTopologyResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[SeedTopologyResponse]:
    """Seed Service Topology

     Idempotently MERGE the real platform services and DEPENDS_ON edges into Neo4j (never deletes
    anything). Also runs automatically at startup.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SeedTopologyResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> SeedTopologyResponse | None:
    """Seed Service Topology

     Idempotently MERGE the real platform services and DEPENDS_ON edges into Neo4j (never deletes
    anything). Also runs automatically at startup.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SeedTopologyResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[SeedTopologyResponse]:
    """Seed Service Topology

     Idempotently MERGE the real platform services and DEPENDS_ON edges into Neo4j (never deletes
    anything). Also runs automatically at startup.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SeedTopologyResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> SeedTopologyResponse | None:
    """Seed Service Topology

     Idempotently MERGE the real platform services and DEPENDS_ON edges into Neo4j (never deletes
    anything). Also runs automatically at startup.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SeedTopologyResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
