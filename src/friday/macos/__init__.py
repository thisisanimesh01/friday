"""macOS control and permission framework package."""

from macos.registry import (
    ActionDefinition,
    ActionRegistry,
    ActionResult,
    RiskTier,
    default_registry,
    record_audit_log,
)
from macos.router import format_action_result, route_macos_intent

__all__ = [
    "ActionDefinition",
    "ActionRegistry",
    "ActionResult",
    "RiskTier",
    "default_registry",
    "format_action_result",
    "record_audit_log",
    "route_macos_intent",
]
