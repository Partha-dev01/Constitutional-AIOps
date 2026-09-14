from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.explain_request import ExplainRequest
from ...models.explain_response import ExplainResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: ExplainRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/insights/explain",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExplainResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ExplainResponse.from_dict(response.json())

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
) -> Response[ExplainResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ExplainRequest,
) -> Response[ExplainResponse | HTTPValidationError]:
    """Explain a widget's computed data

     Return a short, model-generated plain-language explanation of a widget's already-computed data. Opt-
    in and cost-fenced; degrades to a uniform available=false body when disabled, over budget, or
    without an endpoint.

    Args:
        body (ExplainRequest): A request for a plain-language explanation of a widget's computed
            data.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExplainResponse | HTTPValidationError]
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
    body: ExplainRequest,
) -> ExplainResponse | HTTPValidationError | None:
    """Explain a widget's computed data

     Return a short, model-generated plain-language explanation of a widget's already-computed data. Opt-
    in and cost-fenced; degrades to a uniform available=false body when disabled, over budget, or
    without an endpoint.

    Args:
        body (ExplainRequest): A request for a plain-language explanation of a widget's computed
            data.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExplainResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ExplainRequest,
) -> Response[ExplainResponse | HTTPValidationError]:
    """Explain a widget's computed data

     Return a short, model-generated plain-language explanation of a widget's already-computed data. Opt-
    in and cost-fenced; degrades to a uniform available=false body when disabled, over budget, or
    without an endpoint.

    Args:
        body (ExplainRequest): A request for a plain-language explanation of a widget's computed
            data.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExplainResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ExplainRequest,
) -> ExplainResponse | HTTPValidationError | None:
    """Explain a widget's computed data

     Return a short, model-generated plain-language explanation of a widget's already-computed data. Opt-
    in and cost-fenced; degrades to a uniform available=false body when disabled, over budget, or
    without an endpoint.

    Args:
        body (ExplainRequest): A request for a plain-language explanation of a widget's computed
            data.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExplainResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
