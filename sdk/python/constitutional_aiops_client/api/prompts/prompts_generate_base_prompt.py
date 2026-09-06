from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_prompt_request import GeneratePromptRequest
from ...models.generate_prompt_response import GeneratePromptResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: GeneratePromptRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/prompts/generate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GeneratePromptResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GeneratePromptResponse.from_dict(response.json())

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
) -> Response[GeneratePromptResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GeneratePromptRequest,
) -> Response[GeneratePromptResponse | HTTPValidationError]:
    """Generate Base Prompt (onboarding)

     Draft a base operations-assistant system prompt from the services + topology entered in the
    onboarding wizard. ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines it
    with the reasoning model and falls back to the template on any failure. The draft is NOT persisted —
    Apply it via PUT /prompts/reasoning_chat. Admin only.

    Args:
        body (GeneratePromptRequest): Onboarding wizard: draft a base prompt from services +
            topology.

            ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
            it with the reasoning model, FALLING BACK to the template on any failure so
            setup never breaks. The draft is NOT persisted — the wizard Applies it via
            ``PUT /prompts/reasoning_chat``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GeneratePromptResponse | HTTPValidationError]
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
    body: GeneratePromptRequest,
) -> GeneratePromptResponse | HTTPValidationError | None:
    """Generate Base Prompt (onboarding)

     Draft a base operations-assistant system prompt from the services + topology entered in the
    onboarding wizard. ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines it
    with the reasoning model and falls back to the template on any failure. The draft is NOT persisted —
    Apply it via PUT /prompts/reasoning_chat. Admin only.

    Args:
        body (GeneratePromptRequest): Onboarding wizard: draft a base prompt from services +
            topology.

            ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
            it with the reasoning model, FALLING BACK to the template on any failure so
            setup never breaks. The draft is NOT persisted — the wizard Applies it via
            ``PUT /prompts/reasoning_chat``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GeneratePromptResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GeneratePromptRequest,
) -> Response[GeneratePromptResponse | HTTPValidationError]:
    """Generate Base Prompt (onboarding)

     Draft a base operations-assistant system prompt from the services + topology entered in the
    onboarding wizard. ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines it
    with the reasoning model and falls back to the template on any failure. The draft is NOT persisted —
    Apply it via PUT /prompts/reasoning_chat. Admin only.

    Args:
        body (GeneratePromptRequest): Onboarding wizard: draft a base prompt from services +
            topology.

            ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
            it with the reasoning model, FALLING BACK to the template on any failure so
            setup never breaks. The draft is NOT persisted — the wizard Applies it via
            ``PUT /prompts/reasoning_chat``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GeneratePromptResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GeneratePromptRequest,
) -> GeneratePromptResponse | HTTPValidationError | None:
    """Generate Base Prompt (onboarding)

     Draft a base operations-assistant system prompt from the services + topology entered in the
    onboarding wizard. ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines it
    with the reasoning model and falls back to the template on any failure. The draft is NOT persisted —
    Apply it via PUT /prompts/reasoning_chat. Admin only.

    Args:
        body (GeneratePromptRequest): Onboarding wizard: draft a base prompt from services +
            topology.

            ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
            it with the reasoning model, FALLING BACK to the template on any failure so
            setup never breaks. The draft is NOT persisted — the wizard Applies it via
            ``PUT /prompts/reasoning_chat``.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GeneratePromptResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
