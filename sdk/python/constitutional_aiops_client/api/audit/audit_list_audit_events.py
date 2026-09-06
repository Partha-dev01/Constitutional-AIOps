from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.audit_list_audit_events_response_audit_list_audit_events import (
    AuditListAuditEventsResponseAuditListAuditEvents,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 100,
    days: int | Unset = 7,
    event_type: None | str | Unset = UNSET,
    resource_type: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["days"] = days

    json_event_type: None | str | Unset
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    json_resource_type: None | str | Unset
    if isinstance(resource_type, Unset):
        json_resource_type = UNSET
    else:
        json_resource_type = resource_type
    params["resource_type"] = json_resource_type

    json_actor_id: None | str | Unset
    if isinstance(actor_id, Unset):
        json_actor_id = UNSET
    else:
        json_actor_id = actor_id
    params["actor_id"] = json_actor_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/audit/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuditListAuditEventsResponseAuditListAuditEvents.from_dict(
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
) -> Response[AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    days: int | Unset = 7,
    event_type: None | str | Unset = UNSET,
    resource_type: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
) -> Response[AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError]:
    """List Audit Events

     Return recent audit events, newest first. Admin only.

    An empty list is a normal, honest result on a fresh instance -- the trail
    only fills as validations, approvals and actions happen.

    Args:
        limit (int | Unset):  Default: 100.
        days (int | Unset):  Default: 7.
        event_type (None | str | Unset):
        resource_type (None | str | Unset):
        actor_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        limit=limit,
        days=days,
        event_type=event_type,
        resource_type=resource_type,
        actor_id=actor_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    days: int | Unset = 7,
    event_type: None | str | Unset = UNSET,
    resource_type: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
) -> AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError | None:
    """List Audit Events

     Return recent audit events, newest first. Admin only.

    An empty list is a normal, honest result on a fresh instance -- the trail
    only fills as validations, approvals and actions happen.

    Args:
        limit (int | Unset):  Default: 100.
        days (int | Unset):  Default: 7.
        event_type (None | str | Unset):
        resource_type (None | str | Unset):
        actor_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        limit=limit,
        days=days,
        event_type=event_type,
        resource_type=resource_type,
        actor_id=actor_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    days: int | Unset = 7,
    event_type: None | str | Unset = UNSET,
    resource_type: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
) -> Response[AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError]:
    """List Audit Events

     Return recent audit events, newest first. Admin only.

    An empty list is a normal, honest result on a fresh instance -- the trail
    only fills as validations, approvals and actions happen.

    Args:
        limit (int | Unset):  Default: 100.
        days (int | Unset):  Default: 7.
        event_type (None | str | Unset):
        resource_type (None | str | Unset):
        actor_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        limit=limit,
        days=days,
        event_type=event_type,
        resource_type=resource_type,
        actor_id=actor_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    days: int | Unset = 7,
    event_type: None | str | Unset = UNSET,
    resource_type: None | str | Unset = UNSET,
    actor_id: None | str | Unset = UNSET,
) -> AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError | None:
    """List Audit Events

     Return recent audit events, newest first. Admin only.

    An empty list is a normal, honest result on a fresh instance -- the trail
    only fills as validations, approvals and actions happen.

    Args:
        limit (int | Unset):  Default: 100.
        days (int | Unset):  Default: 7.
        event_type (None | str | Unset):
        resource_type (None | str | Unset):
        actor_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuditListAuditEventsResponseAuditListAuditEvents | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            days=days,
            event_type=event_type,
            resource_type=resource_type,
            actor_id=actor_id,
        )
    ).parsed
