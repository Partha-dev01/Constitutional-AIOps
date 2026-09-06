from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.similar_episode import SimilarEpisode
from ...types import UNSET, Response, Unset


def _get_kwargs(
    episode_id: str,
    *,
    limit: int | Unset = 5,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/graph/episodes/{episode_id}/similar".format(
            episode_id=quote(str(episode_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[SimilarEpisode] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = SimilarEpisode.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[SimilarEpisode]]:
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
    limit: int | Unset = 5,
) -> Response[HTTPValidationError | list[SimilarEpisode]]:
    """Find Similar Episodes

     Find episodes similar to the specified one

    Args:
        episode_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[SimilarEpisode]]
    """

    kwargs = _get_kwargs(
        episode_id=episode_id,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> HTTPValidationError | list[SimilarEpisode] | None:
    """Find Similar Episodes

     Find episodes similar to the specified one

    Args:
        episode_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[SimilarEpisode]
    """

    return sync_detailed(
        episode_id=episode_id,
        client=client,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> Response[HTTPValidationError | list[SimilarEpisode]]:
    """Find Similar Episodes

     Find episodes similar to the specified one

    Args:
        episode_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[SimilarEpisode]]
    """

    kwargs = _get_kwargs(
        episode_id=episode_id,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    episode_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 5,
) -> HTTPValidationError | list[SimilarEpisode] | None:
    """Find Similar Episodes

     Find episodes similar to the specified one

    Args:
        episode_id (str):
        limit (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[SimilarEpisode]
    """

    return (
        await asyncio_detailed(
            episode_id=episode_id,
            client=client,
            limit=limit,
        )
    ).parsed
