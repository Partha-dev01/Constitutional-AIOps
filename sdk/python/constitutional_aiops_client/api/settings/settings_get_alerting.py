from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alerting_config_public import AlertingConfigPublic
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/settings/notifications/alerting",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AlertingConfigPublic | None:
    if response.status_code == 200:
        response_200 = AlertingConfigPublic.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AlertingConfigPublic]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[AlertingConfigPublic]:
    """Get Remote Alerting Settings

     Return the Telegram / Matrix remote-alerting config. Admin only. Secrets are never returned; each is
    reduced to a boolean 'set' flag.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertingConfigPublic]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> AlertingConfigPublic | None:
    """Get Remote Alerting Settings

     Return the Telegram / Matrix remote-alerting config. Admin only. Secrets are never returned; each is
    reduced to a boolean 'set' flag.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlertingConfigPublic
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[AlertingConfigPublic]:
    """Get Remote Alerting Settings

     Return the Telegram / Matrix remote-alerting config. Admin only. Secrets are never returned; each is
    reduced to a boolean 'set' flag.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertingConfigPublic]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> AlertingConfigPublic | None:
    """Get Remote Alerting Settings

     Return the Telegram / Matrix remote-alerting config. Admin only. Secrets are never returned; each is
    reduced to a boolean 'set' flag.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlertingConfigPublic
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
