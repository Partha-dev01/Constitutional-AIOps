from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.benchmark_request import BenchmarkRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: BenchmarkRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/benchmark/run",
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
    body: BenchmarkRequest,
) -> Response[Any | HTTPValidationError]:
    """Run Benchmark

     Start a benchmark run.

    Admin only: the full research-benchmark harness runs against the box's
    configured (owner) endpoint, so a regular tenant must not be able to spend
    the owner key here (BYOK). Per-tenant "evaluate my own endpoint" is a
    future feature that would route through the caller's BYOK config.

    This runs in the background and returns immediately with a job ID.
    Use /status to check progress.

    Args:
        body (BenchmarkRequest): Request to start a benchmark.

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
    body: BenchmarkRequest,
) -> Any | HTTPValidationError | None:
    """Run Benchmark

     Start a benchmark run.

    Admin only: the full research-benchmark harness runs against the box's
    configured (owner) endpoint, so a regular tenant must not be able to spend
    the owner key here (BYOK). Per-tenant "evaluate my own endpoint" is a
    future feature that would route through the caller's BYOK config.

    This runs in the background and returns immediately with a job ID.
    Use /status to check progress.

    Args:
        body (BenchmarkRequest): Request to start a benchmark.

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
    body: BenchmarkRequest,
) -> Response[Any | HTTPValidationError]:
    """Run Benchmark

     Start a benchmark run.

    Admin only: the full research-benchmark harness runs against the box's
    configured (owner) endpoint, so a regular tenant must not be able to spend
    the owner key here (BYOK). Per-tenant "evaluate my own endpoint" is a
    future feature that would route through the caller's BYOK config.

    This runs in the background and returns immediately with a job ID.
    Use /status to check progress.

    Args:
        body (BenchmarkRequest): Request to start a benchmark.

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
    body: BenchmarkRequest,
) -> Any | HTTPValidationError | None:
    """Run Benchmark

     Start a benchmark run.

    Admin only: the full research-benchmark harness runs against the box's
    configured (owner) endpoint, so a regular tenant must not be able to spend
    the owner key here (BYOK). Per-tenant "evaluate my own endpoint" is a
    future feature that would route through the caller's BYOK config.

    This runs in the background and returns immediately with a job ID.
    Use /status to check progress.

    Args:
        body (BenchmarkRequest): Request to start a benchmark.

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
