from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.health_serving_health_response_health_serving_health import (
    HealthServingHealthResponseHealthServingHealth,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/health/serving",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HealthServingHealthResponseHealthServingHealth | None:
    if response.status_code == 200:
        response_200 = HealthServingHealthResponseHealthServingHealth.from_dict(
            response.json()
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HealthServingHealthResponseHealthServingHealth]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[HealthServingHealthResponseHealthServingHealth]:
    """Serving Mode Health

     Reports which serving mode is live (Mode 1 = frozen dual-engine artifact, Mode 2 = modernized
    stack), the engine feature flags, and the engine endpoints with best-effort live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthServingHealthResponseHealthServingHealth]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> HealthServingHealthResponseHealthServingHealth | None:
    """Serving Mode Health

     Reports which serving mode is live (Mode 1 = frozen dual-engine artifact, Mode 2 = modernized
    stack), the engine feature flags, and the engine endpoints with best-effort live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthServingHealthResponseHealthServingHealth
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[HealthServingHealthResponseHealthServingHealth]:
    """Serving Mode Health

     Reports which serving mode is live (Mode 1 = frozen dual-engine artifact, Mode 2 = modernized
    stack), the engine feature flags, and the engine endpoints with best-effort live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthServingHealthResponseHealthServingHealth]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> HealthServingHealthResponseHealthServingHealth | None:
    """Serving Mode Health

     Reports which serving mode is live (Mode 1 = frozen dual-engine artifact, Mode 2 = modernized
    stack), the engine feature flags, and the engine endpoints with best-effort live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthServingHealthResponseHealthServingHealth
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
