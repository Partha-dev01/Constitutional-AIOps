from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.infrastructure_get_monitored_containers_response_infrastructure_get_monitored_containers import (
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/infrastructure/containers/monitored",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
    | None
):
    if response.status_code == 200:
        response_200 = InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers.from_dict(
            response.json()
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
]:
    """Get Monitored Container List

     Get the list of containers being monitored

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> (
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
    | None
):
    """Get Monitored Container List

     Get the list of containers being monitored

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
]:
    """Get Monitored Container List

     Get the list of containers being monitored

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
    | None
):
    """Get Monitored Container List

     Get the list of containers being monitored

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        InfrastructureGetMonitoredContainersResponseInfrastructureGetMonitoredContainers
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
