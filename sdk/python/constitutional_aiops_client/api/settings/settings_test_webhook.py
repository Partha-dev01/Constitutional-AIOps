from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.probe_result import ProbeResult
from ...models.webhook_test_request import WebhookTestRequest
from ...types import Response


def _get_kwargs(
    *,
    body: WebhookTestRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/settings/notifications/test-webhook",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ProbeResult | None:
    if response.status_code == 200:
        response_200 = ProbeResult.from_dict(response.json())

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
) -> Response[HTTPValidationError | ProbeResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookTestRequest,
) -> Response[HTTPValidationError | ProbeResult]:
    """Send Test Webhook

     Send a sample notification payload to the supplied webhook URL and report whether it was accepted.
    Admin only. The server refuses to POST to non-public addresses. Returns reachability + HTTP status
    only.

    Args:
        body (WebhookTestRequest): A webhook URL to send a sample notification to.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProbeResult]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookTestRequest,
) -> HTTPValidationError | ProbeResult | None:
    """Send Test Webhook

     Send a sample notification payload to the supplied webhook URL and report whether it was accepted.
    Admin only. The server refuses to POST to non-public addresses. Returns reachability + HTTP status
    only.

    Args:
        body (WebhookTestRequest): A webhook URL to send a sample notification to.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProbeResult
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookTestRequest,
) -> Response[HTTPValidationError | ProbeResult]:
    """Send Test Webhook

     Send a sample notification payload to the supplied webhook URL and report whether it was accepted.
    Admin only. The server refuses to POST to non-public addresses. Returns reachability + HTTP status
    only.

    Args:
        body (WebhookTestRequest): A webhook URL to send a sample notification to.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ProbeResult]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookTestRequest,
) -> HTTPValidationError | ProbeResult | None:
    """Send Test Webhook

     Send a sample notification payload to the supplied webhook URL and report whether it was accepted.
    Admin only. The server refuses to POST to non-public addresses. Returns reachability + HTTP status
    only.

    Args:
        body (WebhookTestRequest): A webhook URL to send a sample notification to.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ProbeResult
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
