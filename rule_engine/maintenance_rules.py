# rule_engine/maintenance_rules.py

"""
Domain-Specific Maintenance Rules - Industrial operations heuristics.

Implements:
- PM (Preventive Maintenance) order scheduling rules
- Failure pattern detection
- Degradation trend analysis
- Energy efficiency monitoring
- Equipment connectivity checks
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from rule_engine.rule_base import RuleBase, RuleResult
from utils.logger import get_logger

logger = get_logger(__name__)


class PMOverdueRule(RuleBase):
    """Trigger when Preventive Maintenance orders are overdue."""
    
    def __init__(self, pm_config: Dict[str, int] = None):
        super().__init__(
            name="PMOrderOverdue",
            rule_id="rule_pm_overdue",
            severity="warning",
            default_confidence=0.90,
        )
        self.pm_config = pm_config or {
            "alert_before_due_days": 14,
            "overdue_after_days": 0,
            "critical_after_days": 60,
        }
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check PM order due dates."""
        
        features = data.get("features", [])
        sap_pm_orders = [f for f in features if "sap__pm_order_due_date" in str(f)]
        
        if not sap_pm_orders:
            return self._not_triggered_result(self, [])
        
        today = datetime.now().date()
        overdue_orders = []
        upcoming_orders = []
        critical_orders = []
        
        for order in sap_pm_orders:
            try:
                if isinstance(order, dict):
                    due_date_str = order.get("feature_value")
                else:
                    due_date_str = str(order)
                
                # Parse date (handle various formats)
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]:
                    try:
                        due_date = datetime.strptime(due_date_str.split()[0], "%Y-%m-%d").date()
                        break
                    except (ValueError, IndexError):
                        continue
                else:
                    continue
                
                days_overdue = (today - due_date).days
                
                if days_overdue > self.pm_config["critical_after_days"]:
                    critical_orders.append({
                        "due_date": due_date,
                        "days_overdue": days_overdue,
                    })
                elif days_overdue > 0:
                    overdue_orders.append({
                        "due_date": due_date,
                        "days_overdue": days_overdue,
                    })
                elif days_overdue > -self.pm_config["alert_before_due_days"]:
                    upcoming_orders.append({
                        "due_date": due_date,
                        "days_until_due": -days_overdue,
                    })
            
            except Exception as exc:
                logger.debug(f"Error parsing PM order: {exc}")
                continue
        
        # Determine if rule triggered
        triggered = bool(critical_orders or overdue_orders)
        severity = "critical" if critical_orders else "warning"
        
        if critical_orders:
            message = f"{len(critical_orders)} PM order(s) critically overdue (>{self.pm_config['critical_after_days']} days)"
            remediation = "Schedule PM immediately. Equipment maintenance severely overdue."
            confidence = 0.98
        elif overdue_orders:
            message = f"{len(overdue_orders)} PM order(s) overdue ({overdue_orders[0]['days_overdue']} days)"
            remediation = "Schedule PM orders. Equipment due for maintenance."
            confidence = 0.95
        else:
            message = f"PM scheduling current. Upcoming: {len(upcoming_orders)} orders"
            remediation = ""
            confidence = 0.90
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["pm_order_due_date"],
            data={
                "overdue_count": len(overdue_orders),
                "critical_count": len(critical_orders),
                "upcoming_count": len(upcoming_orders),
            },
            confidence=confidence,
            severity=severity,
        )


class FailurePatternRule(RuleBase):
    """Trigger when repeated failures detected (failure pattern)."""
    
    def __init__(self, pattern_config: Dict[str, Any] = None):
        super().__init__(
            name="RepeatedFailurePattern",
            rule_id="rule_failure_pattern",
            severity="warning",
            default_confidence=0.85,
        )
        self.pattern_config = pattern_config or {
            "min_failures": 3,
            "lookback_days": 90,
        }
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for repeated failure patterns."""
        
        features = data.get("features", [])
        failure_records = [f for f in features if "sap__failure" in str(f) or "breakdown" in str(f).lower()]
        
        if len(failure_records) < self.pattern_config["min_failures"]:
            return self._not_triggered_result(self, [])
        
        triggered = len(failure_records) >= self.pattern_config["min_failures"]
        
        if triggered:
            message = f"Repeated failures: {len(failure_records)} breakdowns detected"
            remediation = "Investigate root cause. Equipment showing chronic failure pattern."
            severity = "critical" if len(failure_records) >= 5 else "warning"
            confidence = min(0.95, 0.70 + len(failure_records) * 0.05)
        else:
            message = "No abnormal failure pattern detected"
            remediation = ""
            severity = "info"
            confidence = 0.80
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["failure_events"],
            data={
                "failure_count": len(failure_records),
                "min_threshold": self.pattern_config["min_failures"],
            },
            confidence=confidence,
            severity=severity,
        )


class TemperatureUptrendRule(RuleBase):
    """Trigger when temperature shows upward trend (equipment degradation)."""
    
    def __init__(self):
        super().__init__(
            name="TemperatureUptrend",
            rule_id="rule_temp_degradation",
            severity="warning",
            default_confidence=0.80,
        )
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for temperature increase trend."""
        
        profile = data.get("profile", {})
        temp_profile = profile.get("temperature", {})
        
        if not temp_profile:
            return self._not_triggered_result(self, [])
        
        mean_temp = temp_profile.get("mean", 0)
        max_temp = temp_profile.get("max", 0)
        median_temp = temp_profile.get("median", 0)
        
        # Simple trend: if mean is significantly close to max, temperature rising
        spread = max_temp - mean_temp
        uptrend_indicator = spread < (max_temp - median_temp) * 0.5
        
        if uptrend_indicator and mean_temp > 60:  # Only alert if above 60C baseline
            triggered = True
            message = f"Temperature trend: {mean_temp:.1f}C average (approaching max {max_temp:.1f}C)"
            remediation = "Monitor temperature closely. Equipment may be degrading."
            severity = "warning"
            confidence = 0.78
        else:
            triggered = False
            message = f"Temperature stable: {mean_temp:.1f}C average"
            remediation = ""
            severity = "info"
            confidence = 0.75
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["temperature"],
            data={
                "mean_temperature": mean_temp,
                "max_temperature": max_temp,
                "trend_indicator": uptrend_indicator,
            },
            confidence=confidence,
            severity=severity,
        )


class VibrationSpikeRule(RuleBase):
    """Trigger when vibration exceeds bearing wear threshold."""
    
    def __init__(self, spike_threshold: float = 7.0):
        super().__init__(
            name="VibrationSpike",
            rule_id="rule_vibration_spike",
            severity="critical",
            default_confidence=0.92,
        )
        self.spike_threshold = spike_threshold
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for excessive vibration."""
        
        profile = data.get("profile", {})
        vib_profile = profile.get("vibration", {})
        
        if not vib_profile:
            vib_profile = profile.get("acceleration", {})
        
        if not vib_profile:
            return self._not_triggered_result(self, [])
        
        max_vibration = vib_profile.get("max", 0)
        mean_vibration = vib_profile.get("mean", 0)
        
        triggered = max_vibration > self.spike_threshold
        
        if triggered:
            message = f"High vibration detected: {max_vibration:.2f} mm/s (limit: {self.spike_threshold})"
            remediation = "URGENT: Check bearing condition. High vibration indicates wear. Reduce load or stop equipment."
            severity = "critical"
            confidence = 0.95
        else:
            message = f"Vibration normal: {mean_vibration:.2f} mm/s average"
            remediation = ""
            severity = "info"
            confidence = 0.85
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["vibration"],
            data={
                "max_vibration": max_vibration,
                "mean_vibration": mean_vibration,
                "threshold": self.spike_threshold,
            },
            confidence=confidence,
            severity=severity,
        )


class EnergyAnomalyRule(RuleBase):
    """Trigger when energy consumption exceeds baseline (efficiency drop)."""
    
    def __init__(self, efficiency_threshold: float = 0.15):
        super().__init__(
            name="EnergyAnomaly",
            rule_id="rule_energy_anomaly",
            severity="warning",
            default_confidence=0.80,
        )
        self.efficiency_threshold = efficiency_threshold  # 15% above baseline
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for energy efficiency drops."""
        
        features = data.get("features", [])
        energy_records = [f for f in features if "energy" in str(f).lower() or "power" in str(f).lower()]
        
        if not energy_records:
            return self._not_triggered_result(self, [])
        
        # Look for efficiency deviation
        baseline = data.get("baseline_energy", 0)
        current = data.get("current_energy", 0)
        
        if baseline > 0:
            efficiency_drop = (current - baseline) / baseline
            triggered = efficiency_drop > self.efficiency_threshold
        else:
            triggered = False
            efficiency_drop = 0
        
        if triggered:
            message = f"Energy consumption up {efficiency_drop:.1%} above baseline (threshold: {self.efficiency_threshold:.0%})"
            remediation = "Check equipment for degradation. Energy efficiency has decreased."
            severity = "warning"
            confidence = 0.85
        else:
            message = "Energy consumption within normal range"
            remediation = ""
            severity = "info"
            confidence = 0.75
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["energy_consumption"],
            data={
                "baseline": baseline,
                "current": current,
                "efficiency_drop": efficiency_drop,
                "threshold": self.efficiency_threshold,
            },
            confidence=confidence,
            severity=severity,
        )


class RFIDConnectivityRule(RuleBase):
    """Trigger when RFID scanner shows data gaps."""
    
    def __init__(self, gap_hours: int = 24):
        super().__init__(
            name="RFIDDataGap",
            rule_id="rule_rfid_gap",
            severity="warning",
            default_confidence=0.85,
        )
        self.gap_hours = gap_hours
    
    def evaluate(self, data: Dict[str, Any]) -> RuleResult:
        """Check for RFID scan gaps."""
        
        features = data.get("features", [])
        rfid_scans = [f for f in features if "rfid" in str(f).lower()]
        
        if not rfid_scans:
            return self._not_triggered_result(self, [])
        
        # Check if recent scans exist
        scan_gap_detected = len(rfid_scans) < 5 or data.get("last_scan_hours_ago", 0) > self.gap_hours
        
        if scan_gap_detected:
            message = f"RFID: No scans for >{self.gap_hours} hours"
            remediation = "Check RFID scanner. Connectivity or equipment issue."
            triggered = True
            severity = "warning"
            confidence = 0.88
        else:
            message = "RFID scanner operating normally"
            remediation = ""
            triggered = False
            severity = "info"
            confidence = 0.85
        
        return self._create_result(
            triggered=triggered,
            message=message,
            remediation=remediation,
            affected_columns=["rfid_scans"],
            data={
                "scan_count": len(rfid_scans),
                "gap_threshold_hours": self.gap_hours,
            },
            confidence=confidence,
            severity=severity,
        )
