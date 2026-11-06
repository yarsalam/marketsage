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
7. GitFlic (Russia) remains a research lead, not a selected provider. Available pricing and compatibility details found so far are from a third-party review, not yet independently confirmed against official current terms. Its own CI syntax appears different from GitHub Actions; verify official documentation before considering migration.
8. Never evade export controls, sanctions, account eligibility, geo-restrictions or provider terms through false identity, address, location, VPN spoofing, proxy accounts or another person's account. Check legal eligibility and provider terms before account creation or data transfer.

## Candidate matrix

| Candidate | Origin / operating model | Advertised free capacity | Main fit | Main blocker / decision |
|---|---|---:|---|---|
| Forgejo + Woodpecker | Open source, self-hosted | No hosted compute included | Preferred mature, replaceable self-hosted baseline | Needs owner-controlled compute; Woodpecker security boundaries and isolated backend must be configured |
| Gitea + Gitea Actions | Open source, self-hosted | No hosted compute included | Alternative forge and Actions-compatible runner | Needs owner-controlled compute; runner isolation and permissions require hardening |
| GitRiver Community | Russia, self-hosted binary-only | Community claims unlimited CI/storage because it uses our hardware | Disposable sandbox comparison only | Source code is not provided; reverse engineering restricted by license; vendor says no independent external security audit; do not trust with private code/secrets |
| Gitee Go | China, hosted, coupled to Gitee | Official page: 200 min/repository + 1,000 min/org/month | Potential external hosted worker for low-risk tasks | Must verify registration/access/terms; likely requires Gitee mirror; no code transfer without approval; quota and account state must be observed |
| Alibaba Cloud DevOps Flow | China, hosted | Official docs: 3,000 core-min/month; 20 GiB Git/LFS and 10 GiB artifacts | Technically capable CI candidate | Activation requires pay-as-you-go; exclude under USD 0 policy |
| GitFlic CE | Russia, self-hosted; SaaS also exists | Third-party review reports free CE | Potential integrated self-hosted alternative | Official terms/pricing and security posture not yet independently confirmed; own CI YAML likely requires workflow rewrite |
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
Current evidence found is a third-party review, not sufficient to select the service. It reports a free self-hosted Community Edition and a SaaS free tier for small teams, and notes a custom gitflic-ci.yaml syntax. Confirm every detail from official GitFlic documentation and license terms before relying on it.

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
- GitFlic third-party overview (lead only; not official confirmation): https://digital-atlas.ru/servisy/gitflic/
- Gitsi official terms, privacy and trust pages: https://www.gitsi.com/terms ; https://www.gitsi.com/privacy ; https://www.gitsi.com/trust
- Woodpecker security boundaries and architecture: https://woodpecker-ci.org/docs/usage/security-boundaries ; https://woodpecker-ci.org/docs/administration/general
- Forgejo Actions security guidance: https://forgejo.org/docs/latest/user/actions/security/