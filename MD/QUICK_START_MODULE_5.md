╔══════════════════════════════════════════════════════════════════════════════╗
║                         QUICK START ACTION PLAN                               ║
║                    Next 2 Hours: Implement Module 5                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════════════════
DECISION: Ready to build Module 5?
════════════════════════════════════════════════════════════════════════════════

If YES → Follow this guide
If NO → Read the documentation files first (see list at end)
If MAYBE → Scan the "WHAT WILL I BUILD" section below

════════════════════════════════════════════════════════════════════════════════
WHAT WILL I BUILD IN 2 HOURS?
════════════════════════════════════════════════════════════════════════════════

✓ One core orchestrator that merges rule findings
✓ A prioritizer that ranks insights by severity
✓ A severity calculator for smart severity assessment
✓ Database integration to persist insights

Result: insights table populated with real findings from rules

Before:
  └─ Rules fire (10 domain rules from Module 3)
  └─ But findings are just objects in memory (not stored)

After:
  └─ Rules fire
  └─ Module 5 merges & deduplicates them
  └─ Insights table is populated
  └─ Frontend can query and display them
  └─ Module 6 can use insights for dashboard context

════════════════════════════════════════════════════════════════════════════════
FILES TO CREATE: 3 PYTHON FILES (~500 lines total)
════════════════════════════════════════════════════════════════════════════════

CREATE THESE FILES (in this order):

1️⃣  orchestration/insight_orchestrator.py        [~250 lines]
2️⃣  orchestration/severity_scoring.py            [~100 lines]
3️⃣  orchestration/prioritization.py              [~100 lines]

PLUS UPDATE:

4️⃣  storage/repositories/insight_repo.py         [~80 lines - NEW]
5️⃣  app/pipeline_runner.py                       [~20 lines - ADD STEP 7]

════════════════════════════════════════════════════════════════════════════════
STEP-BY-STEP ACTION:
════════════════════════════════════════════════════════════════════════════════

⏱️  TOTAL TIME: ~120 minutes

┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Create insight_orchestrator.py [40 minutes]         │
└─────────────────────────────────────────────────────────────┘

What to code:
  • InsightType enum (RULE, ML, HEALTH)
  • SeverityLevel enum (CRITICAL, WARNING, INFO)  
  • Insight dataclass (the data structure)
  • InsightOrchestrator class (main orchestrator)
    ├─ orchestrate() - Main method
    ├─ _convert_rule_findings() - Convert Module 3 output
    ├─ _convert_ml_findings() - Convert Module 4 output (if present)
    ├─ _deduplicate_insights() - Remove duplicates
    ├─ _prioritize_insights() - Sort by severity
    ├─ _generate_title() - Human-readable titles
    └─ _extract_*_data() - Data formatting

Code structure ALREADY PROVIDED in:
  → MODULE_5_IMPLEMENTATION_GUIDE.md (just copy the InsightOrchestrator class)

File location:
  orchestration/insight_orchestrator.py

Task:
  ☐ Copy class structure from guide
  ☐ Fill in any TODOs
  ☐ Test: python -c "from orchestration.insight_orchestrator import InsightOrchestrator"


┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create severity_scoring.py [20 minutes]             │
└─────────────────────────────────────────────────────────────┘

What to code:
  • SeverityAssessment class
  • assess_severity() method (multi-factor severity logic)

Rules:
  • Base severity from rule
  • Escalate if affecting multiple columns
  • Escalate if getting worse (trend analysis)
  • Escalate if frequent occurrence

File location:
  orchestration/severity_scoring.py

Task:
  ☐ Create class with assess_severity() method
  ☐ ~100 lines
  ☐ Handle 4 factors: frequency, scope, trend, criticality


┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Create prioritization.py [20 minutes]               │
└─────────────────────────────────────────────────────────────┘

What to code:
  • PrioritizedInsight dataclass
  • InsightPrioritizer class
  • prioritize() method (rank insights)
  • _calculate_priority_score() (weighted scoring)

Formula:
  score = (severity_weight × 50) + (confidence × 30) + (impact × 20)

File location:
  orchestration/prioritization.py

Task:
  ☐ Create prioritizer class
  ☐ ~100 lines
  ☐ Return top 20 insights ranked by importance


┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Create insight_repo.py [30 minutes]                 │
└─────────────────────────────────────────────────────────────┘

What to code:
  • InsightRepository class
  • bulk_insert() - Save insights to database
  • get_insights_for_run() - Query insights

File location:
  storage/repositories/insight_repo.py

Task:
  ☐ Create repository class
  ☐ Implement bulk_insert(insights) using DuckDB
  ☐ Implement get_insights_for_run(run_id) query
  ☐ ~80 lines


┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Integrate into pipeline_runner.py [15 minutes]      │
└─────────────────────────────────────────────────────────────┘

After Step 6 (Rules), add:

  # Step 7: Orchestration (Module 5)
  logger.info("Starting Module 5: Orchestration")
  
  from orchestration.insight_orchestrator import InsightOrchestrator
  from storage.repositories.insight_repo import InsightRepository
  
  orchestrator = InsightOrchestrator(logger)
  insight_repo = InsightRepository()
  
  # Get rule findings from previous step
  ml_findings = None  # Module 4 not implemented yet
  
  insights = orchestrator.orchestrate(run_id, rule_findings, ml_findings)
  inserted = insight_repo.bulk_insert(insights)
  logger.info(f"✓ Created {inserted} insights")

Task:
  ☐ Add imports
  ☐ Add Step 7 after Step 6
  ☐ Test: Pipeline runs without errors


┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Test Module 5 [15 minutes]                          │
└─────────────────────────────────────────────────────────────┘

Test case 1: Run pipeline with sample data
  $ python app/pipeline_runner.py
  → Check logs: "Created X insights"
  → Verify: SELECT COUNT(*) FROM insights;

Test case 2: Verify insights table populated
  $ duckdb storage/offline_endurance_intelligence.duckdb
  > SELECT * FROM insights LIMIT 5;
  → Should show insights with: type, severity, confidence, title

Test case 3: Check deduplication
  $ python -c "from tests.test_module5_orchestration import test_*; test_deduplication()"

Task:
  ☐ Run pipeline
  ☐ Check insights in database
  ☐ Verify severity ordering
  ☐ All lights green!

════════════════════════════════════════════════════════════════════════════════
REFERENCE: Code Templates (Copy-Paste Ready)
════════════════════════════════════════════════════════════════════════════════

Complete code structures are in:
  → MODULE_5_IMPLEMENTATION_GUIDE.md

You can literally copy the class definitions and just fill in method bodies.

════════════════════════════════════════════════════════════════════════════════
IMPORTANT: What Can Go Wrong (Troubleshooting)
════════════════════════════════════════════════════════════════════════════════

❌ Import errors (orchestration module not found)
   FIX: Make sure __init__.py exists in orchestration/
   $ touch orchestration/__init__.py

❌ Database errors (insights table not found)
   FIX: Check schema.sql was applied correctly
   $ duckdb storage/offline_endurance_intelligence.duckdb < storage/schema.sql

❌ Finding findings missing
   FIX: Verify rule_findings is being passed correctly from step 6
   $ Add logger.info(f"Rule findings: {len(rule_findings)}") before orchestrate()

❌ Type errors with dataclasses
   FIX: Define Insight as @dataclass with field defaults
   FIX: Use field(default_factory=...) for mutable defaults

❌ Severity enum mismatch
   FIX: Use SeverityLevel["CRITICAL"] not SeverityLevel.CRITICAL in string comparisons

════════════════════════════════════════════════════════════════════════════════
SUCCESS INDICATORS
════════════════════════════════════════════════════════════════════════════════

✅ You'll know Module 5 is done when:

  1. Pipeline runs without errors (Step 1-7 all execute)
  2. insights table has records (SELECT COUNT(*) FROM insights > 0)
  3. Insights are ordered by severity (CRITICAL first, INFO last)
  4. No duplicate titles (deduplication working)
  5. Confidence scores are in 0.0-1.0 range
  6. created_at timestamps are recent
  7. Tests pass: pytest tests/test_module5_orchestration.py -v

Example output:
  ✓ Created 3 insights
  ✓ Severity ordering correct (CRITICAL, WARNING, INFO)
  ✓ Deduplication working (5 findings → 3 insights)
  ✓ Confidence scores valid (0.60-0.95)
  ✓ Database persisted correctly
  
  RESULT: Module 5 COMPLETE ✓

════════════════════════════════════════════════════════════════════════════════
WHAT HAPPENS NEXT
════════════════════════════════════════════════════════════════════════════════

After Module 5 is done:

  ✓ Frontend Insights page can now query real data (instead of hardcoded)
  ✓ Module 6 (Dashboard) can use insights table for context
  ✓ Rule findings are permanently stored
  ✓ User sees actual findings from their data

Then we move to Module 6 (Dashboard) - the PRIMARY FEATURE:
  → Auto-generate beautiful charts
  → Professional dashboard layout
  → This is what makes your app valuable!

════════════════════════════════════════════════════════════════════════════════
DOCUMENTATION REFERENCE
════════════════════════════════════════════════════════════════════════════════

Need more details? Read these files:

📄 COMPLETE_MODULE_MAP.md
   └─ Full project overview
   
📄 IMPLEMENTATION_ROADMAP.md
   └─ All 5 modules planned in detail
   
📄 MODULE_5_IMPLEMENTATION_GUIDE.md
   └─ Complete code templates (copy-paste ready)
   └─ Database integration examples
   └─ Testing patterns
   
📄 PROJECT_ANALYSIS_SUMMARY.md
   └─ Session summary and context

════════════════════════════════════════════════════════════════════════════════
READY? Start with Step 1 (orchestration/insight_orchestrator.py)
════════════════════════════════════════════════════════════════════════════════
