from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.incident_category import IncidentCategory
from ...models.incident_list import IncidentList
from ...models.incident_severity import IncidentSeverity
from ...models.incident_status import IncidentStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[IncidentStatus] | None | Unset = UNSET,
    severity: list[IncidentSeverity] | None | Unset = UNSET,
    category: list[IncidentCategory] | None | Unset = UNSET,
    service: None | str | Unset = UNSET,
    search: None | str | Unset = UNSET,
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

    json_severity: list[str] | None | Unset
    if isinstance(severity, Unset):
        json_severity = UNSET
    elif isinstance(severity, list):
        json_severity = []
        for severity_type_0_item_data in severity:
            severity_type_0_item = severity_type_0_item_data.value
            json_severity.append(severity_type_0_item)

    else:
        json_severity = severity
    params["severity"] = json_severity

    json_category: list[str] | None | Unset
    if isinstance(category, Unset):
        json_category = UNSET
    elif isinstance(category, list):
        json_category = []
        for category_type_0_item_data in category:
            category_type_0_item = category_type_0_item_data.value
            json_category.append(category_type_0_item)

    else:
        json_category = category
    params["category"] = json_category

    json_service: None | str | Unset
    if isinstance(service, Unset):
        json_service = UNSET
    else:
        json_service = service
    params["service"] = json_service

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/incidents/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | IncidentList | None:
    if response.status_code == 200:
        response_200 = IncidentList.from_dict(response.json())

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
) -> Response[HTTPValidationError | IncidentList]:
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
    status: list[IncidentStatus] | None | Unset = UNSET,
    severity: list[IncidentSeverity] | None | Unset = UNSET,
    category: list[IncidentCategory] | None | Unset = UNSET,
    service: None | str | Unset = UNSET,
    search: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | IncidentList]:
    """List Incidents

     Get paginated list of incidents with optional filters

    Args:
        page (int | Unset): Page number Default: 1.
        page_size (int | Unset): Items per page Default: 20.
        status (list[IncidentStatus] | None | Unset): Filter by status
        severity (list[IncidentSeverity] | None | Unset): Filter by severity
        category (list[IncidentCategory] | None | Unset): Filter by category
        service (None | str | Unset): Filter by affected service
        search (None | str | Unset): Search in title/description

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentList]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        category=category,
        service=service,
        search=search,
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
    status: list[IncidentStatus] | None | Unset = UNSET,
    severity: list[IncidentSeverity] | None | Unset = UNSET,
    category: list[IncidentCategory] | None | Unset = UNSET,
    service: None | str | Unset = UNSET,
    search: None | str | Unset = UNSET,
) -> HTTPValidationError | IncidentList | None:
    """List Incidents

     Get paginated list of incidents with optional filters

    Args:
        page (int | Unset): Page number Default: 1.
        page_size (int | Unset): Items per page Default: 20.
        status (list[IncidentStatus] | None | Unset): Filter by status
        severity (list[IncidentSeverity] | None | Unset): Filter by severity
        category (list[IncidentCategory] | None | Unset): Filter by category
        service (None | str | Unset): Filter by affected service
        search (None | str | Unset): Search in title/description

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentList
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        category=category,
        service=service,
        search=search,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[IncidentStatus] | None | Unset = UNSET,
    severity: list[IncidentSeverity] | None | Unset = UNSET,
    category: list[IncidentCategory] | None | Unset = UNSET,
    service: None | str | Unset = UNSET,
    search: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | IncidentList]:
    """List Incidents

     Get paginated list of incidents with optional filters

    Args:
        page (int | Unset): Page number Default: 1.
        page_size (int | Unset): Items per page Default: 20.
        status (list[IncidentStatus] | None | Unset): Filter by status
        severity (list[IncidentSeverity] | None | Unset): Filter by severity
        category (list[IncidentCategory] | None | Unset): Filter by category
        service (None | str | Unset): Filter by affected service
        search (None | str | Unset): Search in title/description

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentList]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        category=category,
        service=service,
        search=search,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[IncidentStatus] | None | Unset = UNSET,
    severity: list[IncidentSeverity] | None | Unset = UNSET,
    category: list[IncidentCategory] | None | Unset = UNSET,
    service: None | str | Unset = UNSET,
    search: None | str | Unset = UNSET,
) -> HTTPValidationError | IncidentList | None:
    """List Incidents

     Get paginated list of incidents with optional filters

    Args:
        page (int | Unset): Page number Default: 1.
        page_size (int | Unset): Items per page Default: 20.
        status (list[IncidentStatus] | None | Unset): Filter by status
        severity (list[IncidentSeverity] | None | Unset): Filter by severity
        category (list[IncidentCategory] | None | Unset): Filter by category
        service (None | str | Unset): Filter by affected service
        search (None | str | Unset): Search in title/description

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentList
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            status=status,
            severity=severity,
            category=category,
            service=service,
            search=search,
        )
    ).parsed
