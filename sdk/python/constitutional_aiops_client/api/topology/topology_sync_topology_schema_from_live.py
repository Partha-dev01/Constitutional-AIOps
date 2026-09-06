from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_schema_response import GenerateSchemaResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/topology/schema/sync-live",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GenerateSchemaResponse | None:
    if response.status_code == 200:
        response_200 = GenerateSchemaResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GenerateSchemaResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GenerateSchemaResponse]:
    """Sync Topology Schema from Live Infrastructure

     Build a candidate topology from what is ACTUALLY running on this host right now — the platform
    services with a live Docker container plus any Prometheus-discovered edge hosts, and the
    dependency/telemetry edges between them. Returned as a PREVIEW (NOT persisted): review it, then
    Apply to make it the live topology. On a lite / bring-your-own-endpoint deployment this reflects the
    real small footprint instead of the full reference stack — schema and live view stay in step. Admin
    only.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateSchemaResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> GenerateSchemaResponse | None:
    """Sync Topology Schema from Live Infrastructure

     Build a candidate topology from what is ACTUALLY running on this host right now — the platform
    services with a live Docker container plus any Prometheus-discovered edge hosts, and the
    dependency/telemetry edges between them. Returned as a PREVIEW (NOT persisted): review it, then
    Apply to make it the live topology. On a lite / bring-your-own-endpoint deployment this reflects the
    real small footprint instead of the full reference stack — schema and live view stay in step. Admin
    only.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateSchemaResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GenerateSchemaResponse]:
    """Sync Topology Schema from Live Infrastructure

     Build a candidate topology from what is ACTUALLY running on this host right now — the platform
    services with a live Docker container plus any Prometheus-discovered edge hosts, and the
    dependency/telemetry edges between them. Returned as a PREVIEW (NOT persisted): review it, then
    Apply to make it the live topology. On a lite / bring-your-own-endpoint deployment this reflects the
    real small footprint instead of the full reference stack — schema and live view stay in step. Admin
    only.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateSchemaResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> GenerateSchemaResponse | None:
    """Sync Topology Schema from Live Infrastructure

     Build a candidate topology from what is ACTUALLY running on this host right now — the platform
    services with a live Docker container plus any Prometheus-discovered edge hosts, and the
    dependency/telemetry edges between them. Returned as a PREVIEW (NOT persisted): review it, then
    Apply to make it the live topology. On a lite / bring-your-own-endpoint deployment this reflects the
    real small footprint instead of the full reference stack — schema and live view stay in step. Admin
    only.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateSchemaResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
