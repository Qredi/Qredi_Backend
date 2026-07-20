"""
Router package — one FastAPI APIRouter per feature. Each router only wires
HTTP concerns (path, status code, auth dependency, request/response schema)
to a service call; no business logic lives here.

`all_routers` is provided so an app entrypoint can do:

    from fastapi import FastAPI
    from app.api.v1 import all_routers

    app = FastAPI()
    for r in all_routers:
        app.include_router(r)
"""

from app.api.v1.auth_router import router as auth_router
from app.api.v1.user_router import router as user_router
from app.api.v1.organization_router import router as organization_router
from app.api.v1.umkm_profile_router import router as umkm_profile_router
from app.api.v1.lender_profile_router import router as lender_profile_router
from app.api.v1.qris_transaction_router import router as qris_transaction_router
from app.api.v1.score_router import router as score_router
from app.api.v1.loan_outcome_router import router as loan_outcome_router
from app.api.v1.match_router import router as match_router
from app.api.v1.audit_log_router import router as audit_log_router

all_routers = [
    auth_router,
    user_router,
    organization_router,
    umkm_profile_router,
    lender_profile_router,
    qris_transaction_router,
    score_router,
    loan_outcome_router,
    match_router,
    audit_log_router,
]

__all__ = [
    "auth_router",
    "user_router",
    "organization_router",
    "umkm_profile_router",
    "lender_profile_router",
    "qris_transaction_router",
    "score_router",
    "loan_outcome_router",
    "match_router",
    "audit_log_router",
    "all_routers",
]