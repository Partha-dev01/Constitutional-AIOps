from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.dismiss_host_response import DismissHostResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    edge_label: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/v1/infrastructure/remote-hosts/{edge_label}".format(
            edge_label=quote(str(edge_label), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DismissHostResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DismissHostResponse.from_dict(response.json())

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
) -> Response[DismissHostResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    edge_label: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DismissHostResponse | HTTPValidationError]:
    """Dismiss Remote Edge Host

     Hide a remote host from the monitored-hosts list by dismissing its `edge` label. The list is auto-
    derived from live telemetry, so this adds the label to a persisted denylist rather than deleting
    telemetry. If the host keeps shipping it stays hidden until restored. Use to clear stale/one-off
    hosts.

    Args:
        edge_label (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DismissHostResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        edge_label=edge_label,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    edge_label: str,
    *,
    client: AuthenticatedClient | Client,
) -> DismissHostResponse | HTTPValidationError | None:
    """Dismiss Remote Edge Host

     Hide a remote host from the monitored-hosts list by dismissing its `edge` label. The list is auto-
    derived from live telemetry, so this adds the label to a persisted denylist rather than deleting
    telemetry. If the host keeps shipping it stays hidden until restored. Use to clear stale/one-off
    hosts.

    Args:
        edge_label (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DismissHostResponse | HTTPValidationError
    """

    return sync_detailed(
        edge_label=edge_label,
        client=client,
    ).parsed


async def asyncio_detailed(
    edge_label: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DismissHostResponse | HTTPValidationError]:
    """Dismiss Remote Edge Host

     Hide a remote host from the monitored-hosts list by dismissing its `edge` label. The list is auto-
    derived from live telemetry, so this adds the label to a persisted denylist rather than deleting
    telemetry. If the host keeps shipping it stays hidden until restored. Use to clear stale/one-off
    hosts.

    Args:
        edge_label (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DismissHostResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        edge_label=edge_label,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    edge_label: str,
    *,
    client: AuthenticatedClient | Client,
) -> DismissHostResponse | HTTPValidationError | None:
    """Dismiss Remote Edge Host

     Hide a remote host from the monitored-hosts list by dismissing its `edge` label. The list is auto-
    derived from live telemetry, so this adds the label to a persisted denylist rather than deleting
    telemetry. If the host keeps shipping it stays hidden until restored. Use to clear stale/one-off
    hosts.

    Args:
        edge_label (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DismissHostResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            edge_label=edge_label,
            client=client,
        )
    ).parsed
