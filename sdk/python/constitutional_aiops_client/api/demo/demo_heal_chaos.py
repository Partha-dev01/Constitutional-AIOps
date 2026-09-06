from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.chaos_action_response import ChaosActionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    scenario: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/demo/chaos/{scenario}/heal".format(
            scenario=quote(str(scenario), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ChaosActionResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ChaosActionResponse.from_dict(response.json())

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
) -> Response[ChaosActionResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    scenario: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ChaosActionResponse | HTTPValidationError]:
    """Heal Chaos Scenario

     Heal/undo a chaos scenario on the t3.

    Args:
        scenario (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ChaosActionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        scenario=scenario,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    scenario: str,
    *,
    client: AuthenticatedClient | Client,
) -> ChaosActionResponse | HTTPValidationError | None:
    """Heal Chaos Scenario

     Heal/undo a chaos scenario on the t3.

    Args:
        scenario (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ChaosActionResponse | HTTPValidationError
    """

    return sync_detailed(
        scenario=scenario,
        client=client,
    ).parsed


async def asyncio_detailed(
    scenario: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ChaosActionResponse | HTTPValidationError]:
    """Heal Chaos Scenario

     Heal/undo a chaos scenario on the t3.

    Args:
        scenario (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ChaosActionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        scenario=scenario,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    scenario: str,
    *,
    client: AuthenticatedClient | Client,
) -> ChaosActionResponse | HTTPValidationError | None:
    """Heal Chaos Scenario

     Heal/undo a chaos scenario on the t3.

    Args:
        scenario (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ChaosActionResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            scenario=scenario,
            client=client,
        )
    ).parsed
