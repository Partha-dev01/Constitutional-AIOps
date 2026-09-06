from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.episode import Episode
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    episode_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/episodes/{episode_id}".format(
            episode_id=quote(str(episode_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Episode | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = Episode.from_dict(response.json())

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
) -> Response[Episode | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Episode | HTTPValidationError]:
    """Get Episode Details

     Get detailed information about a specific episode

    Args:
        episode_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Episode | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        episode_id=episode_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Episode | HTTPValidationError | None:
    """Get Episode Details

     Get detailed information about a specific episode

    Args:
        episode_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Episode | HTTPValidationError
    """

    return sync_detailed(
        episode_id=episode_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Episode | HTTPValidationError]:
    """Get Episode Details

     Get detailed information about a specific episode

    Args:
        episode_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Episode | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        episode_id=episode_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Episode | HTTPValidationError | None:
    """Get Episode Details

     Get detailed information about a specific episode

    Args:
        episode_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Episode | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            episode_id=episode_id,
            client=client,
        )
    ).parsed
