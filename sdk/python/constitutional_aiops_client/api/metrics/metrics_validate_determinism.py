from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.metrics_validate_determinism_response_metrics_validate_determinism import (
    MetricsValidateDeterminismResponseMetricsValidateDeterminism,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: list[str] | None | Unset = UNSET,
    iterations: int | Unset = 5,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["iterations"] = iterations

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/metrics/validate/determinism",
        "params": params,
    }

    if isinstance(body, list):
        _kwargs["json"] = body

    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    HTTPValidationError
    | MetricsValidateDeterminismResponseMetricsValidateDeterminism
    | None
):
    if response.status_code == 200:
        response_200 = (
            MetricsValidateDeterminismResponseMetricsValidateDeterminism.from_dict(
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
    HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: list[str] | None | Unset = UNSET,
    iterations: int | Unset = 5,
) -> Response[
    HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism
]:
    """Validate Determinism

     Test output determinism with temperature=0

    Args:
        iterations (int | Unset):  Default: 5.
        body (list[str] | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism]
    """

    kwargs = _get_kwargs(
        body=body,
        iterations=iterations,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: list[str] | None | Unset = UNSET,
    iterations: int | Unset = 5,
) -> (
    HTTPValidationError
    | MetricsValidateDeterminismResponseMetricsValidateDeterminism
    | None
):
    """Validate Determinism

     Test output determinism with temperature=0

    Args:
        iterations (int | Unset):  Default: 5.
        body (list[str] | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism
    """

    return sync_detailed(
        client=client,
        body=body,
        iterations=iterations,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: list[str] | None | Unset = UNSET,
    iterations: int | Unset = 5,
) -> Response[
    HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism
]:
    """Validate Determinism

     Test output determinism with temperature=0

    Args:
        iterations (int | Unset):  Default: 5.
        body (list[str] | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism]
    """

    kwargs = _get_kwargs(
        body=body,
        iterations=iterations,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: list[str] | None | Unset = UNSET,
    iterations: int | Unset = 5,
) -> (
    HTTPValidationError
    | MetricsValidateDeterminismResponseMetricsValidateDeterminism
    | None
):
    """Validate Determinism

     Test output determinism with temperature=0

    Args:
        iterations (int | Unset):  Default: 5.
        body (list[str] | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MetricsValidateDeterminismResponseMetricsValidateDeterminism
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            iterations=iterations,
        )
    ).parsed
