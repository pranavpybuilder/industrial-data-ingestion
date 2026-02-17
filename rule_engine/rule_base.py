# rule_engine/rule_base.py

"""
Base Rule Classes - Foundation for all maintenance rules.

Provides:
- Abstract RuleBase for implementing specific rules
- RuleResult dataclass for standardized outputs
- Severity enum for consistent severity classification
- Common interfaces and patterns
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from utils.logger import get_logger

logger = get_logger(__name__)


class Severity(Enum):
    """Rule finding severity levels."""
    CRITICAL = "critical"      # Immediate action required
    WARNING = "warning"        # Should investigate soon  
    INFO = "info"              # For awareness


@dataclass
class RuleResult:
    """Standardized result from a rule evaluation."""
    
    rule_name: str              # Name of the rule (e.g., "TemperatureOutOfRange")
    rule_id: str                # Unique rule ID
    triggered: bool             # Whether rule condition was met
    severity: str               # "critical", "warning", or "info"
    confidence: float           # 0-1, how confident is this finding
    message: str                # Human-readable message
    remediation: str            # Suggested action
    affected_columns: List[str] # Which columns triggered this rule
    data: Dict[str, Any]        # Raw data that triggered rule (for debugging)
    
    def __str__(self) -> str:
        if self.triggered:
            return f"[{self.severity.upper()}] {self.rule_name}: {self.message}"
        return f"[OK] {self.rule_name}: No issues detected"


class RuleBase(ABC):
    """Abstract base class for all rules."""
    
    def __init__(
        self,
        name: str,
        rule_id: str,
        severity: str = "warning",
        default_confidence: float = 0.85,
    ):
        """
        Initialize rule.
        
        Parameters
        ----------
        name : str
            Human-readable rule name
        rule_id : str
            Unique identifier (e.g., "rule_temp_out_of_range")
        severity : str
            Default severity if triggered: "critical", "warning", "info"
        default_confidence : float
            Default confidence score (0-1) if no custom calculation
        """
        self.name = name
        self.rule_id = rule_id
        self.severity = severity
        self.default_confidence = default_confidence
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """
        Evaluate rule against input data.
        
        Parameters
        ----------
        data : dict
            Input data with profiling info, features, thresholds, etc.
        
        Returns
        -------
        RuleResult with triggered status and details
        """
        pass
    
    def explain(self, result: RuleResult) -> str:
        """
        Generate human-readable explanation for rule result.
        
        Parameters
        ----------
        result : RuleResult
            The result to explain
        
        Returns
        -------
        str: Detailed explanation message
        """
        if result.triggered:
            return f"{result.message} (confidence: {result.confidence:.0%})"
        return f"✓ {self.name}: All checks passed"
    
    def _create_result(
        self,
        triggered: bool,
        message: str,
        remediation: str,
        affected_columns: List[str],
        data: Dict[str, Any],
        confidence: Optional[float] = None,
        severity: Optional[str] = None,
    ) -> RuleResult:
        """
        Helper to create consistent RuleResult objects.
        
        Parameters
        ----------
        triggered : bool
            Whether rule condition was met
        message : str
            Description of finding
        remediation : str
            Suggested action
        affected_columns : list
            Columns involved
        data : dict
            Raw triggering data
        confidence : float, optional
            Override default confidence
        severity : str, optional
            Override default severity
        
        Returns
        -------
        RuleResult
        """
        return RuleResult(
            rule_name=self.name,
            rule_id=self.rule_id,
            triggered=triggered,
            severity=severity or self.severity,
            confidence=confidence if confidence is not None else self.default_confidence,
            message=message,
            remediation=remediation,
            affected_columns=affected_columns,
            data=data,
        )
    
    @staticmethod
    def _not_triggered_result(rule: 'RuleBase', affected_cols: List[str]) -> RuleResult:
        """Create a 'not triggered' result."""
        return rule._create_result(
            triggered=False,
            message="No anomalies detected",
            remediation="No action required",
            affected_columns=affected_cols,
            data={},
        )


class RuleEngine:
    """Orchestrates multiple rules."""
    
    def __init__(self, name: str = "RuleEngine"):
        """Initialize rule engine."""
        self.name = name
        self.rules: Dict[str, RuleBase] = {}
        self.logger = get_logger(__name__)
    
    def register_rule(self, rule: RuleBase) -> None:
        """Register a rule with the engine."""
        self.rules[rule.rule_id] = rule
        self.logger.debug(f"Registered rule: {rule.name}")
    
    def evaluate_all(self, data: Dict[str, Any]) -> List[RuleResult]:
        """
        Evaluate all registered rules against input data.
        
        Parameters
        ----------
        data : dict
            Input data for rules
        
        Returns
        -------
        list of RuleResult, one per rule
        """
        results = []
        for rule_id, rule in self.rules.items():
            try:
                result = rule.evaluate(data)
                results.append(result)
                if result.triggered:
                    self.logger.info(f"Rule triggered: {rule.name}")
            except Exception as exc:
                self.logger.error(f"Rule evaluation failed ({rule.name}): {exc}")
        
        return results
    
    def get_triggered_rules(self, results: List[RuleResult]) -> List[RuleResult]:
        """Filter to only triggered rules."""
        return [r for r in results if r.triggered]
    
    def get_critical_findings(self, results: List[RuleResult]) -> List[RuleResult]:
        """Filter to only critical severity findings."""
        return [r for r in results if r.severity == "critical" and r.triggered]
