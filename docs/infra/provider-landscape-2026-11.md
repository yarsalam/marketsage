# Provider landscape research — 2026-11

**Status:** desk research only; no account registrations, repository exports, billing activation, CI dispatches, or installations performed.
**Cost ceiling:** USD 0. No paid trial, payment method, pay-as-you-go activation, overage, or VPS purchase is authorized.
**Scope:** identify legally usable, technically plausible CI / source-control options that may remain reachable when US/EU hosted CI services are unavailable.

## Executive decision

1. Keep the provider-neutral control plane and task contract as the core. Do not move the canonical repository or private source code to a new hosted provider during desk research.
2. The most credible no-subscription path is self-hosting on hardware already controlled by the owner: Forgejo or Gitea as the forge, with Woodpecker CI or Forgejo Actions as the execution engine. This still consumes electricity, storage, network and maintenance; it is not free compute.
3. Keep GitRiver Community (Russia) as a low-trust, disposable sandbox candidate only, not a shortlisted trusted platform. Its own site advertises an integrated Git forge and CI/CD, but its license says the software is distributed in object code and source code is not provided; reverse engineering is contractually restricted. Its security page states that no independent external audit has been conducted. Do not use it for private MarketSage code, secrets or trusted worker execution unless those material risks are resolved.
4. Gitee Go (China) is a hosted candidate for a later, low-risk reachability test only. Its official page advertises 200 free build minutes per repository and 1,000 per organization/month. It is integrated with Gitee's own forge; do not assume it can directly execute GitHub repository workflows. A mirror/import workflow would be needed, and private source code must not be copied without a separate explicit decision and legal/data review.
5. Exclude Alibaba Cloud DevOps Flow from the zero-cost shortlist for now. Although it advertises free monthly resource quotas (3,000 core-minutes, 20 GiB Git, 20 GiB LFS, 10 GiB artifacts), its region-based DevOps activation requires enabling pay-as-you-go billing. That creates a billing relationship and overage exposure inconsistent with the current zero-cost instruction. Do not activate it or create an organization.
6. Do not select Gitsi hosted alpha: its terms state manual private-alpha approval; its terms/privacy pages contain unfilled legal-entity/address/hosting-region placeholders. Do not upload any code or register pending clarification.
7. GitFlic (Russia) is a stronger follow-up candidate than initially assessed: official docs confirm a hosted free tier up to five company members, configurable CI/CD, external Docker runners and a self-hosted deployment path. Its self-hosted license/edition pricing and current eligibility for this user still need confirmation. Its CI config is not GitHub Actions-compatible by assumption; test a small YAML pipeline before migration.
8. Never evade export controls, sanctions, account eligibility, geo-restrictions or provider terms through false identity, address, location, VPN spoofing, proxy accounts or another person's account. Check legal eligibility and provider terms before account creation or data transfer.

## Candidate matrix

| Candidate | Origin / operating model | Advertised free capacity | Main fit | Main blocker / decision |
|---|---|---:|---|---|
| Forgejo + Woodpecker | Open source, self-hosted | No hosted compute included | Preferred mature, replaceable self-hosted baseline | Needs owner-controlled compute; Woodpecker security boundaries and isolated backend must be configured |
| Gitea + Gitea Actions | Open source, self-hosted | No hosted compute included | Alternative forge and Actions-compatible runner | Needs owner-controlled compute; runner isolation and permissions require hardening |
| GitRiver Community | Russia, self-hosted binary-only | Community claims unlimited CI/storage because it uses our hardware | Disposable sandbox comparison only | Source code is not provided; reverse engineering restricted by license; vendor says no independent external security audit; do not trust with private code/secrets |
| Gitee Go | China, hosted, coupled to Gitee | Official page: 200 min/repository + 1,000 min/org/month | Potential external hosted worker for low-risk tasks | Must verify registration/access/terms; likely requires Gitee mirror; no code transfer without approval; quota and account state must be observed |
| Alibaba Cloud DevOps Flow | China, hosted | Official docs: 3,000 core-min/month; 20 GiB Git/LFS and 10 GiB artifacts | Technically capable CI candidate | Activation requires pay-as-you-go; exclude under USD 0 policy |
| GitFlic | Russia, hosted SaaS + self-hosted distribution | Official docs: hosted company plan free up to 5 members; self-hosted Community terms need confirmation | Candidate hosted forge with owner-operated Docker runner, or self-hosted platform | Verify current legal eligibility/access and self-hosted CE license/price; Docker runner boundary and custom CI syntax need review |
| Gitsi | India, hosted private alpha | Advertises 200 org CI minutes/month on Free | Not suitable at present | Private alpha approval; legal entity and data hosting fields incomplete in published terms/privacy |
| CircleCI | US/EU hosted + self-hosted runners | Free plan credit allowance exists | Existing account may remain useful if login restored | User login session currently fails; no hosted execution until actual access and budget verified |
| Buildkite | Hosted + self-hosted agents | Current account is a time-limited trial | Secondary runner option | Trial is not durable free capacity; no pipeline creation until trial limits/terms verified |

## Evidence and caveats

### Gitee Go
Official product page: https://gitee.com/features/gitee-go

The official page describes Gitee Go as an integrated CI/CD service with visual and YAML pipelines, manual/automatic/scheduled triggers, parallel jobs, plugins, quality gates and deployment tasks. It explicitly advertises 200 free build minutes per repository and 1,000 free build minutes per organization per month.

The same page describes deep integration with Gitee code hosting. Therefore the working assumption is that a Gitee repository mirror/import will be required. This must be proven using a harmless public test repository before any private MarketSage content is considered. Confirm whether a GitHub webhook/import/sync is supported, how secrets are handled, where builds run, concurrency, artifact retention, quota exhaustion behavior, account eligibility, and data location.

### Alibaba Cloud DevOps Flow
Official billing page: https://www.alibabacloud.com/help/en/yunxiao/product-overview/billing-description-region-version

The page advertises 3,000 monthly build core-minutes, 20 GiB Git, 20 GiB LFS and 10 GiB artifact storage. However, the same documentation says the region-based product must activate pay-as-you-go before an organization can be created. It also publishes overage rates. It is not compatible with the strict zero-cost posture unless the provider later offers a mode that does not require billing activation and hard-stops at quota. Do not create an organization or activate billing.

### GitRiver Community
Official product page: https://gitriver.ru/ ; FAQ: https://gitriver.ru/faq ; Pricing: https://gitriver.ru/pricing ; Features: https://gitriver.ru/features

The vendor advertises a self-hosted Rust application, PostgreSQL, integrated Git hosting, CI/CD, OCI/package registries, tasks, merge requests, backup and notifications. Its FAQ states minimum requirements of 1 vCPU/256 MiB for the application and 2+ CPU/4+ GiB RAM with Docker for the built-in executor; production CI guidance is 8+ CPU/16+ GiB SSD. The site highlights version 1.1.0. CI uses its own YAML format under .gitriver/workflows/, so existing GitHub Actions workflows should not be assumed to work unchanged. Its published benchmark is vendor-produced and only covers a subset of scenarios. More importantly, the license explicitly says the program is distributed as object code and source code is not provided, and restricts reverse engineering. Its security page states that an independent external audit has not yet been conducted (it reports only its own OWASP ASVS L2 review). These are material supply-chain and assurance gaps for a financial research project; do not treat GitRiver as a trusted production runner or place private code/secrets in it.

Before even a disposable test: review the license and jurisdiction; request the full third-party component list, SBOM, release verification method and security review report; confirm the security support window and isolated runner design. Given the binary-only distribution and lack of independent audit, keep it below Forgejo/Woodpecker in priority. If tested at all, use a disposable public repository in a fully isolated VM with no secrets, no private network access and no host mounts. Do not connect the MarketSage private repository or production secrets.

### GitFlic
Official GitFlic docs confirm the cloud service is free for companies up to five members, and that CI/CD agents can be registered at company level and run with Docker. The application minimum requirements are 2 CPU cores, 4 GiB RAM and at least 25 GiB disk, with Java 17, Redis and PostgreSQL. The runner documentation instructs creating a dedicated runner user and adding it to the Docker group; that grants powerful Docker-host access and requires an isolated disposable VM, not a shared laptop/production host. The docs include a self-hosted distribution and separate PRO/Enterprise license activation, but the exact no-cost Community terms for the self-hosted edition still need official confirmation. Hosted SaaS is a candidate only after terms, access, jurisdiction and data location are checked; do not upload private code yet.

### Huawei Cloud CodeArts (China)
Official documentation describes a Free package with up to 1,800 pipeline execution minutes/month and 300 minutes/month of resource-consuming pipeline tasks in one specification. Other billing documentation says CodeArts uses pay-per-use billing and free quota is granted after enabling pay-per-use; another guide describes enabling the Free Edition. The plan is time-limited in some regions and account setup may require regional eligibility. This ambiguity and possible pay-per-use activation mean it is not accepted under the strict USD 0 rule until a no-billing activation path and hard quota stop are confirmed in the actual account. Do not enable pay-per-use or buy resources. Sources: https://support.huaweicloud.com/intl/en-us/price-devcloud/codearts_29_0006.html ; https://support.huaweicloud.com/intl/en-us/ally-visitor-1-usermanual-codearts/codearts_07_0005.html

### Gitsi
Official pages: https://www.gitsi.com/terms ; https://www.gitsi.com/privacy ; https://www.gitsi.com/trust ; https://www.gitsi.com/pricing

The published terms describe private alpha and manual account approval. Several legal identity, registered office and data-hosting fields are placeholders. Reject hosted use until these are complete and independently verifiable.

## Proposed technical direction

### Phase A — no-cost local proof, no private code transfer
- Keep GitHub as the current canonical source while access remains available; no forced migration.
- Evaluate Forgejo + Woodpecker as the baseline independent forge/CI pair.
- Evaluate GitRiver Community as a separate, disposable local prototype, not a production choice.
- Use a disposable public repository and non-sensitive sample code.
- Run the CI engine in a container/VM isolated from the host; never use a host-mode runner for untrusted PR code.
- Do not run workers on the yarsalam production VPS.
- The owner's laptop may be used only for an explicitly on-demand experiment; it is not a 24/7 service.
- If no suitable non-production host exists, stop before installation and continue with portable manifests, security review and documentation.

### Phase B — external provider reachability test
Only after Phase A's test design is ready and the owner chooses to test an external account:
1. Confirm provider terms allow the user's actual country, entity and use case.
2. Check registration and login without proxy/location/identity workarounds.
3. Use a new public dummy repository with no MarketSage source, secrets, data or identifying private details.
4. Verify manual trigger first; do not enable automatic triggers.
5. Check quota, concurrency, logs, retention, artifact handling, cancellation and quota-exhaustion behavior.
6. Confirm the provider hard-stops at free quota without automatic overage or billing activation.
7. Record only sanitized evidence. A provider is not accepted until a complete run and a failure/recovery test pass.

### Phase C — private code consideration (separate approval required)
Do not mirror or upload the private MarketSage repository to Gitee, GitFlic, GitRiver-hosted SaaS, Gitsi or any third party without explicit approval after reviewing jurisdiction, data location, access controls, deletion/export, incident handling, and secret isolation. Self-hosted software installed on an owner-controlled machine is a different risk profile from hosted source-code storage.

## Acceptance checklist
- [ ] Actual access from the user's normal permitted network and account verified.
- [ ] Official terms, operator identity, legal eligibility and data locations reviewed.
- [ ] No payment method, paid trial, pay-as-you-go activation or overage exposure.
- [ ] Dummy public repository only; no private MarketSage code or secrets.
- [ ] Manual execution works; automatic triggers remain disabled initially.
- [ ] Free quota and concurrency confirmed in the account UI.
- [ ] Quota exhaustion stops safely without paid fallback.
- [ ] Logs and artifacts are sanitized; no secret leakage.
- [ ] Worker isolation and host boundary tested.
- [ ] Failure classification, cancellation, duplicate delivery and safe recovery tested.
- [ ] Evidence stored in the provider-neutral control plane.
- [ ] Owner approval recorded before any private repository connection or production-like use.

## Sources checked on 2026-11-06
- Gitee Go official product page: https://gitee.com/features/gitee-go
- Alibaba Cloud DevOps billing: https://www.alibabacloud.com/help/en/yunxiao/product-overview/billing-description-region-version
- GitRiver official site, FAQ, pricing, features, license and security disclosure: https://gitriver.ru/ ; https://gitriver.ru/faq ; https://gitriver.ru/pricing ; https://gitriver.ru/features ; https://gitriver.ru/license ; https://gitriver.ru/docs/security
- GitFlic official documentation (billing, runner and minimum requirements): https://docs.gitflic.ru/latest/company/billing_for_company/ ; https://docs.gitflic.ru/latest/cicd/agent/ ; https://docs.gitflic.ru/latest/setup/runner/installdocker/ ; https://docs.gitflic.ru/latest/setup/gitflic_app/min_req/
- Huawei Cloud CodeArts official billing and package specifications: https://support.huaweicloud.com/intl/en-us/ally-visitor-1-usermanual-codearts/codearts_07_0005.html ; https://support.huaweicloud.com/intl/en-us/price-devcloud/codearts_29_0006.html
- Gitsi official terms, privacy and trust pages: https://www.gitsi.com/terms ; https://www.gitsi.com/privacy ; https://www.gitsi.com/trust
- Woodpecker security boundaries and architecture: https://woodpecker-ci.org/docs/usage/security-boundaries ; https://woodpecker-ci.org/docs/administration/general
- Forgejo Actions security guidance: https://forgejo.org/docs/latest/user/actions/security/
## Existing GitHub workflow audit (read-only)

Files inspected on the infrastructure branch:

- `.github/workflows/ci.yml`: automatic `push` triggers for `main`, `deploy/**`, `research/**`, `ci/**`; automatic `pull_request` triggers targeting `main` and `deploy/**`. It uses hosted `ubuntu-latest`, installs dependencies, runs tests/builds and builds production images. No secrets are declared in the inspected workflow. Do not open a PR targeting `main` or `deploy/**` while hosted Actions remains blocked unless a controlled test is explicitly authorized; a PR event would request a run even though current Actions quota is exhausted.
- `.github/workflows/local-tsetmc-integrated-acceptance.yml`, `.github/workflows/local-tsetmc-offline-acceptance.yml`, `.github/workflows/local-tsetmc-sanitized-diagnostics.yml`: manual `workflow_dispatch` only, explicit boolean confirmation, restricted to `main` and actor `yarsalam`, self-hosted labels, `contents: read`, no secrets, no artifact upload and no production action. The integrated workflow pins both checkout actions and the pipeline commit. These workflows are deliberately excluded from provider migration until infrastructure gates are proven.
- The new branch name `infra/provider-neutral-control-plane-2026-11` is not included in the current `ci.yml` push branch filters, so ordinary pushes to this branch should not match that workflow. No workflow was dispatched and no PR was opened.

Do not confuse a workflow definition with evidence of an execution. This audit is static only; no runner availability or workflow correctness is asserted.

## Provider revalidation — 2026-11-07 (official pricing and limits)

This section supersedes any earlier shorthand in the candidate matrix where current public pricing pages provide more precise numbers. It is still desk research: no accounts were connected, no private code was transferred, and no build was started.

### Hosted execution candidates

| Provider | Current public Free allowance | Interpretation for MarketSage | Current decision |
|---|---|---|---|
| CircleCI | Free plan: up to 6,000 build minutes on the small Docker resource class, 30,000 credits/month, 5 active users, up to 30x concurrency; no credit card required. Private repositories use the normal 30,000-credit allowance, not the larger open-source allowance. | Best first hosted fallback to test with a disposable public repository. Credits are resource-class-dependent; do not equate all job minutes with small-Docker minutes. Verify actual account access and hard-stop behavior before relying on it. | Candidate A; account login/access and quota exhaustion behavior still unverified. |
| Buildkite | Free plan: up to 5 users, 10 concurrent self-hosted jobs, 2,000 Linux AMD64 vCPU-minutes/month on the small hosted shape, and up to 250k test executions/month. The small hosted shape is 2 vCPU, so 2,000 vCPU-minutes is not 2,000 ordinary wall-clock build minutes. | Strong secondary hosted pool plus a useful self-hosted-agent control plane. Separate the 30-day all-access trial from the ongoing Free-plan allowance. Verify the actual account's post-trial state and hard-stop behavior. | Candidate B; do not treat the trial as permanent capacity. |
| GitLab.com Free | 400 compute minutes/month for Free namespaces on GitLab-hosted instance runners; usage resets monthly. | Good independent forge/CI fallback for a small set of high-value checks. Self-managed runners still require owner-controlled compute; do not assume they create free compute. | Candidate C; public dummy-repository test first. |
| Gitee Go | Official Gitee product page advertises 200 free build minutes per repository and 1,000 per organization/month. | Potential additional quota, but deeply integrated with Gitee hosting. Requires a disposable public Gitee repository and a separate review of terms, account eligibility, region, webhooks, quota-stop and artifact handling. | Candidate D; no MarketSage private-code mirror or upload without separate approval. |
| GitFlic hosted | Official documentation says companies with up to five members can use gitflic.ru without charge; CI/CD agents can be registered and Docker agents are supported. | Potential additional independent route, but legal eligibility, jurisdiction, data location, hosted limits and the trust boundary of Docker agents must be checked. | Candidate E; no private-code transfer before explicit approval and legal review. |

### Lightweight external control plane candidate

Cloudflare Workers Free is not a build runner. It can, however, be evaluated as a lightweight independent webhook/heartbeat/status endpoint:

- Workers Free: 100,000 requests/day, 10 ms CPU per invocation and 128 MB memory.
- D1 Free: 5 million rows read/day, 100,000 rows written/day and 5 GB total storage.
- Queues Free: 10,000 operations/day; message retention is only 24 hours on the Free plan.
- Queue consumers have a 15-minute wall-clock ceiling, but the Free Workers CPU limit remains very small; this is not suitable for running tests or building containers.

Possible role: a thin external observer and wake-up channel, with D1 as the durable task ledger and Queue messages treated only as disposable wake-ups. The ledger must be able to reconstruct work after a Queue message expires. Keep records minimal and sanitized; review data location and terms before storing even private task metadata. This does not replace a compute worker or provide an always-on VPS.

### Compute VM candidate — Google Cloud Free Tier

Google Cloud documents one non-preemptible e2-micro VM per month in selected US regions, 30 GB-months of standard persistent disk and 1 GB/month outbound transfer. A billing account is required. The new-customer Free Trial gives USD 300 for 90 days and says no Google Cloud usage is billed during that trial; after upgrading to a paid billing account, usage beyond Free Tier limits is billable.

The e2-micro is too small to be the primary MarketSage build worker, and the US-only region plus 1 GB egress limit make it a poor fit for repeated dependency-heavy builds. Do not create/upgrade a paid billing account or deploy resources under the current USD 0 ceiling. At most, reconsider it later for a very small external monitor after a separate hard-cost-control review.

### Orchestration engine — Temporal

Temporal Cloud currently advertises USD 150 in introductory credits for 90 days and usage-based pricing thereafter (including metered actions and storage); it is not a permanent free hosted control plane. Temporal OSS is self-hostable, but requires a continuously available service and persistence infrastructure. Keep it as a future engineering option, not as the current zero-cost hosted dependency. The present small coordinator prototype should first prove its manifest/lifecycle contracts and clean-checkout tests.

### Revised implementation choice

1. Keep GitHub as canonical source for now; do not mirror private code to another forge.
2. Use CircleCI Free and Buildkite Free as the first two hosted-provider candidates, but test only with a disposable public repository until the owner separately approves private-repository integration.
3. Evaluate GitLab.com Free as a third hosted CI option; use its 400-minute pool selectively.
4. Evaluate Cloudflare Workers + D1 + Queues only for independent heartbeat/webhook/task-state metadata, never for compilation or tests.
5. Keep Forgejo + Woodpecker as the self-hosted, replaceable worker stack when an isolated host exists. The owner's laptop remains on-demand only; Oracle signup is blocked by the provider's compliance response and must not be bypassed.
6. Route work by measured eligibility and actual remaining quota. A missing quota API, trial credit, free-tier marketing claim or successful login is not proof that a task can run at zero cost. Stop before any overage, paid upgrade, card charge or private-code transfer.

### Official sources checked on 2026-11-07

- CircleCI Free pricing: https://circleci.com/pricing/
- Buildkite Free pricing and agent limits: https://buildkite.com/pricing/
- GitLab compute minutes: https://docs.gitlab.com/ci/pipelines/compute_minutes/
- Gitee Go product and advertised quotas: https://gitee.com/features/gitee-go
- GitFlic company billing and CI/CD agents: https://docs.gitflic.ru/latest/company/billing_for_company/ ; https://docs.gitflic.ru/latest/cicd/agent/ ; https://docs.gitflic.ru/latest/en/setup/runner/agent_types/
- Cloudflare Workers limits/pricing: https://developers.cloudflare.com/workers/platform/limits/ ; https://developers.cloudflare.com/workers/platform/pricing/
- Cloudflare D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- Cloudflare Queues pricing/limits: https://developers.cloudflare.com/queues/platform/pricing/ ; https://developers.cloudflare.com/queues/platform/limits/
- Google Cloud Free Tier: https://docs.cloud.google.com/free/docs/free-cloud-features
- Temporal Cloud pricing: https://temporal.io/pricing
