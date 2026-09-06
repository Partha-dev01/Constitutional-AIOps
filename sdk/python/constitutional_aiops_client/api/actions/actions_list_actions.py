from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.action_list import ActionList
from ...models.action_status import ActionStatus
from ...models.action_type import ActionType
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[ActionStatus] | None | Unset = UNSET,
    action_type: list[ActionType] | None | Unset = UNSET,
    target_service: None | str | Unset = UNSET,
    incident_id: None | str | Unset = UNSET,
    requires_approval: bool | None | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    json_status: list[str] | None | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, list):
        json_status = []
        for status_type_0_item_data in status:
            status_type_0_item = status_type_0_item_data.value
            json_status.append(status_type_0_item)

    else:
        json_status = status
    params["status"] = json_status

    json_action_type: list[str] | None | Unset
    if isinstance(action_type, Unset):
        json_action_type = UNSET
    elif isinstance(action_type, list):
        json_action_type = []
        for action_type_type_0_item_data in action_type:
            action_type_type_0_item = action_type_type_0_item_data.value
            json_action_type.append(action_type_type_0_item)

    else:
        json_action_type = action_type
    params["action_type"] = json_action_type

    json_target_service: None | str | Unset
    if isinstance(target_service, Unset):
        json_target_service = UNSET
    else:
        json_target_service = target_service
    params["target_service"] = json_target_service

    json_incident_id: None | str | Unset
    if isinstance(incident_id, Unset):
        json_incident_id = UNSET
    else:
        json_incident_id = incident_id
    params["incident_id"] = json_incident_id

    json_requires_approval: bool | None | Unset
    if isinstance(requires_approval, Unset):
        json_requires_approval = UNSET
    else:
        json_requires_approval = requires_approval
    params["requires_approval"] = json_requires_approval

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/actions/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ActionList | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ActionList.from_dict(response.json())

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
) -> Response[ActionList | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[ActionStatus] | None | Unset = UNSET,
    action_type: list[ActionType] | None | Unset = UNSET,
    target_service: None | str | Unset = UNSET,
    incident_id: None | str | Unset = UNSET,
    requires_approval: bool | None | Unset = UNSET,
) -> Response[ActionList | HTTPValidationError]:
    """List Actions

     Get paginated list of actions with optional filters

    Args:
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.
        status (list[ActionStatus] | None | Unset):
        action_type (list[ActionType] | None | Unset):
        target_service (None | str | Unset):
        incident_id (None | str | Unset):
        requires_approval (bool | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ActionList | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        action_type=action_type,
        target_service=target_service,
        incident_id=incident_id,
        requires_approval=requires_approval,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[ActionStatus] | None | Unset = UNSET,
    action_type: list[ActionType] | None | Unset = UNSET,
    target_service: None | str | Unset = UNSET,
    incident_id: None | str | Unset = UNSET,
    requires_approval: bool | None | Unset = UNSET,
) -> ActionList | HTTPValidationError | None:
    """List Actions

     Get paginated list of actions with optional filters

    Args:
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.
        status (list[ActionStatus] | None | Unset):
        action_type (list[ActionType] | None | Unset):
        target_service (None | str | Unset):
        incident_id (None | str | Unset):
        requires_approval (bool | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ActionList | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        status=status,
        action_type=action_type,
        target_service=target_service,
        incident_id=incident_id,
        requires_approval=requires_approval,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[ActionStatus] | None | Unset = UNSET,
    action_type: list[ActionType] | None | Unset = UNSET,
    target_service: None | str | Unset = UNSET,
    incident_id: None | str | Unset = UNSET,
    requires_approval: bool | None | Unset = UNSET,
) -> Response[ActionList | HTTPValidationError]:
    """List Actions

     Get paginated list of actions with optional filters

    Args:
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.
        status (list[ActionStatus] | None | Unset):
        action_type (list[ActionType] | None | Unset):
        target_service (None | str | Unset):
        incident_id (None | str | Unset):
        requires_approval (bool | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ActionList | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        action_type=action_type,
        target_service=target_service,
        incident_id=incident_id,
        requires_approval=requires_approval,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[ActionStatus] | None | Unset = UNSET,
    action_type: list[ActionType] | None | Unset = UNSET,
    target_service: None | str | Unset = UNSET,
    incident_id: None | str | Unset = UNSET,
    requires_approval: bool | None | Unset = UNSET,
) -> ActionList | HTTPValidationError | None:
    """List Actions

     Get paginated list of actions with optional filters

    Args:
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 20.
        status (list[ActionStatus] | None | Unset):
        action_type (list[ActionType] | None | Unset):
        target_service (None | str | Unset):
        incident_id (None | str | Unset):
        requires_approval (bool | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ActionList | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            status=status,
            action_type=action_type,
            target_service=target_service,
            incident_id=incident_id,
            requires_approval=requires_approval,
        )
    ).parsed
