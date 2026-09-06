from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.infrastructure_remove_monitored_container_response_infrastructure_remove_monitored_container import (
    InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer,
)
from ...types import Response


def _get_kwargs(
    container_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/v1/infrastructure/containers/{container_name}/monitor".format(
            container_name=quote(str(container_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
    | None
):
    if response.status_code == 200:
        response_200 = InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer.from_dict(
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
) -> Response[
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    container_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
]:
    """Remove Container from Monitoring

     Remove a container from the monitored list

    Args:
        container_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer]
    """

    kwargs = _get_kwargs(
        container_name=container_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    container_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
    | None
):
    """Remove Container from Monitoring

     Remove a container from the monitored list

    Args:
        container_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
    """

    return sync_detailed(
        container_name=container_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    container_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
]:
    """Remove Container from Monitoring

     Remove a container from the monitored list

    Args:
        container_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer]
    """

    kwargs = _get_kwargs(
        container_name=container_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    container_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
    | None
):
    """Remove Container from Monitoring

     Remove a container from the monitored list

    Args:
        container_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InfrastructureRemoveMonitoredContainerResponseInfrastructureRemoveMonitoredContainer
    """

    return (
        await asyncio_detailed(
            container_name=container_name,
            client=client,
        )
    ).parsed
