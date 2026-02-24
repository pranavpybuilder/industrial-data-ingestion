# rule_engine/threshold_engine.py

"""
Threshold-Based Rules - Numeric comparisons against configured limits.

Implements:
- Single-threshold rules (out of range, missing data, outliers)
- Multi-threshold rules (temporal anomalies, consistency)
- Configurable thresholds from YAML
- Applied to profiled columns
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from rule_engine.rule_base import RuleBase, RuleResult, RuleEngine, Severity
from utils.logger import get_logger

logger = get_logger(__name__)


class ParameterOutOfRangeRule(RuleBase):
    """Trigger when numeric parameter exceeds configured bounds."""
    
    def __init__(self, column_name: str, min_val: float = None, max_val: float = None):
        super().__init__(
            name=f"ParameterOutOfRange({column_name})",
            rule_id=f"rule_out_of_range_{column_name}",
            severity="warning",
            default_confidence=0.90,
        )
        self.column_name = column_name
        self.min_val = min_val
        self.max_val = max_val
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check if column values exceed thresholds."""
        
        profile = data.get("profile", {})
        if self.column_name not in profile:
            return self._not_triggered_result(self, [])
        
        col_profile = profile[self.column_name]
        mean_val = col_profile.get("mean")
        max_observed = col_profile.get("max")
        min_observed = col_profile.get("min")
        
        violations = []
        triggered = False
        severity = "warning"
        
        if self.max_val is not None and max_observed > self.max_val:
            violations.append(f"Max observed {max_observed:.2f} exceeds limit {self.max_val}")
            triggered = True
            severity = "critical" if max_observed > self.max_val * 1.2 else "warning"
        
        if self.min_val is not None and min_observed < self.min_val:
            violations.append(f"Min observed {min_observed:.2f} below limit {self.min_val}")
            triggered = True
            severity = "warning"
        
        if triggered:
            message = f"{self.column_name}: " + "; ".join(violations)
            remediation = f"Check {self.column_name} readings. May indicate sensor drift or equipment malfunction."
            confidence = 0.95
        else:
            message = f"{self.column_name} within normal range (max: {max_observed:.2f}, min: {min_observed:.2f})"
            remediation = ""
            confidence = 0.85
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[self.column_name],
            data={
                "min_limit": self.min_val,
                "max_limit": self.max_val,
                "min_observed": min_observed,
                "max_observed": max_observed,
                "mean_observed": mean_val,
            },
            confidence=confidence,
            severity=severity,
        )


class MissingDataRule(RuleBase):
    """Trigger when column has excessive missing values."""
    
    def __init__(self, column_name: str, warning_threshold: float = 0.2, critical_threshold: float = 0.5):
        super().__init__(
            name=f"MissingData({column_name})",
            rule_id=f"rule_missing_{column_name}",
            severity="warning",
            default_confidence=0.85,
        )
        self.column_name = column_name
        self.warning_threshold = warning_threshold      # 20%
        self.critical_threshold = critical_threshold    # 50%
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for excessive missing values."""
        
        profile = data.get("profile", {})
        if self.column_name not in profile:
            return self._not_triggered_result(self, [])

        col_profile = profile[self.column_name]
        missing_pct_raw = col_profile.get(
            "missing_percentage",
            col_profile.get("null_percentage", 0),
        )
        missing_pct = missing_pct_raw / 100.0
        
        if missing_pct > self.critical_threshold:
            severity = "critical"
            message = f"{self.column_name}: {missing_pct:.1%} missing (critical: >{self.critical_threshold:.0%})"
            remediation = f"Investigate data source. {self.column_name} has severe data gaps."
            confidence = 0.95
            triggered = True
        elif missing_pct > self.warning_threshold:
            severity = "warning"
            message = f"{self.column_name}: {missing_pct:.1%} missing (warning: >{self.warning_threshold:.0%})"
            remediation = f"Check {self.column_name} data collection. Gaps detected."
            confidence = 0.90
            triggered = True
        else:
            message = f"{self.column_name}: Data complete ({missing_pct:.1%} missing)"
            remediation = ""
            severity = "info"
            confidence = 0.85
            triggered = False
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[self.column_name],
            data={
                "missing_percentage": missing_pct,
                "warning_threshold": self.warning_threshold,
                "critical_threshold": self.critical_threshold,
            },
            confidence=confidence,
            severity=severity,
        )


class OutlierDetectionRule(RuleBase):
    """Trigger when column has excessive outliers."""
    
    def __init__(self, column_name: str, outlier_warning_count: int = 3, outlier_critical_count: int = 5):
        super().__init__(
            name=f"OutlierDetection({column_name})",
            rule_id=f"rule_outliers_{column_name}",
            severity="warning",
            default_confidence=0.80,
        )
        self.column_name = column_name
        self.outlier_warning_count = outlier_warning_count
        self.outlier_critical_count = outlier_critical_count
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for outliers in column."""
        
        profile = data.get("profile", {})
        if self.column_name not in profile:
            return self._not_triggered_result(self, [])
        
        col_profile = profile[self.column_name]
        outlier_count = col_profile.get("outlier_count", 0)
        total_rows = data.get("total_rows", 100)
        outlier_pct = outlier_count / total_rows if total_rows > 0 else 0
        
        if outlier_count > self.outlier_critical_count:
            severity = "critical"
            message = f"{self.column_name}: {outlier_count} outliers detected ({outlier_pct:.1%})"
            remediation = f"Investigate {self.column_name} anomalies. May indicate sensor issues or process changes."
            confidence = 0.90
            triggered = True
        elif outlier_count > self.outlier_warning_count:
            severity = "warning"
            message = f"{self.column_name}: {outlier_count} outliers detected ({outlier_pct:.1%})"
            remediation = f"Monitor {self.column_name} for unusual values."
            confidence = 0.85
            triggered = True
        else:
            message = f"{self.column_name}: Normal outlier distribution ({outlier_count} detected)"
            remediation = ""
            severity = "info"
            confidence = 0.80
            triggered = False
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[self.column_name],
            data={
                "outlier_count": outlier_count,
                "outlier_percentage": outlier_pct,
                "warning_count": self.outlier_warning_count,
                "critical_count": self.outlier_critical_count,
            },
            confidence=confidence,
            severity=severity,
        )


class IncompleteDataRule(RuleBase):
    """Trigger when dataset has too few samples."""
    
    def __init__(self, min_rows: int = 10):
        super().__init__(
            name="IncompleteData",
            rule_id="rule_insufficient_data",
            severity="warning",
            default_confidence=0.75,
        )
        self.min_rows = min_rows
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check if dataset has minimum required samples."""
        
        total_rows = data.get("total_rows", 0)
        triggered = total_rows < self.min_rows
        
        if triggered:
            message = f"Dataset has only {total_rows} rows (need {self.min_rows} for analysis)"
            remediation = "Collect more data. Current dataset too small for reliable analysis."
            severity = "warning"
            confidence = 0.80
        else:
            message = f"Dataset size adequate ({total_rows} rows)"
            remediation = ""
            severity = "info"
            confidence = 0.70
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=[],
            data={"total_rows": total_rows, "min_required": self.min_rows},
            confidence=confidence,
            severity=severity,
        )


# Threshold Engine Orchestrator
class ThresholdEngine(RuleEngine):
    """Apply all threshold-based rules to profiled data."""
    
    def __init__(self):
        super().__init__(name="ThresholdEngine")
        self.logger = get_logger(__name__)
    
    def apply_to_profile(self, 
                        column_name: str,
                        profile: Dict[str, Any],
                        thresholds: Dict[str, Any],
                        total_rows: int) -> List[RuleResult]:
        """
        Apply threshold rules to a single column profile.
        
        Parameters
        ----------
        column_name : str
            Column being analyzed
        profile : dict
            Column profile from Module 2
        thresholds : dict
            Threshold configuration for this column
        total_rows : int
            Total rows in dataset
        
        Returns
        -------
        list of RuleResult
        """
        
        results = []
        data_context = {
            "profile": {column_name: profile},
            "total_rows": total_rows,
        }
        
        # Out of range check
        if "min" in thresholds or "max" in thresholds:
            rule = ParameterOutOfRangeRule(
                column_name=column_name,
                min_val=thresholds.get("min"),
                max_val=thresholds.get("max"),
            )
            results.append(rule.evaluate(data_context))
        
        # Missing data check
        missing_pct = profile.get("missing_percentage", 0) / 100.0
        if missing_pct > 0:
            rule = MissingDataRule(column_name)
            results.append(rule.evaluate(data_context))
        
        # Outlier check
        if profile.get("outlier_count", 0) > 0:
            rule = OutlierDetectionRule(column_name)
            results.append(rule.evaluate(data_context))
        
        return results
    
    def apply_to_all_profiles(self,
                             profiles: Dict[str, Any],
                             column_configs: Dict[str, Any],
                             total_rows: int) -> List[RuleResult]:
        """
        Apply threshold rules to all column profiles.
        
        Parameters
        ----------
        profiles : dict
            All column profiles from Module 2
        column_configs : dict
            Threshold config for each column (from thresholds.yaml)
        total_rows : int
            Total rows in dataset
        
        Returns
        -------
        list of RuleResult for all columns
        """
        
        all_results = []
        
        # Apply column-specific rules
        for column_name, profile in profiles.items():
            if column_name in column_configs:
                col_thresholds = column_configs[column_name]
                results = self.apply_to_profile(
                    column_name=column_name,
                    profile=profile,
                    thresholds=col_thresholds,
                    total_rows=total_rows,
                )
                all_results.extend(results)
        
        # Global data sufficiency check
        data_context = {"profile": {}, "total_rows": total_rows}
        insufficient_data_rule = IncompleteDataRule(min_rows=5)
        all_results.append(insufficient_data_rule.evaluate(data_context))
        
        return all_results
