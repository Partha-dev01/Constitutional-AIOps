from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.incidents_find_similar_incidents_response_incidents_find_similar_incidents import (
    IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    incident_id: str,
    *,
    limit: int | Unset = 5,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/incidents/{incident_id}/similar".format(
            incident_id=quote(str(incident_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
    | None
):
    if response.status_code == 200:
        response_200 = IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents.from_dict(
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
) -> Response[
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> Response[
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
]:
    """Find Similar Incidents

     Find similar incidents from graph memory

    Args:
        incident_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> (
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
    | None
):
    """Find Similar Incidents

     Find similar incidents from graph memory

    Args:
        incident_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
    """

    return sync_detailed(
        incident_id=incident_id,
        client=client,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> Response[
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
]:
    """Find Similar Incidents

     Find similar incidents from graph memory

    Args:
        incident_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> (
    HTTPValidationError
    | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
    | None
):
    """Find Similar Incidents

     Find similar incidents from graph memory

    Args:
        incident_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentsFindSimilarIncidentsResponseIncidentsFindSimilarIncidents
    """

    return (
        await asyncio_detailed(
            incident_id=incident_id,
            client=client,
            limit=limit,
        )
    ).parsed
