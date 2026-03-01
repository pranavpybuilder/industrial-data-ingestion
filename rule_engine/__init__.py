# rule_engine/__init__.py

"""
Rule-Based Maintenance Engine - Module 3

Export main components for use in pipeline and IPC layer.
"""

from rule_engine.rule_base import (
    RuleBase,
    RuleResult,
    RuleEngine,
    Severity,
)

from rule_engine.threshold_engine import (
    ThresholdEngine,
    ParameterOutOfRangeRule,
    MissingDataRule,
    OutlierDetectionRule,
)

from rule_engine.maintenance_rules import (
    PMOverdueRule,
    FailurePatternRule,
    TemperatureUptrendRule,
    VibrationSpikeRule,
    EnergyAnomalyRule,
    RFIDConnectivityRule,
    RepeatFailureRule,
    HighMTTRRule,
    FailureEscalationRule,
)

from rule_engine.explainability import (
    RuleExplainer,
)

from rule_engine.energy_rules import (
    HighConsumptionDayRule,
    ConsumptionTrendRule,
    PeakDemandRule,
)

__all__ = [
    "RuleBase",
    "RuleResult",
    "RuleEngine",
    "Severity",
    "ThresholdEngine",
    "ParameterOutOfRangeRule",
    "MissingDataRule",
    "OutlierDetectionRule",
    "PMOverdueRule",
    "FailurePatternRule",
    "TemperatureUptrendRule",
    "VibrationSpikeRule",
    "EnergyAnomalyRule",
    "RFIDConnectivityRule",
    "RepeatFailureRule",
    "HighMTTRRule",
    "FailureEscalationRule",
    "RuleExplainer",
    "HighConsumptionDayRule",
    "ConsumptionTrendRule",
    "PeakDemandRule",
]
