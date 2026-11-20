# Decisions log

## 2026-11-15: Hosting (decided, **not ordered yet**)

The server will be ordered only once the application work is done, so no money is spent while it's being built. Measurements and price comparison are in [PHASE1-REPORT.md](PHASE1-REPORT.md).

| Item | Decision |
|---|---|
| Server | **Netcup VPS 1000 G12.5**: 4 shared vCPU (x86), 8 GB RAM, 128 GB SSD, IPv4 + IPv6 |
| Location | "No preference Europe". Latency differences between EU sites are 10–20 ms, so paying €1.56/month to choose isn't worth it. |
| Term and price | 24 months at **€10.35/month** (0% VAT shown at checkout), about €248 in total. Before ordering, check the auto-renewal and cancellation notice period, and expect possible ID verification for a new account. |
| Ruled out | **OVH VPS-2:** no stock in any region on 2026-11-15. **Hetzner:** CX/CAX are discontinued and CPX32 costs about $36/month. **Oracle Free:** cut to 12 GB, with idle-reclaim risk. **AWS:** €49+ for one box, and the existing 9× t2.micro would cost about €104 and can't hold Keycloak. **Scale-to-zero:** 2–4 minute cold starts for visitors. |
| Runtime profile | The slim demo profile measured at about 2.5 GB, with every microservice kept. Lean observability (Prometheus, Grafana, single-binary Loki) stays internal only. |
| Domain | A subdomain of the existing **firaskhalife.dev**, e.g. `demo.` or `grading.`. The domain is already on Cloudflare. No new domain will be bought. |
| Edge | **Cloudflare free plan**: a Tunnel to the server (no inbound ports except SSH), proxied DNS, managed WAF rules, and bot protection. Check that the portfolio's own DNS records are proxied (orange cloud) so it gets the same protection. |
| Visitor experience | Always on, with no cold start. The demo reset happens in place (wipe and reseed while services keep running), not with `down -v`. |
| Backups | None for data, since the demo resets by design. The server must be rebuildable from git (IaC plus seed data). |

## 2026-11-15: Order of work

1. **The application first**, as a product and as code:
   - What a visitor sees: a full frontend redesign and one-click demo login.
   - Backend improvements and new or better features.
   - Code quality across all repos for senior reviewers, including the Terraform repo, and possibly an AWS CDK version to show IaC range.
2. **Only then:** Docker and Compose cleanup, credentials, deployment, CI/CD (the choice between the existing Jenkinsfile and GitHub Actions is still open), and IaC for the Netcup host (check whether Netcup has an API or Terraform provider).

The repos **stay public**, so no secret is ever committed. The secrets already leaked will be replaced in the credentials phase.

## Open questions
- Whether Netcup can be managed as code (API or Terraform provider), or needs cloud-init plus Ansible.
- Whether to use Jenkins or GitHub Actions. The admin-service repo has a `Jenkinsfile` and the others have `add_*_pipeline` branches.
- Whether to add a student persona. The code currently has only the roles ADMIN, DEV, JURY and ADVISOR.
