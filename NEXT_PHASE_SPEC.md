# Next Phase Architecture Spec
**Parcel Feasibility Engine — v2 Blueprint**

> This document defines the three major architectural changes needed to evolve the platform from a powerful developer tool into a product that feels like a senior entitlement consultant built into software. Written as a concrete blueprint for implementation in Claude Code or similar AI-assisted coding sessions.

---

## The Three Problems to Solve

1. **Rules engine won't scale** — rules are hardcoded Python logic per jurisdiction. Adding LA County means copying and modifying all modules. Code changes when laws change. No versioning, no citations embedded, no confidence levels.

2. **No agentic layer** — the engine does all the work silently and dumps structured data. No LLM narrates results, guides users, or surfaces what actually matters for a given parcel and intent.

3. **UX doesn't feel inevitable** — the current flow asks the user to go through a large technical form before getting results. The "just works" version hides complexity entirely and leads with intent.

---

## Part 1: Rules-as-Data Engine

### Problem
Current rules are Python logic (`sb9.py`, `overlays.py`, etc.) with constraints embedded in conditionals. This is:
- Hard to version independently from code
- Impossible for non-engineers to inspect or maintain
- Unscalable across jurisdictions without rewriting modules
- Incapable of surfacing citations or confidence levels at the rule level

### Design Principles
- Rules are structured data, not code logic
- Python modules become **rule evaluators** (interpret data), not rule definitions
- Each rule carries its own metadata: citation, confidence, version, effective date
- Pathways (SB 9, SB 35, Density Bonus) are first-class objects with their own schema
- Precedence is explicit and configurable per jurisdiction

### Rule Schema

```python
# app/models/rules_engine.py

class RuleEffect(BaseModel):
    effect_type: Literal["constraint", "formula", "requirement", "eligibility", "advisory"]
    field: str                          # e.g. "max_height_ft", "min_setback_ft"
    operator: Literal["set", "add", "multiply", "min", "max", "require", "prohibit"]
    value: Union[float, str, bool]
    condition: Optional[str] = None     # JSONLogic expression for conditional effects
    explanation: str                    # Human-readable explanation of this effect

class Rule(BaseModel):
    id: str                             # e.g. "sm_r2_max_height"
    jurisdiction_id: str                # e.g. "santa_monica_ca"
    law_code: Optional[str]             # e.g. "SMMC 9.07.020"
    rule_type: Literal["base_zoning", "overlay", "pathway", "exception", "administrative"]
    name: str
    description: str
    applies_when: dict                  # JSONLogic conditions: {"parcel.zoning": "R2"}
    effects: List[RuleEffect]
    citations: List[str]                # e.g. ["Gov. Code § 65852.21", "SMMC 9.07.020(b)"]
    confidence: Literal["definitive", "interpretive", "advisory"]
    version: str                        # semver
    effective_date: date
    superseded_by: Optional[str] = None # Rule id that replaces this one
    precedence: int                     # Higher = evaluated later, wins conflicts

class Pathway(BaseModel):
    id: str                             # e.g. "sb9_lot_split"
    jurisdiction_id: str
    name: str                           # "SB 9 Lot Split"
    law_code: str                       # "Gov. Code § 65852.21"
    eligibility_conditions: dict        # JSONLogic: all must be true
    ineligibility_conditions: dict      # JSONLogic: any makes pathway unavailable
    modified_constraints: List[Rule]    # Rules that replace/modify base zoning
    additional_obligations: List[str]   # e.g. ["owner-occupancy affidavit", "no prior split"]
    approval_type: Literal["ministerial", "administrative", "discretionary"]
    statutory_deadline_days: Optional[int]
    description: str
    citations: List[str]

class Jurisdiction(BaseModel):
    id: str                             # "santa_monica_ca"
    name: str                           # "Santa Monica, CA"
    state: str                          # "CA"
    base_rules: List[str]               # Rule ids that apply by default
    overlay_rules: List[str]            # Rule ids for overlay districts
    pathways: List[str]                 # Pathway ids available in this jurisdiction
    rule_precedence_order: List[str]    # ["base_zoning", "overlay", "pathway", "exception"]
    last_updated: date
    update_notes: str
```

### Rule Evaluator Pattern

```python
# app/rules/evaluator.py
# Replace hardcoded logic modules with a single evaluator that interprets rule data

class RuleEvaluator:
    def __init__(self, jurisdiction: Jurisdiction, rules: List[Rule], pathways: List[Pathway]):
        self.jurisdiction = jurisdiction
        self.rules = {r.id: r for r in rules}
        self.pathways = {p.id: p for p in pathways}

    def evaluate_parcel(self, parcel: ParcelBase, project: Optional[ProjectBase] = None) -> EvaluationResult:
        """
        Apply all applicable rules to a parcel in precedence order.
        Returns constraints, pathway eligibility, and per-rule audit trail.
        """
        context = self._build_context(parcel, project)
        applicable_rules = self._filter_applicable_rules(context)
        constraints = self._apply_rules_in_precedence(applicable_rules, context)
        pathway_results = self._evaluate_pathways(context, constraints)

        return EvaluationResult(
            constraints=constraints,
            pathways=pathway_results,
            applied_rules=[r.id for r in applicable_rules],
            skipped_rules=self._explain_skipped_rules(context),
            assumptions=self._surface_assumptions(context),
            citations=self._collect_citations(applicable_rules),
        )
```

### Migration Path
1. Define `Rule`, `Pathway`, `Jurisdiction` models (new file: `app/models/rules_engine.py`)
2. Create DB tables + Alembic migration for rule storage
3. Write a **seed script** that converts existing Python rule logic into rule data records for Santa Monica
4. Build `RuleEvaluator` to replace per-law modules
5. Keep existing modules as fallback until evaluator is validated against test suite (247 tests must still pass)
6. Once tests pass with evaluator, deprecate old modules

> **Key constraint:** Do not break existing API contract during migration. `POST /api/v1/analyze` should return identical results before and after.

---

## Part 2: Agentic Layer

### Design Principles
- The LLM **never** makes zoning conclusions — only the rules engine does
- The LLM **narrates, guides, and explains** what the engine found
- The agentic layer is stateful per session (conversation memory)
- Outputs are always grounded: LLM cites specific rules, never fabricates

### Architecture

```
User Intent
    ↓
IntentClassifier (LLM, lightweight)
    ↓
RuleEvaluator (deterministic, no LLM)
    ↓
AdvisoryScorer (heuristic risk signals)
    ↓
NarrativeGenerator (LLM, grounded in engine output)
    ↓
DynamicActionSuggester (rule-driven, not LLM)
    ↓
Response: { narrative, metrics, actions, citations }
```

### Intent Types
```python
class UserIntent(str, Enum):
    MAXIMIZE_UNITS = "maximize_units"           # What's the most I can build?
    FASTEST_PATH = "fastest_path"               # What gets approved quickest?
    LOWEST_RISK = "lowest_risk"                 # What's least likely to get denied?
    CHECK_SPECIFIC_LAW = "check_specific_law"   # Does SB 9 apply here?
    CHECK_PLANS = "check_plans"                 # Validate uploaded concept
    EXPLORE = "explore"                         # General: what can I build?
```

### New API Endpoint

```python
# POST /api/v1/advise
class AdviseRequest(BaseModel):
    parcel_apn: str
    intent: UserIntent
    context: Optional[str] = None       # Free text: "I want to build 8 units affordable"
    conversation_id: Optional[str] = None  # For follow-up turns

class AdviseResponse(BaseModel):
    conversation_id: str
    headline: str                        # "SB 9 gives you 4 units on this parcel"
    narrative: str                       # 2-3 paragraph LLM explanation
    key_metrics: List[KeyMetric]         # Max units, height, timeline, etc.
    pathways: List[PathwayResult]        # Ranked by intent
    risk_signals: List[RiskSignal]       # Advisory layer findings
    suggested_actions: List[SuggestedAction]  # Dynamic follow-ups
    citations: List[Citation]            # All rules that produced this output
    confidence: Literal["high", "medium", "low"]
    assumptions: List[str]              # What was assumed, what needs verification
```

### Advisory/Risk Layer

This is the pre-application intelligence that turns the product from a lookup tool into a consultant:

```python
class RiskSignal(BaseModel):
    signal_type: Literal["planning_concern", "review_trigger", "delay_risk", "eligibility_risk"]
    severity: Literal["high", "medium", "low"]
    title: str                          # "Historic adjacency may trigger Design Review"
    explanation: str
    source: str                         # What triggered this signal
    mitigation: Optional[str]           # What the developer can do about it

# Risk signals are heuristic — NOT LLM-generated
# They come from pattern matching on parcel attributes + rule outputs:
# - Coastal zone → flag for Coastal Commission review risk
# - Historic district adjacency → flag Design Review Process
# - Discretionary pathway → flag community opposition risk
# - Missing RHNA progress → flag SB 35 threshold uncertainty
```

### LLM Grounding Pattern

```python
# The LLM prompt is always structured, never open-ended
NARRATIVE_PROMPT = """
You are an entitlement consultant explaining analysis results to a real estate developer.
The following are FACTS produced by a deterministic rules engine. Do not add conclusions not in the data.

PARCEL: {parcel_summary}
INTENT: {user_intent}
ENGINE RESULTS: {engine_output_json}
RISK SIGNALS: {risk_signals_json}
CITATIONS: {citations_list}

Write a 2-3 paragraph explanation that:
1. Directly answers the user's intent ({user_intent})
2. Highlights the most important finding first
3. Explains any key constraints or risks
4. Uses plain language (no jargon without explanation)
5. Ends with what the developer should do next

Do not invent numbers. Every figure must come from ENGINE RESULTS above.
Cite rules parenthetically when relevant: (Gov. Code § 65852.21)
"""
```

### LLM Provider Strategy
- Default: Anthropic Claude (already have API key context)
- Fallback: OpenAI GPT-4o
- Model: Use a fast/cheap model (Haiku, GPT-4o-mini) for intent classification; use full model for narrative
- Keep LLM calls to 1-2 per user action max

---

## Part 3: UX Redesign

### Core Principle
> Hide complexity. Lead with intent. Surface only what matters.

The current flow requires users to make decisions constantly. The new flow makes one decision per step and the product handles the rest.

### New Flow

```
1. MAP (default view)
   └─ Click any parcel in Santa Monica
       ↓
2. PARCEL SNAPSHOT (replaces "Continue to Form")
   ┌─────────────────────────────────────┐
   │ 624 Lincoln Blvd                    │
   │ R2 Zone · 7,500 sq ft · Coastal     │
   │ Built 1962 · Not rent controlled    │
   └─────────────────────────────────────┘
   "What do you want to do with this parcel?"
   [Maximize Units] [Fastest Approval] [Lowest Risk] [Check My Plans]
       ↓
3. RESULTS (intent-driven)
   ┌─────────────────────────────────────┐
   │ Best path for maximum units: SB 9   │
   │ + Density Bonus → up to 6 units     │
   │                                     │
   │ ⚠ Coastal overlay limits height     │
   │ ✓ Not historic — no DRP required    │
   │ ✓ Near transit — no parking req'd   │
   └─────────────────────────────────────┘
   [Tell me more about SB 9 here]
   [What's the timeline?]
   [Show me the financial picture]
   [What could go wrong?]
       ↓
4. CONVERSATION (follow-up turns, agent-driven)
   Any suggested action becomes the next turn
   Agent responds with focused, relevant answer
   Deep-dive tabs available but not default
```

### Component Changes

| Current | Replace With | Why |
|---|---|---|
| `ParcelForm.tsx` (40KB) | `ParcelSnapshotCard` + intent buttons | Form complexity hidden, auto-filled from GIS |
| `ResultsDashboard` tab dump | `AdvisorResponse` narrative-first layout | Lead with headline + narrative, tabs become "dig deeper" |
| Static 3-button toggle (Map/MultiParcel/Manual) | Map as primary, address search as secondary | Map is the natural entry point |
| No follow-up mechanism | `ConversationThread` component | Each result generates contextual follow-up actions |

### New Component Architecture

```
page.tsx
├── ParcelMap (primary entry — unchanged mostly)
├── ParcelSnapshotCard (new — replaces "Continue to Form" gate)
│   ├── ParcelQuickStats (APN, zone, size, overlays, rent control)
│   └── IntentSelector (4-6 intent buttons)
├── AdvisorResponse (new — replaces ResultsDashboard as primary view)
│   ├── HeadlineCard (the one-line answer)
│   ├── NarrativePanel (LLM output, 2-3 paragraphs)
│   ├── KeyMetricsRow (max units, height, timeline, risk level)
│   ├── RiskSignalList (advisory flags)
│   ├── SuggestedActions (dynamic follow-up buttons)
│   └── CitationsPanel (SourceNotesPanel, already exists)
└── DeepDiveDrawer (existing tabs moved here — accessible but not default)
    ├── ScenarioComparison (existing)
    ├── EconomicFeasibility (existing)
    ├── TimelineVisualization (existing)
    └── ... (other existing tabs)
```

> **Key:** existing components don't get deleted — they move into `DeepDiveDrawer`. Users who want the full data still get it. But it's not the default landing.

---

## Implementation Order

### Step 1 — Agentic Layer First (highest UX impact, lowest backend risk)
The existing rules engine is solid. We can put the LLM layer on top of it without touching the rules modules.
- Add `POST /api/v1/advise` endpoint
- Implement `IntentClassifier` (lightweight)
- Implement `NarrativeGenerator` with grounding prompt
- Implement `RiskSignalDetector` (heuristic, no LLM)
- Implement `DynamicActionSuggester`
- Wire to frontend with new `AdvisorResponse` component

**Why first:** Highest impact on the "feels right" problem. Can be done without touching the rules engine.

### Step 2 — UX Redesign
- Build `ParcelSnapshotCard` + `IntentSelector`
- Build `AdvisorResponse` component
- Move existing tabs into `DeepDiveDrawer`
- Update `page.tsx` flow

**Why second:** The agentic layer needs to be working before the new UX can use it.

### Step 3 — Rules-as-Data Migration
- Define schemas + DB tables
- Write Santa Monica seed script from existing Python logic
- Build `RuleEvaluator`
- Validate against existing 247-test suite
- Deprecate old modules

**Why third:** Lowest urgency, highest risk of regression. Existing rules work. This is foundation for multi-jurisdiction expansion.

---

## What This Is Not

To stay focused, the following are explicitly **out of scope** for this phase:

- Multi-city support (LA, Pasadena, etc.) — after rules-as-data is working
- Uploaded plan analysis — after agentic layer is stable
- City/planner authoring interface — later phase
- Mobile-responsive redesign — after desktop UX is right
- Enterprise multi-user features — after first paying customers

---

## Notes on COI / Trust

Per the product strategy:
- All outputs must be grounded in **public rules only** — no outputs that imply insider city knowledge
- Every result must show its source citations
- Hard constraints and advisory interpretations must be clearly separated
- Outputs framed as "analysis based on public code" not "official city determination"
- Confidence levels surfaced explicitly on interpretive outputs

---

*Last updated: 2026-03-23*
*Status: Blueprint — not yet implemented*
