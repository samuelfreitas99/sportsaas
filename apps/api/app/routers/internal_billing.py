from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.organization import Organization
from app.routers.billing import _generate_charges_core  # <-- IMPORT CERTO

router = APIRouter()


def _require_internal_key(x_internal_key: str | None):
    expected = getattr(settings, "INTERNAL_KEY", None)
    if not expected:
        raise HTTPException(status_code=500, detail="INTERNAL_KEY não configurado")
    if not x_internal_key or x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/internal/billing/run")
def run_billing(
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None),
):
    _require_internal_key(x_internal_key)

    org_ids = [row[0] for row in db.query(Organization.id).all()]

    results = []
    for org_id in org_ids:
        r = _generate_charges_core(
            db=db,
            org_id=org_id,
            force=False,
            cycle_key_override=None,
            created_by_id=None,
        )
        results.append({"org_id": str(org_id), **r})

    return {"orgs": len(org_ids), "results": results}
