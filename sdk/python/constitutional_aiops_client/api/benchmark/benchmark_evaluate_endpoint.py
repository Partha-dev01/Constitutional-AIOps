from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.evaluate_endpoint_request import EvaluateEndpointRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: EvaluateEndpointRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/benchmark/evaluate-endpoint",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EvaluateEndpointRequest,
) -> Response[Any | HTTPValidationError]:
    """Evaluate Endpoint

     Quick check: run a few sample cases against the configured LLM endpoint.

    For self-hosters who want to know "is the model I pointed the app at good
    enough for this workload" without committing to a full benchmark run. Uses
    the same agents and scoring as the research benchmark, on a handful of cases,
    synchronously.

    Admin only: it exercises the box's configured (owner) endpoint via the
    shared runner, so a regular tenant must not reach it and spend the owner
    key (BYOK).

    Args:
        body (EvaluateEndpointRequest): Request for the self-hoster 'evaluate my configured
            endpoint' quick-check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
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
    body: EvaluateEndpointRequest,
) -> Any | HTTPValidationError | None:
    """Evaluate Endpoint

     Quick check: run a few sample cases against the configured LLM endpoint.

    For self-hosters who want to know "is the model I pointed the app at good
    enough for this workload" without committing to a full benchmark run. Uses
    the same agents and scoring as the research benchmark, on a handful of cases,
    synchronously.

    Admin only: it exercises the box's configured (owner) endpoint via the
    shared runner, so a regular tenant must not reach it and spend the owner
    key (BYOK).

    Args:
        body (EvaluateEndpointRequest): Request for the self-hoster 'evaluate my configured
            endpoint' quick-check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EvaluateEndpointRequest,
) -> Response[Any | HTTPValidationError]:
    """Evaluate Endpoint

     Quick check: run a few sample cases against the configured LLM endpoint.

    For self-hosters who want to know "is the model I pointed the app at good
    enough for this workload" without committing to a full benchmark run. Uses
    the same agents and scoring as the research benchmark, on a handful of cases,
    synchronously.

    Admin only: it exercises the box's configured (owner) endpoint via the
    shared runner, so a regular tenant must not reach it and spend the owner
    key (BYOK).

    Args:
        body (EvaluateEndpointRequest): Request for the self-hoster 'evaluate my configured
            endpoint' quick-check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: EvaluateEndpointRequest,
) -> Any | HTTPValidationError | None:
    """Evaluate Endpoint

     Quick check: run a few sample cases against the configured LLM endpoint.

    For self-hosters who want to know "is the model I pointed the app at good
    enough for this workload" without committing to a full benchmark run. Uses
    the same agents and scoring as the research benchmark, on a handful of cases,
    synchronously.

    Admin only: it exercises the box's configured (owner) endpoint via the
    shared runner, so a regular tenant must not reach it and spend the owner
    key (BYOK).

    Args:
        body (EvaluateEndpointRequest): Request for the self-hoster 'evaluate my configured
            endpoint' quick-check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
