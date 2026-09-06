from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.decision_request import DecisionRequest
from ...models.decision_response import DecisionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    action_id: str,
    *,
    body: DecisionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/chat/actions/{action_id}/decision".format(
            action_id=quote(str(action_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DecisionResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DecisionResponse.from_dict(response.json())

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
) -> Response[DecisionResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    action_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DecisionRequest,
) -> Response[DecisionResponse | HTTPValidationError]:
    """Decide On A Proposed Remediation

     Approve or reject a remediation action that the AI proposed in approve/auto mode. On approval the
    cached action is executed through the constitutionally gated path (execute_tool_call); on rejection
    nothing runs.

    Args:
        action_id (str):
        body (DecisionRequest): User decision on a proposed remediation action (approve-to-run
            protocol). Example: {'approved': True, 'comment': 'Confirmed: restart the DB container'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DecisionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        action_id=action_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    action_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DecisionRequest,
) -> DecisionResponse | HTTPValidationError | None:
    """Decide On A Proposed Remediation

     Approve or reject a remediation action that the AI proposed in approve/auto mode. On approval the
    cached action is executed through the constitutionally gated path (execute_tool_call); on rejection
    nothing runs.

    Args:
        action_id (str):
        body (DecisionRequest): User decision on a proposed remediation action (approve-to-run
            protocol). Example: {'approved': True, 'comment': 'Confirmed: restart the DB container'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DecisionResponse | HTTPValidationError
    """

    return sync_detailed(
        action_id=action_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    action_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DecisionRequest,
) -> Response[DecisionResponse | HTTPValidationError]:
    """Decide On A Proposed Remediation

     Approve or reject a remediation action that the AI proposed in approve/auto mode. On approval the
    cached action is executed through the constitutionally gated path (execute_tool_call); on rejection
    nothing runs.

    Args:
        action_id (str):
        body (DecisionRequest): User decision on a proposed remediation action (approve-to-run
            protocol). Example: {'approved': True, 'comment': 'Confirmed: restart the DB container'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DecisionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        action_id=action_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    action_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DecisionRequest,
) -> DecisionResponse | HTTPValidationError | None:
    """Decide On A Proposed Remediation

     Approve or reject a remediation action that the AI proposed in approve/auto mode. On approval the
    cached action is executed through the constitutionally gated path (execute_tool_call); on rejection
    nothing runs.

    Args:
        action_id (str):
        body (DecisionRequest): User decision on a proposed remediation action (approve-to-run
            protocol). Example: {'approved': True, 'comment': 'Confirmed: restart the DB container'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DecisionResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            action_id=action_id,
            client=client,
            body=body,
        )
    ).parsed
