# MarketSage — Decision Log

All decisions below are durable records. New decisions must be appended; do not rewrite history silently.

## 2026-11-02 — Adopt a governed execution model

**Decision authority:** Owner  
**Status:** Approved in conversation; repository adoption pending merge.

**Decision**
- MarketSage is an internal investment-decision system for the owner's own capital, not primarily an academic research project or public SaaS.
- The nine rules in `PROJECT_EXECUTION_CONSTITUTION.md` govern all project work.
- The owner delegates routine engineering implementation, PR merging, and software deployment to the execution lead when the change remains within the approved strategy and passes required checks.
- Any change to product strategy, investment horizon/universe principles, fundamental modeling direction, or material capital risk must be presented to the owner for explicit approval.
- Real-money trades, broker orders, and portfolio allocation changes are not authorized by this delegation.
- All significant work must be recorded in Git; repeated work must be prevented through state, manifest, hash, and decision records.

**Repository privacy**
- Owner instructed that `yarsalam/marketsage` be changed from Public to Private.
- Completed by the owner on 2026-11-02; repository metadata now reports `visibility: private`.
- A subsequent rulesets API read returned HTTP 403 with GitHub's message to upgrade to Pro or make the repository public. Private branch-protection/ruleset support is therefore a plan-level blocker in the current account. Do not register a self-hosted runner until branch and trusted-workflow controls are resolved.

**Runner principle**
- Owner has authorized provision of access needed for the runner and execution lead.
- Access must be least-privilege and scoped to the MarketSage repository and designated data directories; blanket laptop or personal-account access is not required.
- Runner must execute only trusted reviewed workflows, not untrusted fork or arbitrary PR code.

## Decision template

### YYYY-MM-DD — Title

**Decision authority:** Owner / Delegated execution  
**Status:** Proposed / Approved / Rejected / Superseded

**Question:**  
**Decision:**  
**Reason/evidence:**  
**Scope affected:**  
**Capital-risk impact:**  
**Implementation PR/commit:**  
**Supersedes:** (if any)
