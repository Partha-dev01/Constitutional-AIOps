from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.demo_get_demo_status_response_demo_get_demo_status import (
    DemoGetDemoStatusResponseDemoGetDemoStatus,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/demo/status",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DemoGetDemoStatusResponseDemoGetDemoStatus | None:
    if response.status_code == 200:
        response_200 = DemoGetDemoStatusResponseDemoGetDemoStatus.from_dict(
            response.json()
        )

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DemoGetDemoStatusResponseDemoGetDemoStatus]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[DemoGetDemoStatusResponseDemoGetDemoStatus]:
    """Get Demo Status

     Proxy the t3 agent's live scenario + container status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DemoGetDemoStatusResponseDemoGetDemoStatus]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> DemoGetDemoStatusResponseDemoGetDemoStatus | None:
    """Get Demo Status

     Proxy the t3 agent's live scenario + container status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DemoGetDemoStatusResponseDemoGetDemoStatus
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[DemoGetDemoStatusResponseDemoGetDemoStatus]:
    """Get Demo Status

     Proxy the t3 agent's live scenario + container status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DemoGetDemoStatusResponseDemoGetDemoStatus]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> DemoGetDemoStatusResponseDemoGetDemoStatus | None:
    """Get Demo Status

     Proxy the t3 agent's live scenario + container status.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DemoGetDemoStatusResponseDemoGetDemoStatus
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
