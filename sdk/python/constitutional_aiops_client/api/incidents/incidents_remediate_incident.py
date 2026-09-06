from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.incidents_remediate_incident_response_incidents_remediate_incident import (
    IncidentsRemediateIncidentResponseIncidentsRemediateIncident,
)
from ...types import Response


def _get_kwargs(
    incident_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/incidents/{incident_id}/remediate".format(
            incident_id=quote(str(incident_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
    | None
):
    if response.status_code == 200:
        response_200 = (
            IncidentsRemediateIncidentResponseIncidentsRemediateIncident.from_dict(
                response.json()
            )
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
    HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
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
) -> Response[
    HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
]:
    """Remediate Incident

     Approve-and-remediate an incident. Demo incidents heal the injected fault on the t3 control agent;
    real incidents restart the affected service through the constitutional gate (same path as chat
    approve-to-run, so Tier-1 safety + the action kill-switch + whitelist all still apply). The verdict
    is surfaced in the response.

    Args:
        incident_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
    | None
):
    """Remediate Incident

     Approve-and-remediate an incident. Demo incidents heal the injected fault on the t3 control agent;
    real incidents restart the affected service through the constitutional gate (same path as chat
    approve-to-run, so Tier-1 safety + the action kill-switch + whitelist all still apply). The verdict
    is surfaced in the response.

    Args:
        incident_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
    """

    return sync_detailed(
        incident_id=incident_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
]:
    """Remediate Incident

     Approve-and-remediate an incident. Demo incidents heal the injected fault on the t3 control agent;
    real incidents restart the affected service through the constitutional gate (same path as chat
    approve-to-run, so Tier-1 safety + the action kill-switch + whitelist all still apply). The verdict
    is surfaced in the response.

    Args:
        incident_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    HTTPValidationError
    | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
    | None
):
    """Remediate Incident

     Approve-and-remediate an incident. Demo incidents heal the injected fault on the t3 control agent;
    real incidents restart the affected service through the constitutional gate (same path as chat
    approve-to-run, so Tier-1 safety + the action kill-switch + whitelist all still apply). The verdict
    is surfaced in the response.

    Args:
        incident_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IncidentsRemediateIncidentResponseIncidentsRemediateIncident
    """

    return (
        await asyncio_detailed(
            incident_id=incident_id,
            client=client,
        )
    ).parsed
