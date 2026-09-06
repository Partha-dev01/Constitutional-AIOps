from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_schema_request import GenerateSchemaRequest
from ...models.generate_schema_response import GenerateSchemaResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: GenerateSchemaRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/topology/schema/generate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GenerateSchemaResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GenerateSchemaResponse.from_dict(response.json())

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
) -> Response[GenerateSchemaResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateSchemaRequest,
) -> Response[GenerateSchemaResponse | HTTPValidationError]:
    """Generate Topology Schema (LLM preview)

     Have the Qwen3-14B reasoning model generate a candidate topology schema from a natural-language
    prompt. The candidate is strictly validated and returned as a PREVIEW (NOT persisted). Retries once
    on invalid LLM output, then returns a structured 422. Never crashes, never persists unvalidated
    output. Admin only.

    Args:
        body (GenerateSchemaRequest): Natural-language prompt for the 14B schema generator.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateSchemaResponse | HTTPValidationError]
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
    body: GenerateSchemaRequest,
) -> GenerateSchemaResponse | HTTPValidationError | None:
    """Generate Topology Schema (LLM preview)

     Have the Qwen3-14B reasoning model generate a candidate topology schema from a natural-language
    prompt. The candidate is strictly validated and returned as a PREVIEW (NOT persisted). Retries once
    on invalid LLM output, then returns a structured 422. Never crashes, never persists unvalidated
    output. Admin only.

    Args:
        body (GenerateSchemaRequest): Natural-language prompt for the 14B schema generator.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateSchemaResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateSchemaRequest,
) -> Response[GenerateSchemaResponse | HTTPValidationError]:
    """Generate Topology Schema (LLM preview)

     Have the Qwen3-14B reasoning model generate a candidate topology schema from a natural-language
    prompt. The candidate is strictly validated and returned as a PREVIEW (NOT persisted). Retries once
    on invalid LLM output, then returns a structured 422. Never crashes, never persists unvalidated
    output. Admin only.

    Args:
        body (GenerateSchemaRequest): Natural-language prompt for the 14B schema generator.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateSchemaResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateSchemaRequest,
) -> GenerateSchemaResponse | HTTPValidationError | None:
    """Generate Topology Schema (LLM preview)

     Have the Qwen3-14B reasoning model generate a candidate topology schema from a natural-language
    prompt. The candidate is strictly validated and returned as a PREVIEW (NOT persisted). Retries once
    on invalid LLM output, then returns a structured 422. Never crashes, never persists unvalidated
    output. Admin only.

    Args:
        body (GenerateSchemaRequest): Natural-language prompt for the 14B schema generator.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateSchemaResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
