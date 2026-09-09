"""
Unit tests for Coding Model Quantization removal and Model Load/Unload RBAC Access.
"""

import pytest
import yaml
from pathlib import Path
from backend.router.model_registry import DEFAULT_MODELS
from backend.models.registry import get_model, _MODELS_DB
from backend.security.rbac import rbac_enforcer
from backend.security.policy import action_firewall, ActionDecision


def test_coding_model_quantization_configs():
    """Verify coding model quantization is configured as 4-bit in yaml config."""
    config_path = Path("configs/models.yaml")
    assert config_path.exists(), "configs/models.yaml must exist"
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    coding_cfg = data["models"]["coding"]
    assert coding_cfg["quantization"] == "4-bit", "Coding model quantization must be '4-bit'"


def test_coding_model_quantization_in_registries():
    """Verify coding model has quantization='4-bit' in both router and model database registries."""
    # Router registry
    router_coding = DEFAULT_MODELS["coding"]
    assert router_coding.quantization == "4-bit", f"Expected '4-bit', got {router_coding.quantization}"

    # Models DB registry
    db_coding = get_model("coding-local")
    assert db_coding is not None
    assert db_coding.quantization == "4-bit", f"Expected '4-bit', got {db_coding.quantization}"


def test_get_model_flexible_resolution():
    """Verify get_model resolves by id, role, name, and loose alias."""
    assert get_model("coding-local") is not None
    assert get_model("coding") is not None
    assert get_model("qwen2.5-coder:7b") is not None
    assert get_model("reasoning-local") is not None
    assert get_model("reasoning") is not None
    assert get_model("vision-local") is not None
    assert get_model("vision") is not None


def test_rbac_model_management_access():
    """Verify admin and engineering have model management permissions, while finance is blocked."""
    # Admin has all permissions
    assert rbac_enforcer.can_manage_models("admin") is True
    assert rbac_enforcer.has_permission("admin", "model.load") is True
    assert rbac_enforcer.has_permission("admin", "model.unload") is True

    # Engineering has model management access
    assert rbac_enforcer.can_manage_models("engineering") is True
    assert rbac_enforcer.has_permission("engineering", "model.load") is True
    assert rbac_enforcer.has_permission("engineering", "model.unload") is True
    assert rbac_enforcer.has_permission("engineering", "model.manage") is True

    # Finance does NOT have model management access
    assert rbac_enforcer.can_manage_models("finance") is False
    assert rbac_enforcer.has_permission("finance", "model.load") is False
    assert rbac_enforcer.has_permission("finance", "model.unload") is False

    # HR does NOT have model management access
    assert rbac_enforcer.can_manage_models("hr") is False


def test_firewall_allows_model_actions():
    """Verify security firewall policy allows model.load and model.unload."""
    load_rule = action_firewall.check("model.load", user_role="engineering")
    assert load_rule.decision == ActionDecision.ALLOWED

    unload_rule = action_firewall.check("model.unload", user_role="engineering")
    assert unload_rule.decision == ActionDecision.ALLOWED
