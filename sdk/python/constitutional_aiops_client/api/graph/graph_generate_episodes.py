from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_episodes_request import GenerateEpisodesRequest
from ...models.generate_episodes_response import GenerateEpisodesResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: GenerateEpisodesRequest | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/graph/generate-episodes",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GenerateEpisodesResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GenerateEpisodesResponse.from_dict(response.json())

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
) -> Response[GenerateEpisodesResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateEpisodesRequest | Unset = UNSET,
) -> Response[GenerateEpisodesResponse | HTTPValidationError]:
    """Generate Episodes via Reasoning Agent

     Generate realistic demo episodes using Qwen3-14B based on actual service templates

    Args:
        body (GenerateEpisodesRequest | Unset): Request to generate demo episodes via Reasoning
            Agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateEpisodesResponse | HTTPValidationError]
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
    body: GenerateEpisodesRequest | Unset = UNSET,
) -> GenerateEpisodesResponse | HTTPValidationError | None:
    """Generate Episodes via Reasoning Agent

     Generate realistic demo episodes using Qwen3-14B based on actual service templates

    Args:
        body (GenerateEpisodesRequest | Unset): Request to generate demo episodes via Reasoning
            Agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateEpisodesResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateEpisodesRequest | Unset = UNSET,
) -> Response[GenerateEpisodesResponse | HTTPValidationError]:
    """Generate Episodes via Reasoning Agent

     Generate realistic demo episodes using Qwen3-14B based on actual service templates

    Args:
        body (GenerateEpisodesRequest | Unset): Request to generate demo episodes via Reasoning
            Agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateEpisodesResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateEpisodesRequest | Unset = UNSET,
) -> GenerateEpisodesResponse | HTTPValidationError | None:
    """Generate Episodes via Reasoning Agent

     Generate realistic demo episodes using Qwen3-14B based on actual service templates

    Args:
        body (GenerateEpisodesRequest | Unset): Request to generate demo episodes via Reasoning
            Agent.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateEpisodesResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
