# app/services/acs_client.py
"""
Client for calling the internal XGBoost ACS scoring service.

This talks to xgboost_service over the app-net Docker network only —
that service has no public port mapping, so this call never leaves
the internal network.
"""

from uuid import UUID

import httpx

from app.core.config import settings


class ACSServiceError(Exception):
    """Raised when the ACS scoring service call fails or returns an error."""


async def acs_score_call(user_id: UUID, technical_scope: bool = False) -> dict:
    """
    Trigger scoring for a user via the internal xgboost_service and
    return its response.

    Args:
        user_id: The UMKM user's ID to score.
        technical_scope: Passed through to xgboost_service's own
            /{user_id}/score endpoint (controls response detail level).

    Returns:
        The parsed JSON response from xgboost_service — matches its
        ACSScoreResponse schema.

    Raises:
        ACSServiceError: on timeout, connection failure, a 400 from
        xgboost_service (e.g. bad user_id / no data to score), or any
        other non-2xx response.
    """
    url = f"{settings.XGBOOST_SERVICE_URL}/{user_id}/score"
    headers = {"Authorization": f"Bearer {settings.INTERNAL_SERVICE_TOKEN}"}
    params = {"technical_scope": technical_scope}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise ACSServiceError(f"ACS scoring service timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise ACSServiceError(
            f"ACS scoring service returned {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise ACSServiceError(f"Could not reach ACS scoring service: {exc}") from exc