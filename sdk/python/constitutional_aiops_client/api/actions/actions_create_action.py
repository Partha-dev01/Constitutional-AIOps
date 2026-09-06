from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.action import Action
from ...models.action_create import ActionCreate
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: ActionCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/actions/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Action | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = Action.from_dict(response.json())

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
) -> Response[Action | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ActionCreate,
) -> Response[Action | HTTPValidationError]:
    """Create Action

     Create and validate a new action through Constitutional AI

    Args:
        body (ActionCreate): Request to create/propose a new action. Example: {'action_type':
            'restart_service', 'confidence': 0.88, 'description': 'Restart payment-service to clear
            memory leak', 'evidence': {'memory_usage': 0.95, 'restart_history': 'No restarts in 24h'},
            'incident_id': 'INC-2024-042', 'parameters': {'graceful': True, 'timeout': 30},
            'target_instance': 'payment-service-abc123', 'target_service': 'payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Action | HTTPValidationError]
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
    body: ActionCreate,
) -> Action | HTTPValidationError | None:
    """Create Action

     Create and validate a new action through Constitutional AI

    Args:
        body (ActionCreate): Request to create/propose a new action. Example: {'action_type':
            'restart_service', 'confidence': 0.88, 'description': 'Restart payment-service to clear
            memory leak', 'evidence': {'memory_usage': 0.95, 'restart_history': 'No restarts in 24h'},
            'incident_id': 'INC-2024-042', 'parameters': {'graceful': True, 'timeout': 30},
            'target_instance': 'payment-service-abc123', 'target_service': 'payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Action | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ActionCreate,
) -> Response[Action | HTTPValidationError]:
    """Create Action

     Create and validate a new action through Constitutional AI

    Args:
        body (ActionCreate): Request to create/propose a new action. Example: {'action_type':
            'restart_service', 'confidence': 0.88, 'description': 'Restart payment-service to clear
            memory leak', 'evidence': {'memory_usage': 0.95, 'restart_history': 'No restarts in 24h'},
            'incident_id': 'INC-2024-042', 'parameters': {'graceful': True, 'timeout': 30},
            'target_instance': 'payment-service-abc123', 'target_service': 'payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Action | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ActionCreate,
) -> Action | HTTPValidationError | None:
    """Create Action

     Create and validate a new action through Constitutional AI

    Args:
        body (ActionCreate): Request to create/propose a new action. Example: {'action_type':
            'restart_service', 'confidence': 0.88, 'description': 'Restart payment-service to clear
            memory leak', 'evidence': {'memory_usage': 0.95, 'restart_history': 'No restarts in 24h'},
            'incident_id': 'INC-2024-042', 'parameters': {'graceful': True, 'timeout': 30},
            'target_instance': 'payment-service-abc123', 'target_service': 'payment-service'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Action | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
