"""
ArogyaMitra AI - Drug Interaction Router (Phase 2)
Endpoints for drug-drug interaction checking (single pair + batch/polypharmacy).
Per FEATURES_PHASE2.md §2.4.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.core.dependencies import get_current_user
from backend.services.drug_interaction_service import DrugInteractionService

router = APIRouter(prefix="/api/drugs", tags=["Drug Interactions"])


# ── Request / Response Schemas ────────────────────────────────

class DrugPairRequest(BaseModel):
    drug_a: str = Field(..., min_length=2, description="First drug name")
    drug_b: str = Field(..., min_length=2, description="Second drug name")


class DrugListRequest(BaseModel):
    drugs: List[str] = Field(..., min_items=2, max_items=20, description="List of drug names (2-20)")


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    resolved_a: str
    resolved_b: str
    interaction_found: bool
    severity: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    source: str


class BatchInteractionResponse(BaseModel):
    total_pairs: int
    interactions_found: int
    high_risk_count: int
    results: List[InteractionResult]


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/check", response_model=InteractionResult)
async def check_drug_interaction(
    body: DrugPairRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Check for known interactions between two drugs.
    Uses local CSV database with fuzzy name matching + curated built-in list.
    """
    result = DrugInteractionService.check_interaction(
        drug_a=body.drug_a,
        drug_b=body.drug_b,
    )
    return result


@router.post("/check/batch", response_model=BatchInteractionResponse)
async def check_batch_drug_interactions(
    body: DrugListRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Polypharmacy safety check: evaluate all pairwise interactions for a drug list.
    Returns summary stats and individual pair results.
    """
    results = DrugInteractionService.batch_check(drug_list=body.drugs)

    interactions_found = sum(1 for r in results if r["interaction_found"])
    high_risk = sum(
        1 for r in results
        if r.get("severity") in ("severe", "contraindicated")
    )

    return BatchInteractionResponse(
        total_pairs=len(results),
        interactions_found=interactions_found,
        high_risk_count=high_risk,
        results=results,
    )
