from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.analysis_request import AnalysisRequest
from ...models.analysis_response import AnalysisResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: AnalysisRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/chat/analyze",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AnalysisResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AnalysisResponse.from_dict(response.json())

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
) -> Response[AnalysisResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AnalysisRequest,
) -> Response[AnalysisResponse | HTTPValidationError]:
    """Run Analysis

     Run RCA or planning analysis on incident data

    Args:
        body (AnalysisRequest): Request for RCA or planning analysis. Example: {'data':
            {'affected_services': ['api-gateway', 'user-service'], 'start_time':
            '2025-12-14T09:00:00Z', 'symptoms': ['High latency', 'Connection timeouts']},
            'enable_thinking': True, 'incident_id': 'INC-2024-042', 'mode': 'rca'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnalysisResponse | HTTPValidationError]
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
    body: AnalysisRequest,
) -> AnalysisResponse | HTTPValidationError | None:
    """Run Analysis

     Run RCA or planning analysis on incident data

    Args:
        body (AnalysisRequest): Request for RCA or planning analysis. Example: {'data':
            {'affected_services': ['api-gateway', 'user-service'], 'start_time':
            '2025-12-14T09:00:00Z', 'symptoms': ['High latency', 'Connection timeouts']},
            'enable_thinking': True, 'incident_id': 'INC-2024-042', 'mode': 'rca'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnalysisResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AnalysisRequest,
) -> Response[AnalysisResponse | HTTPValidationError]:
    """Run Analysis

     Run RCA or planning analysis on incident data

    Args:
        body (AnalysisRequest): Request for RCA or planning analysis. Example: {'data':
            {'affected_services': ['api-gateway', 'user-service'], 'start_time':
            '2025-12-14T09:00:00Z', 'symptoms': ['High latency', 'Connection timeouts']},
            'enable_thinking': True, 'incident_id': 'INC-2024-042', 'mode': 'rca'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnalysisResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AnalysisRequest,
) -> AnalysisResponse | HTTPValidationError | None:
    """Run Analysis

     Run RCA or planning analysis on incident data

    Args:
        body (AnalysisRequest): Request for RCA or planning analysis. Example: {'data':
            {'affected_services': ['api-gateway', 'user-service'], 'start_time':
            '2025-12-14T09:00:00Z', 'symptoms': ['High latency', 'Connection timeouts']},
            'enable_thinking': True, 'incident_id': 'INC-2024-042', 'mode': 'rca'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnalysisResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
