# 🚀 Parcel Feasibility Engine - AI Agent Quick Start

## Your New Development Workflow

Instead of manually coding features, you now have an **autonomous AI agent system** that:
- Consults domain experts (planners, lawyers, housing specialists)
- Prioritizes features by value and complexity
- Delegates to specialized technical agents
- Builds, tests, documents, and deploys automatically

## ⚡ Getting Started (3 Steps)

### Step 1: Start a Planning Session

```bash
/plan-features
```

The Product Manager Agent will:
1. Consult 3 domain expert SMEs for requirements
2. Analyze your codebase for opportunities
3. Present a prioritized feature backlog

### Step 2: Select Features

You'll see something like:

```
# 🎯 Prioritized Feature Backlog

## 🔥 CRITICAL Priority

### 1. Multi-Parcel Batch Analysis
⭐⭐⭐⭐⭐ Value | 🔧🔧🔧 Complexity | 4-6 hours
Agents: Backend, Frontend, Testing

### 2. PDF Report Export
⭐⭐⭐⭐ Value | 🔧🔧 Complexity | 2-3 hours
Agents: Backend, Frontend

## 🚀 HIGH Priority

### 3. Historical Analysis Tracking
...

Select features: 1,2
```

### Step 3: Let Agents Work

After selection, agents work **fully autonomously**:
- ✅ Write all code
- ✅ Run tests (ensure 80%+ coverage)
- ✅ Update CLAUDE.md files
- ✅ Commit with descriptive messages
- ✅ Deploy to Railway + Vercel

You get a completion report with:
- What was built (with file locations)
- Test coverage metrics
- Commits and deployments
- Recommended next steps

## 🧠 Meet Your AI Team

### Domain Expert SMEs (Provide Requirements)

**Urban Planner SME**
- Expertise: Zoning, development standards, planning workflows
- When needed: Feature requirements, user workflows, GIS data needs

**Housing Law Attorney SME**
- Expertise: SB 9, SB 35, AB 2011, Density Bonus, compliance
- When needed: New laws, legal compliance, statutory calculations

**Affordable Housing Specialist SME**
- Expertise: AMI, LIHTC, affordability compliance, financing
- When needed: Affordability calculations, financial feasibility

### Technical Agents (Build Features)

**From VoltAgent Library** (`.claude-agents-library/`):
- **Backend**: Python Pro, Backend Developer
- **Frontend**: Next.js Developer, React Specialist
- **Quality**: QA Expert, Code Reviewer, Security Auditor
- **Infrastructure**: DevOps Engineer, Cloud Architect
- **Docs**: Documentation Engineer

## 📁 Where Everything Lives

```
.claude/
├── commands/
│   └── plan-features.md           # Entry point (use /plan-features)
├── agents/
│   ├── README.md                  # Full documentation
│   └── domain-experts/            # Planning & legal SMEs
│       ├── urban-planner-sme.md
│       ├── housing-law-attorney-sme.md
│       └── affordable-housing-specialist-sme.md
│
.claude-agents-library/            # Technical agents (VoltAgent)
└── categories/                    # 70+ specialized agents
```

## 🎯 Usage Examples

### Example 1: "I want to add PDF export"

```bash
/plan-features

# PM Agent:
→ Consults Urban Planner: "Planners need downloadable reports"
→ Presents backlog with PDF export prioritized
→ You select it
→ Backend Agent: Creates PDF generation service
→ Frontend Agent: Adds download button
→ QA Agent: Tests PDF content
→ DevOps Agent: Deploys to production
→ Done in ~2 hours, fully autonomous
```

### Example 2: "New law SB XXXX passed"

```bash
/plan-features

# PM Agent:
→ Consults Housing Law Attorney: Analyzes statute
→ Attorney SME: Provides implementation requirements
→ Python Pro: Codes eligibility logic
→ QA Expert: Validates against law
→ Documentation Engineer: Updates user guide
→ All autonomous, legal compliance ensured
```

### Example 3: "App is slow"

```bash
/plan-features

# PM Agent:
→ Identifies performance bottleneck
→ Consults Performance Engineer
→ Implements database indexing + query optimization
→ Result: 400ms → 80ms response time
→ Deployed automatically
```

## ⚙️ Configuration (Already Set)

**Autonomous Mode: ON** (agents don't need permission)
- ✅ Read/write files
- ✅ Run commands
- ✅ Commit changes
- ✅ Update docs
- ✅ Deploy

**Quality Standards: ENFORCED**
- Test coverage: 80%+ minimum
- TypeScript errors: Zero
- Linting: Clean
- CLAUDE.md: Always updated
- Performance: <200ms p95

## 🔄 Integration with CLAUDE.md

Agents automatically:
1. **Read** relevant CLAUDE.md before starting
2. **Follow** documented patterns
3. **Update** CLAUDE.md with new patterns
4. **Trigger** git pre-commit reminder

This keeps your living documentation current!

## 📊 What You Control

You make **strategic decisions**:
- Which features to build
- Priority order
- When to ship

Agents handle **implementation**:
- How to code it
- What tests to write
- How to deploy it
- How to document it

## 🆘 If Something Goes Wrong

Agents are reliable, but if needed:

1. **Check logs**: Review agent outputs in session
2. **Verify files**: Ensure code was written correctly
3. **Run tests**: `pytest` or `npm test`
4. **Manual fix**: Make changes, agents will learn from it

## 🎁 Bonus Features

**Git Pre-Commit Hook** (already installed):
- Reminds you to update CLAUDE.md on commits
- Shows which files to consider updating

**VoltAgent Library** (70+ agents available):
- Browse `.claude-agents-library/categories/`
- Copy any agent to `.claude/agents/` for customization

## 🚀 Ready to Build?

```bash
/plan-features
```

The Product Manager will consult the experts, analyze your codebase, and present options.

**Your role**: Pick what to build
**Agent role**: Build it autonomously

---

**Welcome to AI-powered development!** 🤖✨

Your development experience is now: Strategic vision, not implementation details.
