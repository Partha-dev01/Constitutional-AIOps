from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.incident import Incident
from ...types import UNSET, Response, Unset


def _get_kwargs(
    incident_id: str,
    *,
    enable_thinking: bool | Unset = True,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["enable_thinking"] = enable_thinking

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/incidents/{incident_id}/analyze".format(
            incident_id=quote(str(incident_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | Incident | None:
    if response.status_code == 200:
        response_200 = Incident.from_dict(response.json())

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
) -> Response[HTTPValidationError | Incident]:
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
    enable_thinking: bool | Unset = True,
) -> Response[HTTPValidationError | Incident]:
    """Trigger RCA

     Trigger root cause analysis for an incident

    Args:
        incident_id (str):
        enable_thinking (bool | Unset): Enable extended thinking Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Incident]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        enable_thinking=enable_thinking,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    enable_thinking: bool | Unset = True,
) -> HTTPValidationError | Incident | None:
    """Trigger RCA

     Trigger root cause analysis for an incident

    Args:
        incident_id (str):
        enable_thinking (bool | Unset): Enable extended thinking Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Incident
    """

    return sync_detailed(
        incident_id=incident_id,
        client=client,
        enable_thinking=enable_thinking,
    ).parsed


async def asyncio_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    enable_thinking: bool | Unset = True,
) -> Response[HTTPValidationError | Incident]:
    """Trigger RCA

     Trigger root cause analysis for an incident

    Args:
        incident_id (str):
        enable_thinking (bool | Unset): Enable extended thinking Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | Incident]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        enable_thinking=enable_thinking,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    incident_id: str,
    *,
    client: AuthenticatedClient | Client,
    enable_thinking: bool | Unset = True,
) -> HTTPValidationError | Incident | None:
    """Trigger RCA

     Trigger root cause analysis for an incident

    Args:
        incident_id (str):
        enable_thinking (bool | Unset): Enable extended thinking Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | Incident
    """

    return (
        await asyncio_detailed(
            incident_id=incident_id,
            client=client,
            enable_thinking=enable_thinking,
        )
    ).parsed
