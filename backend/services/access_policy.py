"""
ArogyaMitra AI - Phase 4 Central ProfileAccessPolicy
Replaces scattered ownership checks with centralized Role-Based Access Control (RBAC).
Per PHASE4_IMPLEMENTATION.md F10.
"""

from typing import Optional, List
from backend.models.user import User
from backend.models.family_profile import FamilyProfile
from backend.models.phase4_models import CaregiverAccess
from backend.exceptions.arogya_errors import AccessPolicyDeniedError
from backend.core.logger import logger


class ProfileAccessPolicy:
    """
    Central authorization policy decider for profile-scoped health resources.
    
    Roles:
      - OWNER: Complete access to all resources, export, erasure, billing, and caregiver management.
      - CONTRIBUTOR: Caregiver with read & write capabilities (e.g. record upload, reminder management).
      - VIEWER: Caregiver with read-only access.
      - OUTSIDER: Zero access (denied with 404 to prevent enumeration).
    """

    OWNER_ONLY_ACTIONS = {
        "export",
        "erase",
        "billing",
        "manage_caregivers",
        "manage_guardian_consent",
        "delete_profile",
    }

    WRITE_ACTIONS = {
        "create_record",
        "update_record",
        "delete_record",
        "create_reminder",
        "update_reminder",
        "delete_reminder",
        "edit_parameters",
    }

    READ_ACTIONS = {
        "read_records",
        "read_parameters",
        "read_reminders",
        "read_timeline",
        "read_risk",
        "read_predictions",
        "ask_records",
    }

    @classmethod
    def can(
        cls,
        user: User,
        profile: FamilyProfile,
        action: str,
        caregiver_access: Optional[CaregiverAccess] = None,
    ) -> bool:
        """
        Determines if the given user is authorized to perform action on profile.
        """
        if not user or not profile:
            return False

        # 1. Owner has unrestricted access across all actions
        if profile.owner_user_id == user.user_id:
            return True

        # 2. Owner-only actions strictly reject non-owners
        if action in cls.OWNER_ONLY_ACTIONS:
            return False

        # 3. Caregiver checks
        if caregiver_access:
            # Must be active, accepted, and unrevoked
            if caregiver_access.revoked_at is not None:
                return False
            if caregiver_access.accepted_at is None:
                return False
            if caregiver_access.caregiver_user_id != user.user_id:
                return False
            if caregiver_access.patient_profile_id != profile.profile_id:
                return False

            role = (caregiver_access.role or "VIEWER").upper()

            # CONTRIBUTOR can perform READ and WRITE actions
            if role == "CONTRIBUTOR":
                return action in cls.READ_ACTIONS or action in cls.WRITE_ACTIONS

            # VIEWER can only perform READ actions
            if role == "VIEWER":
                return action in cls.READ_ACTIONS

        return False

    @classmethod
    def authorize(
        cls,
        user: User,
        profile: FamilyProfile,
        action: str,
        caregiver_access: Optional[CaregiverAccess] = None,
    ):
        """
        Enforces authorization policy. Raises AccessPolicyDeniedError (404) on failure.
        """
        allowed = cls.can(user, profile, action, caregiver_access)
        if not allowed:
            logger.warning(
                f"[ProfileAccessPolicy] Denied: user={getattr(user, 'user_id', None)} "
                f"profile={getattr(profile, 'profile_id', None)} action={action}"
            )
            # Raise 404 to avoid leaking resource existence to unauthorized users
            raise AccessPolicyDeniedError()
