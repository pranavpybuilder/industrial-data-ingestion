════════════════════════════════════════════════════════════════════════════════
MODULE 5 (ORCHESTRATION) - DETAILED IMPLEMENTATION GUIDE
════════════════════════════════════════════════════════════════════════════════

This is your starting point. Follow this guide to implement the Orchestration layer.

════════════════════════════════════════════════════════════════════════════════
HIGH-LEVEL ARCHITECTURE
════════════════════════════════════════════════════════════════════════════════

Process Flow:
  Module 3: Rules Engine generates findings
    ├─ 10 rules executed
    ├─ Each rule produces RuleResult objects
    └─ Returns: List[RuleResult]
  
  ↓ (pass to Module 5)
  
  Module 5: Orchestration
    ├─ Read rule findings from Module 3
    ├─ Read ML findings from Module 4 (optional, None if skipped)
    ├─ Merge, deduplicate, prioritize
    ├─ Calculate severity scores
    ├─ Create Insight objects
    └─ Persist to insights table
  
  ↓ (output)
  
  insights table (database)
    └─ Ready for Module 6 (Dashboard) and Frontend (Insights page)

Data Structures (what you'll work with):

  INPUT - RuleResult (from Module 3):
    ├─ rule_name: str (e.g., "TemperatureUptrend")
    ├─ severity: str ("CRITICAL", "WARNING", "INFO")
    ├─ confidence: float (0.0-1.0)
    ├─ message: str
    ├─ remediation: str
    ├─ affected_columns: List[str]
    └─ rule_details: dict (rule-specific data)

  INPUT - MLFinding (from Module 4 - optional):
    ├─ type: str ("ANOMALY", "PATTERN", "FORECAST")
    ├─ severity: str
    ├─ confidence: float
    ├─ feature_name: str
    ├─ metric: float (anomaly_score, pattern_score, etc)
    └─ description: str

  OUTPUT - Insight (to database):
    ├─ insight_id: str (UUID)
    ├─ run_id: str (foreign key)
    ├─ type: str ("RULE" | "ML" | "HEALTH")
    ├─ severity: str ("CRITICAL" | "WARNING" | "INFO")
    ├─ confidence: float (0.0-1.0)
    ├─ title: str (short, user-facing)
    ├─ description: str (longer explanation)
    ├─ data: dict (JSON with rule-specific data)
    ├─ source_module: int (3 or 4)
    └─ created_at: datetime

════════════════════════════════════════════════════════════════════════════════
FILE 1: orchestration/insight_orchestrator.py
════════════════════════════════════════════════════════════════════════════════

PURPOSE: Main orchestrator. Merges findings and creates insights.

STRUCTURE:

  from dataclasses import dataclass, field
  from datetime import datetime
  from typing import List, Dict, Optional
  import uuid
  from enum import Enum
  
  # ─────────────────────────────────────────────────────────────────────────
  class InsightType(Enum):
      RULE = "RULE"
      ML = "ML"
      HEALTH = "HEALTH"
  
  
  class SeverityLevel(Enum):
      CRITICAL = "CRITICAL"
      WARNING = "WARNING"
      INFO = "INFO"
  
  
  @dataclass
  class Insight:
      """Unified insight structure (output to database)"""
      insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
      run_id: str = ""
      type: InsightType = InsightType.RULE
      severity: SeverityLevel = SeverityLevel.INFO
      confidence: float = 0.0
      title: str = ""
      description: str = ""
      data: dict = field(default_factory=dict)
      source_module: int = 3  # Module 3 (rules) or 4 (ML)
      created_at: datetime = field(default_factory=datetime.utcnow)
      
      def to_dict(self):
          """Convert to database-ready dict"""
          return {
              "insight_id": self.insight_id,
              "run_id": self.run_id,
              "type": self.type.value,
              "severity": self.severity.value,
              "confidence": self.confidence,
              "title": self.title,
              "description": self.description,
              "data": self.data,
              "source_module": self.source_module,
              "created_at": self.created_at.isoformat()
          }
  
  
  class InsightOrchestrator:
      """Merges rule + ML findings into unified insights"""
      
      def __init__(self, logger=None):
          self.logger = logger or create_logger(__name__)
      
      def orchestrate(self, run_id: str, rule_findings: List[dict], 
                     ml_findings: Optional[List[dict]] = None) -> List[Insight]:
          """
          Main method: Merge all findings into unified insights
          
          Args:
              run_id: The run we're processing
              rule_findings: Output from Module 3 (rules)
              ml_findings: Output from Module 4 (ML) - can be None
          
          Returns:
              List of Insight objects ready to persist
          """
          
          insights = []
          
          # Step 1: Convert rule findings to insights
          rule_insights = self._convert_rule_findings(run_id, rule_findings)
          insights.extend(rule_insights)
          self.logger.info(f"Created {len(rule_insights)} insights from rules")
          
          # Step 2: Convert ML findings to insights (if present)
          if ml_findings:
              ml_insights = self._convert_ml_findings(run_id, ml_findings)
              insights.extend(ml_insights)
              self.logger.info(f"Created {len(ml_insights)} insights from ML")
          
          # Step 3: Deduplicate similar insights
          insights = self._deduplicate_insights(insights)
          self.logger.info(f"After deduplication: {len(insights)} insights")
          
          # Step 4: Prioritize (sort by severity)
          insights = self._prioritize_insights(insights)
          
          return insights
      
      
      def _convert_rule_findings(self, run_id: str, rule_findings: List[dict]) -> List[Insight]:
          """Convert Module 3 rule findings to Insight objects"""
          
          insights = []
          
          for finding in rule_findings:
              insight = Insight(
                  run_id=run_id,
                  type=InsightType.RULE,
                  severity=SeverityLevel[finding["severity"]],  # CRITICAL/WARNING/INFO
                  confidence=finding.get("confidence", 0.8),
                  title=self._generate_title(finding),
                  description=finding.get("message", ""),
                  data=self._extract_rule_data(finding),
                  source_module=3
              )
              insights.append(insight)
          
          return insights
      
      
      def _convert_ml_findings(self, run_id: str, ml_findings: List[dict]) -> List[Insight]:
          """Convert Module 4 ML findings to Insight objects"""
          
          insights = []
          
          for finding in ml_findings:
              insight = Insight(
                  run_id=run_id,
                  type=InsightType.ML,
                  severity=SeverityLevel[finding["severity"]],
                  confidence=finding.get("confidence", 0.7),
                  title=f"ML: {finding.get('type', 'Anomaly')} in {finding.get('feature_name', 'Unknown')}",
                  description=finding.get("description", ""),
                  data=self._extract_ml_data(finding),
                  source_module=4
              )
              insights.append(insight)
          
          return insights
      
      
      def _deduplicate_insights(self, insights: List[Insight]) -> List[Insight]:
          """Remove duplicate or overlapping insights"""
          
          # Simple approach: if same title + run_id, keep only highest severity
          seen = {}  # key: (run_id, title) → value: insight
          
          for insight in insights:
              key = (insight.run_id, insight.title)
              
              if key not in seen:
                  seen[key] = insight
              else:
                  # Keep the one with higher severity
                  existing = seen[key]
                  severity_rank = {"CRITICAL": 3, "WARNING": 2, "INFO": 1}
                  
                  if severity_rank[insight.severity.value] > severity_rank[existing.severity.value]:
                      seen[key] = insight
          
          return list(seen.values())
      
      
      def _prioritize_insights(self, insights: List[Insight]) -> List[Insight]:
          """Sort insights by priority (severity first, then confidence)"""
          
          severity_rank = {"CRITICAL": 3, "WARNING": 2, "INFO": 1}
          
          return sorted(
              insights,
              key=lambda x: (-severity_rank[x.severity.value], -x.confidence),
              reverse=False
          )
      
      
      def _generate_title(self, finding: dict) -> str:
          """Create user-friendly insight title"""
          
          rule_name = finding.get("rule_name", "Unknown")
          
          # Transform rule names to readable titles
          title_map = {
              "PMOverdue": "Maintenance Due",
              "TemperatureUptrend": "Temperature Rising",
              "VibrationSpike": "Abnormal Vibration Detected",
              "FailurePattern": "Repeated Failures Detected",
              "EnergyAnomaly": "Energy Consumption Anomaly",
              "RFIDConnectivity": "RFID Reader Connection Issue",
              "ParameterOutOfRange": "Parameter Out of Acceptable Range",
              "MissingData": "Missing Data Detected",
              "OutlierDetection": "Outlier Values Found",
              "IncompleteData": "Incomplete Data Set"
          }
          
          return title_map.get(rule_name, f"{rule_name} Rule Triggered")
      
      
      def _extract_rule_data(self, finding: dict) -> dict:
          """Extract rule-specific data for storage"""
          
          return {
              "rule_name": finding.get("rule_name"),
              "affected_columns": finding.get("affected_columns", []),
              "remediation": finding.get("remediation", ""),
              "details": finding.get("rule_details", {})
          }
      
      
      def _extract_ml_data(self, finding: dict) -> dict:
          """Extract ML-specific data for storage"""
          
          return {
              "ml_type": finding.get("type"),
              "feature": finding.get("feature_name"),
              "metric": finding.get("metric", 0.0),
              "baseline": finding.get("baseline"),
              "current": finding.get("current")
          }
  
  
  # ─────────────────────────────────────────────────────────────────────────
  # USAGE IN pipeline_runner.py
  # ─────────────────────────────────────────────────────────────────────────
  
  # After Step 6 (Rules), add:
  
  """
  # Step 7: Orchestration (Module 5)
  orchestrator = InsightOrchestrator(logger)
  ml_findings = None  # Set to actual findings if Module 4 is implemented
  insights = orchestrator.orchestrate(run_id, rule_findings, ml_findings)
  
  # Step 8: Persist insights to database
  insight_repo.bulk_insert(insights)
  logger.info(f"Created and persisted {len(insights)} insights")
  """

════════════════════════════════════════════════════════════════════════════════
FILE 2: orchestration/prioritization.py
════════════════════════════════════════════════════════════════════════════════

PURPOSE: Rank and prioritize insights for display

STRUCTURE:

  from typing import List
  from dataclasses import dataclass
  
  @dataclass
  class PrioritizedInsight:
      """Insight with priority score for ranking"""
      insight_id: str
      title: str
      severity: str
      confidence: float
      priority_score: float
      rank: int
  
  
  class InsightPrioritizer:
      """Rank insights by importance"""
      
      def __init__(self, logger=None):
          self.logger = logger or create_logger(__name__)
          self.max_display_insights = 20  # Show top 20
      
      def prioritize(self, insights: List[dict]) -> List[PrioritizedInsight]:
          """
          Rank insights for display
          
          Factors:
            1. Severity (CRITICAL > WARNING > INFO)
            2. Confidence (higher = more likely true)
            3. Freshness (newer = higher priority)
            4. Impact (affecting more columns = more important)
          """
          
          prioritized = []
          
          for insight in insights:
              priority_score = self._calculate_priority_score(insight)
              prioritized.append(PrioritizedInsight(
                  insight_id=insight["insight_id"],
                  title=insight["title"],
                  severity=insight["severity"],
                  confidence=insight["confidence"],
                  priority_score=priority_score,
                  rank=0  # Will be set after sorting
              ))
          
          # Sort by priority_score descending
          prioritized = sorted(prioritized, key=lambda x: x.priority_score, reverse=True)
          
          # Assign ranks
          for i, insight in enumerate(prioritized, 1):
              insight.rank = i
          
          # Return top N
          return prioritized[:self.max_display_insights]
      
      
      def _calculate_priority_score(self, insight: dict) -> float:
          """
          Calculate priority score (0.0 to 100.0)
          
          Weighted formula:
            score = (severity_weight * 50) + (confidence_weight * 30) + (impact_weight * 20)
          """
          
          severity_weight = {
              "CRITICAL": 1.0,
              "WARNING": 0.6,
              "INFO": 0.2
          }[insight["severity"]]
          
          confidence = insight.get("confidence", 0.5)
          
          impact_weight = len(insight.get("data", {}).get("affected_columns", []))
          impact_weight = min(impact_weight / 5, 1.0)  # Normalize to 0-1
          
          score = (
              severity_weight * 50 +
              confidence * 30 +
              impact_weight * 20
          )
          
          return score

════════════════════════════════════════════════════════════════════════════════
FILE 3: orchestration/severity_scoring.py
════════════════════════════════════════════════════════════════════════════════

PURPOSE: Calculate final severity for insights (can be complex, multi-factor)

STRUCTURE:

  from enum import Enum
  
  class SeverityAssessment:
      """Multi-factor severity assessment"""
      
      def __init__(self, logger=None):
          self.logger = logger or create_logger(__name__)
      
      def assess_severity(self, rule_name: str, finding: dict, context: dict) -> str:
          """
          Determine final severity based on rule + context
          
          Args:
              rule_name: Name of the rule (e.g., "TemperatureUptrend")
              finding: The finding data
              context: Contextual data (profiling stats, trends, etc)
          
          Returns:
              Severity level: "CRITICAL", "WARNING", or "INFO"
          """
          
          # Start with rule's base severity
          base_severity = finding.get("severity", "WARNING")
          
          # Adjust based on context factors
          
          # Factor 1: Frequency (how often does this happen?)
          if finding.get("rule_name") == "TemperatureUptrend":
              # If temp trending up 5+ times in last 10 readings, escalate
              if context.get("uptrend_count", 0) >= 5:
                  return "CRITICAL"
          
          # Factor 2: Scope (how many features affected?)
          affected_count = len(finding.get("affected_columns", []))
          if affected_count >= 3 and base_severity == "WARNING":
              return "CRITICAL"
          
          # Factor 3: Trend (is it getting worse?)
          if context.get("is_worsening", False):
              if base_severity == "INFO":
                  return "WARNING"
              elif base_severity == "WARNING":
                  return "CRITICAL"
          
          # Factor 4: Business criticality (some features are more important)
          critical_features = ["temperature", "pressure", "motor_status"]
          if any(feat in critical_features for feat in finding.get("affected_columns", [])):
              if base_severity == "INFO":
                  return "WARNING"
          
          return base_severity

════════════════════════════════════════════════════════════════════════════════
DATABASE REPOSITORY - orchestration/insight_repo.py
════════════════════════════════════════════════════════════════════════════════

PURPOSE: Persist insights to database

STRUCTURE:

  from storage.connection import get_db_connection
  
  class InsightRepository:
      """Repository for insights table"""
      
      def __init__(self, db_connection=None):
          self.db = db_connection or get_db_connection()
      
      def bulk_insert(self, insights: List[dict]):
          """Insert multiple insights into database"""
          
          # Prepare data
          records = [insight.to_dict() if hasattr(insight, 'to_dict') else insight 
                     for insight in insights]
          
          # Convert to table format
          from duckdb import from_df
          import pandas as pd
          
          df = pd.DataFrame(records)
          
          # Insert
          self.db.execute("""
              INSERT INTO insights (
                  insight_id, run_id, type, severity, confidence,
                  title, description, data, source_module, created_at
              )
              SELECT * FROM df
          """)
          
          return len(records)
      
      
      def get_insights_for_run(self, run_id: str) -> List[dict]:
          """Fetch all insights for a run"""
          
          result = self.db.execute(f"""
              SELECT * FROM insights 
              WHERE run_id = ? 
              ORDER BY severity DESC, confidence DESC
          """, [run_id]).fetchall()
          
          return [dict(row) for row in result]

════════════════════════════════════════════════════════════════════════════════
INTEGRATION INTO pipeline_runner.py
════════════════════════════════════════════════════════════════════════════════

After Step 6 (Rules), add Step 7:

  # Step 7: Orchestration (Module 5)
  logger.info("Starting Module 5: Orchestration")
  
  from orchestration.insight_orchestrator import InsightOrchestrator
  from storage.repositories.insight_repo import InsightRepository
  
  orchestrator = InsightOrchestrator(logger)
  insight_repo = InsightRepository()
  
  # Get rule findings from Step 6
  # Assume: rule_findings is available from previous step
  
  # Get ML findings (optional)
  ml_findings = None
  # if Module 4 is implemented:
  #     from ml_engine.anomaly_detection import detect_anomalies
  #     ml_findings = detect_anomalies(feature_data)
  
  # Orchestrate
  insights = orchestrator.orchestrate(run_id, rule_findings, ml_findings)
  
  # Persist
  inserted_count = insight_repo.bulk_insert(insights)
  logger.info(f"✓ Created {inserted_count} insights")

════════════════════════════════════════════════════════════════════════════════
TESTING MODULE 5
════════════════════════════════════════════════════════════════════════════════

Test File: tests/test_module5_orchestration.py

  def test_rule_to_insight_conversion():
      """Test converting rule findings to insights"""
      
      orchestra = InsightOrchestrator()
      
      rule_findings = [{
          "rule_name": "TemperatureUptrend",
          "severity": "WARNING",
          "confidence": 0.85,
          "message": "Temperature increasing over last hour",
          "remediation": "Check cooling system",
          "affected_columns": ["temperature"]
      }]
      
      insights = orchestra.orchestrate("test_run_1", rule_findings)
      
      assert len(insights) == 1
      assert insights[0].title == "Temperature Rising"
      assert insights[0].severity.value == "WARNING"
      assert insights[0].source_module == 3
  
  
  def test_deduplication():
      """Test that duplicate insights are merged"""
      
      orchestra = InsightOrchestrator()
      
      # Two rules generating same insight
      rule_findings = [
          {
              "rule_name": "TemperatureUptrend",
              "severity": "WARNING",
              "confidence": 0.85,
              "message": "Temperature rising",
              "affected_columns": ["temperature"]
          },
          {
              "rule_name": "TemperatureUptrend",
              "severity": "CRITICAL",
              "confidence": 0.95,
              "message": "Temperature rising severely",
              "affected_columns": ["temperature"]
          }
      ]
      
      insights = orchestra.orchestrate("test_run_2", rule_findings)
      
      # Should have only 1 insight (deduped)
      # Should have kept CRITICAL severity
      assert len(insights) == 1
      assert insights[0].severity.value == "CRITICAL"
  
  
  def test_prioritization():
      """Test that insights are ranked by severity"""
      
      orchestra = InsightOrchestrator()
      
      rule_findings = [
          {"rule_name": "Rule1", "severity": "INFO", "confidence": 0.9},
          {"rule_name": "Rule2", "severity": "CRITICAL", "confidence": 0.7},
          {"rule_name": "Rule3", "severity": "WARNING", "confidence": 0.8}
      ]
      
      insights = orchestra.orchestrate("test_run_3", rule_findings)
      
      # Should be ordered: CRITICAL > WARNING > INFO
      assert insights[0].severity.value == "CRITICAL"
      assert insights[1].severity.value == "WARNING"
      assert insights[2].severity.value == "INFO"

════════════════════════════════════════════════════════════════════════════════
EXPECTED OUTPUT (insights table after Module 5)
════════════════════════════════════════════════════════════════════════════════

Query: SELECT * FROM insights;

Result:
  insight_id          | run_id    | type | severity | confidence | title                        | description
  ──────────────────────────────────────────────────────────────────────────────────────────────────────
  uuid-1234...        | run-001   | RULE | CRITICAL | 0.95       | Temperature Rising          | Temperature increasing over...
  uuid-5678...        | run-001   | RULE | WARNING  | 0.85       | Abnormal Vibration Detected | Vibration spike detected on...
  uuid-9012...        | run-001   | RULE | WARNING  | 0.80       | Maintenance Due             | PM overdue by 5 days on...
  uuid-3456...        | run-001   | RULE | INFO     | 0.60       | Energy Consumption Anomaly  | Unusual energy pattern...

════════════════════════════════════════════════════════════════════════════════
FINAL CHECKLIST FOR MODULE 5 COMPLETION
════════════════════════════════════════════════════════════════════════════════

  ☐ Created orchestration/insight_orchestrator.py (with InsightOrchestrator class)
  ☐ Created orchestration/prioritization.py (with InsightPrioritizer class)
  ☐ Created orchestration/severity_scoring.py (with SeverityAssessment class)
  ☐ Created storage/repositories/insight_repo.py (database access)
  ☐ Updated pipeline_runner.py to call Module 5 after Module 3
  ☐ Defined Insight dataclass with all required fields
  ☐ Implemented deduplication logic
  ☐ Implemented prioritization logic
  ☐ Created test file: tests/test_module5_orchestration.py
  ☐ Tests pass: pytest tests/test_module5_orchestration.py -v
  ☐ Verified insights table populated after run
  ☐ Verified insights have correct severity ordering
  ☐ Module 5 complete! ✓

════════════════════════════════════════════════════════════════════════════════
NEXT STEP
════════════════════════════════════════════════════════════════════════════════

After Module 5 is complete, proceed to Module 6 (Dashboard Engine).

Module 6 will use the insights table created here to provide context
for dashboard generation.

═══════════════════════════════════════════════════════════════════════════════
