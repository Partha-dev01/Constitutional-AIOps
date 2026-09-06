from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.incident import Incident
from ...models.incident_create import IncidentCreate
from ...types import Response


def _get_kwargs(
    *,
    body: IncidentCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/incidents/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | Incident | None:
    if response.status_code == 201:
        response_201 = Incident.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | Incident]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IncidentCreate,
) -> Response[HTTPValidationError | Incident]:
    """Create Incident

     Create a new incident and optionally trigger auto-analysis

    Args:
        body (IncidentCreate): Request to create a new incident. Example: {'affected_services':
            [{'name': 'payment-service', 'namespace': 'production'}], 'auto_analyze': True,
            'category': 'performance', 'description': 'Users reporting slow checkout times',
            'severity': 'high', 'source': 'alert', 'tags': ['checkout', 'latency'], 'title': 'High
            latency on payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Incident]
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
    body: IncidentCreate,
) -> HTTPValidationError | Incident | None:
    """Create Incident

     Create a new incident and optionally trigger auto-analysis

    Args:
        body (IncidentCreate): Request to create a new incident. Example: {'affected_services':
            [{'name': 'payment-service', 'namespace': 'production'}], 'auto_analyze': True,
            'category': 'performance', 'description': 'Users reporting slow checkout times',
            'severity': 'high', 'source': 'alert', 'tags': ['checkout', 'latency'], 'title': 'High
            latency on payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Incident
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IncidentCreate,
) -> Response[HTTPValidationError | Incident]:
    """Create Incident

     Create a new incident and optionally trigger auto-analysis

    Args:
        body (IncidentCreate): Request to create a new incident. Example: {'affected_services':
            [{'name': 'payment-service', 'namespace': 'production'}], 'auto_analyze': True,
            'category': 'performance', 'description': 'Users reporting slow checkout times',
            'severity': 'high', 'source': 'alert', 'tags': ['checkout', 'latency'], 'title': 'High
            latency on payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Incident]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: IncidentCreate,
) -> HTTPValidationError | Incident | None:
    """Create Incident

     Create a new incident and optionally trigger auto-analysis

    Args:
        body (IncidentCreate): Request to create a new incident. Example: {'affected_services':
            [{'name': 'payment-service', 'namespace': 'production'}], 'auto_analyze': True,
            'category': 'performance', 'description': 'Users reporting slow checkout times',
            'severity': 'high', 'source': 'alert', 'tags': ['checkout', 'latency'], 'title': 'High
            latency on payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Incident
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
