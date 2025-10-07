# Parcel Feasibility Engine - AI Agent Development System

Automated, intelligent development workflow using specialized AI agents for planning, coding, and deployment.

## 🎯 Quick Start

```bash
# Start a product planning session
/plan-features
```

The Product Manager Agent will:
1. ✅ Consult domain expert SMEs (planners, lawyers, housing specialists)
2. ✅ Review codebase and identify opportunities
3. ✅ Present prioritized feature backlog
4. ✅ Let you select features to build
5. ✅ Automatically delegate to specialized agents
6. ✅ Execute development autonomously
7. ✅ Run tests, update docs, deploy

## 🏗️ Architecture

```
Product Manager (Orchestrator)
├── Consults: Domain Expert SMEs
│   ├── Urban Planner SME
│   ├── Housing Law Attorney SME
│   └── Affordable Housing Specialist SME
│
└── Delegates to: Technical Agents
    ├── Backend: Python Pro / Backend Developer
    ├── Frontend: Next.js Developer / React Specialist
    ├── Full Stack: Full Stack Developer
    ├── Testing: QA Expert
    ├── Security: Security Auditor
    ├── Performance: Performance Engineer
    ├── DevOps: DevOps Engineer
    └── Docs: Documentation Engineer
```

## 📁 Agent Organization

```
.claude/
├── commands/
│   └── plan-features.md          # PM Agent entry point (use /plan-features)
├── agents/
│   └── domain-experts/            # Domain SMEs
│       ├── urban-planner-sme.md
│       ├── housing-law-attorney-sme.md
│       └── affordable-housing-specialist-sme.md
│
.claude-agents-library/            # Technical agents from VoltAgent
├── categories/
│   ├── 01-core-development/       # Backend, Frontend, Full Stack
│   ├── 02-language-specialists/   # Python Pro, TypeScript Pro, etc.
│   ├── 03-infrastructure/         # Cloud, DevOps, Database
│   ├── 04-quality-security/       # Code Reviewer, QA, Security
│   ├── 05-data-ai/                # Data Analyst, AI Engineer
│   ├── 06-developer-experience/   # Documentation, DevX
│   ├── 08-business-product/       # Product Manager, Business Analyst
│   └── 09-meta-orchestration/     # Architect, Tech Lead
```

## 🧠 Domain Expert SMEs

### Urban Planner SME
**Expertise**: California zoning, development standards, planning processes
- Santa Monica zoning codes (R1, R2, R3, OP, commercial, mixed-use)
- CEQA, General Plans, development feasibility
- Entitlement pathways (ministerial, ARP, DRP, CUP)
- Real-world planning workflows and user needs

**When to Consult**:
- Feature requirements involving zoning or development standards
- User experience design for planners/applicants
- GIS data requirements
- Edge cases in local code interpretation

### Housing Law Attorney SME
**Expertise**: State housing legislation, statutory interpretation, compliance
- SB 9 (lot splits, duplexes)
- SB 35 (streamlined approval)
- AB 2011 (affordable corridors)
- Density Bonus Law (bonuses, concessions, waivers)
- ADU/JADU law, Housing Accountability Act

**When to Consult**:
- Implementing new housing laws
- Legal compliance requirements
- Preemption analysis (state vs. local)
- Risk assessment
- Statutory calculation logic

### Affordable Housing Specialist SME
**Expertise**: LIHTC, AMI calculations, affordability compliance, financing
- Income limits (extremely low, very low, low, moderate)
- Rent/price affordability formulas
- LIHTC, MHP, and other programs
- Deed restrictions and compliance monitoring
- Pro forma analysis and financing structures

**When to Consult**:
- Affordability calculations
- Financial feasibility analysis
- Compliance monitoring features
- Program-specific requirements (LIHTC, etc.)

## 🔧 Technical Agents (from .claude-agents-library)

### Core Development
- **Backend Developer**: Python/FastAPI expert, API design, database optimization
- **Frontend Developer**: React/Next.js expert, UI/UX, accessibility
- **Full Stack Developer**: End-to-end features, seamless integration

### Language Specialists
- **Python Pro**: FastAPI, Pydantic, pytest, async patterns
- **Next.js Developer**: App Router, server components, performance
- **React Specialist**: Hooks, state management, optimization
- **TypeScript Pro**: Type safety, tRPC, advanced patterns

### Infrastructure
- **DevOps Engineer**: CI/CD, Docker, Kubernetes, monitoring
- **Cloud Architect**: AWS/GCP/Azure, scalability, disaster recovery
- **Database Administrator**: PostgreSQL optimization, migrations, backups

### Quality & Security
- **Code Reviewer**: Multi-language review, security, performance
- **QA Expert**: Test strategy, automation, coverage
- **Security Auditor**: SOC 2, GDPR, vulnerability assessment
- **Performance Engineer**: Load testing, profiling, optimization

### Meta & Orchestration
- **Architect**: System design, technical strategy
- **Tech Lead**: Team coordination, standards, roadmap

## 🚀 Usage Examples

### Example 1: Implementing New Feature

```bash
# Start planning session
/plan-features

# PM consults SMEs
→ Urban Planner: "Users need multi-parcel batch analysis"
→ Housing Attorney: "SB 684 requires new calculations"
→ Affordable Housing: "AMI lookup tool would help"

# PM presents prioritized backlog
1. [CRITICAL] SB 684 Implementation
2. [HIGH] Multi-Parcel Batch Analysis
3. [MEDIUM] PDF Export
4. [LOW] AMI Calculator

# You select: "1,2"

# PM breaks down and delegates
→ SB 684:
  - Housing Attorney SME: Define requirements
  - Python Pro: Implement calculation logic
  - QA Expert: Create test suite

→ Multi-Parcel:
  - Backend Developer: POST /api/v1/analyze/batch
  - Next.js Developer: Batch upload UI
  - QA Expert: Integration tests

# Agents execute autonomously
✅ All code written
✅ Tests passing (87% coverage)
✅ CLAUDE.md updated
✅ Deployed to Railway + Vercel

# You get completion report with commits, metrics, next steps
```

### Example 2: Code Review & Optimization

```bash
# PM analyzes codebase
→ Identifies performance bottleneck in parcel search
→ Consults Performance Engineer
→ Implements database indexing + query optimization
→ Result: 400ms → 80ms response time
```

### Example 3: Legal Compliance Update

```bash
# New law passed: AB XXXX
→ Housing Attorney SME: Analyzes statute
→ Provides implementation requirements
→ Python Pro: Codes eligibility logic
→ QA Expert: Validates against statute
→ Documentation Engineer: Updates user guide
```

## ⚙️ Configuration

### Autonomous Execution (Default: ON)

Agents can automatically:
- ✅ Read and write files
- ✅ Run commands (tests, builds)
- ✅ Commit changes with descriptive messages
- ✅ Update CLAUDE.md files
- ✅ Deploy to staging/production

Agents CANNOT:
- ❌ Delete production data
- ❌ Modify .git/config
- ❌ Change security settings

### Quality Standards (Enforced)

- **Test Coverage**: Minimum 80% for business logic
- **Type Safety**: Zero TypeScript errors
- **Linting**: Zero linting issues
- **Security**: No vulnerabilities (npm audit, safety)
- **Performance**: APIs <200ms p95
- **Documentation**: CLAUDE.md updated for new patterns

## 📊 Agent Communication Protocol

Agents coordinate through structured task context:

```json
{
  "task_id": "feat-batch-analysis",
  "feature": "Multi-Parcel Batch Analysis",
  "assigned_to": "backend-developer",
  "status": "in_progress",
  "dependencies": [],
  "deliverables": [
    "POST /api/v1/analyze/batch endpoint",
    "BatchAnalysisRequest/Response models",
    "Batch processing with async queue",
    "Tests for concurrent analysis"
  ],
  "context": {
    "related_files": ["app/api/analyze.py", "app/models/analysis.py"],
    "patterns_to_follow": ["app/CLAUDE.md - Pydantic v2 patterns"],
    "integration_points": ["frontend needs new API client method"],
    "domain_expert_input": "Urban Planner SME recommends CSV upload format"
  }
}
```

## 🎯 Development Workflow

### 1. Planning Phase (PM + SMEs)
- Consult domain experts for requirements
- Review codebase for opportunities
- Prioritize by value, complexity, strategic fit
- Present backlog to user

### 2. Parallel Development (Technical Agents)
- Backend builds APIs
- Frontend builds UI
- Legal agent implements rules
- All execute simultaneously when no dependencies

### 3. Integration Phase (PM Coordinates)
- Ensure frontend/backend integration
- Resolve conflicts
- Run integration tests

### 4. Quality Assurance (QA + Security + Performance)
- Comprehensive test suites
- Security scanning
- Performance profiling
- Coverage analysis

### 5. Documentation (All Agents)
- Update CLAUDE.md files
- Add code comments/docstrings
- Update API docs

### 6. Deployment (DevOps)
- Deploy to Railway (backend)
- Deploy to Vercel (frontend)
- Verify deployments
- Monitor for errors

## 🔗 Integration with CLAUDE.md

All agents follow project-specific patterns documented in CLAUDE.md files:

- **Root CLAUDE.md**: Project overview, tech stack, setup
- **app/CLAUDE.md**: Backend patterns, Pydantic models
- **app/rules/CLAUDE.md**: Housing law implementation
- **frontend/CLAUDE.md**: Next.js patterns, TypeScript
- **frontend/components/CLAUDE.md**: React patterns, Tailwind
- **tests/CLAUDE.md**: Testing patterns

Agents automatically:
1. Read relevant CLAUDE.md before starting
2. Follow documented patterns
3. Update CLAUDE.md with new patterns
4. Trigger git pre-commit hook reminder

## 📈 Benefits

✅ **10x Faster Development**: Parallel agent execution
✅ **Consistent Quality**: Agents follow CLAUDE.md patterns automatically
✅ **Domain Expertise**: SME agents provide planning/legal knowledge
✅ **Comprehensive Testing**: QA agent ensures coverage
✅ **Automated Docs**: CLAUDE.md always current
✅ **Zero-Friction Deploy**: DevOps agent handles it all
✅ **Scalable**: Add new agents as needs grow

## 🆕 Adding New Agents

### Domain Expert SME

1. Create `.claude/agents/domain-experts/[name]-sme.md`
2. Include expertise areas, responsibilities, deliverables format
3. Add to PM Agent consultation list in `/plan-features`

### Technical Agent

1. Browse `.claude-agents-library/categories/` for relevant agent
2. Copy to `.claude/agents/` if customization needed
3. Reference in PM Agent delegation logic

## 🔍 Debugging Agent Workflows

If agent execution fails:

1. **Check agent logs**: Review tool call outputs
2. **Verify file access**: Ensure paths are correct
3. **Review dependencies**: Check if prerequisite tasks completed
4. **Consult CLAUDE.md**: Verify patterns are documented
5. **Manual intervention**: Complete task manually, update agent prompt

## 📚 Resources

- **VoltAgent Awesome Agents**: https://github.com/VoltAgent/awesome-claude-code-subagents
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **Project CLAUDE.md**: /CLAUDE.md
- **Domain Expert SMEs**: .claude/agents/domain-experts/

---

## 🎬 Get Started Now

```bash
/plan-features
```

Let the Product Manager Agent consult the experts, analyze your codebase, and present a prioritized feature backlog. Select what you want built, and watch the agents work autonomously to deliver production-ready features.

**Your development experience**: Strategic decisions, not implementation details.
