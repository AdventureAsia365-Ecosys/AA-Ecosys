# lumiguides.it.com — DNS parity before the Namecheap → Route 53 nameserver switch (AA-811, S237 D5)

Source: `dig` against the authoritative Namecheap servers `dns1/dns2.registrar-servers.com`, run 14/10/2026
(Claude Code, S237 lane infra item 1). Zone transfer (AXFR) is refused, so this list is **discovery, not an
export**. Before switching the nameservers, Nghiệp must open Namecheap → Domain List → lumiguides.it.com →
**Advanced DNS** and tick every row against the table below. Any row in Namecheap that is missing here must be
added to `local.dns_parity_records` in AA-CIS-Infra `accounts/aa365/dns.tf` (PR, CI apply) **before** the switch.

## Records found (all copied into `dns.tf`, TTL 1800 = Namecheap "Automatic", served as 1799)

| # | Name | Type | Value | Purpose / note |
|---|------|------|-------|----------------|
| 1 | `@` | MX | `10 mx.zoho.com` | Zoho Mail inbound |
| 2 | `@` | MX | `20 mx2.zoho.com` | Zoho Mail inbound |
| 3 | `@` | MX | `50 mx3.zoho.com` | Zoho Mail inbound |
| 4 | `@` | TXT | `v=spf1 include:zohomail.com ~all` | SPF (Zoho). Left as is: SES uses its own MAIL FROM sub-domain |
| 5 | `@` | TXT | `zoho-verification=zb55616719.zmverify.zoho.com` | Zoho domain verification |
| 6 | `zmail._domainkey` | TXT | `v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCRUfeh2HiNAjL8S3BM/504yuZp5PX26R8zInoJDzySIjJ4B6aORZYP2o3FZpE0wGGJ+5M6XDgwVk83nNy5HV3VVXQ+QEibpelTenSNu7XOPKs2hzDV1/kfCXwzv5hslYbQirihzK1A7+XlQBpqqdGExmV5rm7snvcUBXHDQ8lZuwIDAQAB` | Zoho DKIM (selector `zmail`) |
| 7 | `aa-cis` | CNAME | `91b6470228dd7980.vercel-dns-017.com` | CIS admin/portal on Vercel |
| 8 | `api-cis` | CNAME | `d-p5fej4ddcg.execute-api.us-west-1.amazonaws.com` | CIS REST API custom domain (API GW 4ylo382khg) |
| 9 | `_82696e885de42cd0cfe7589ce5cdb188.api-cis` | CNAME | `_ca529c9e2dbfc61a703e33210ed793c2.jkddzztszm.acm-validations.aws` | ACM DNS validation, api-cis cert (needed for auto-renewal, cert expires 22/01/2027) |
| 10 | `_664ff4fa710e6d329ff66f6cb3ac3a64.api-cis-aa365` | CNAME | `_db1334da60091d3dc3b933a7027f9942.jkddzztszm.acm-validations.aws` | ACM DNS validation, api-cis-aa365 cert (expires 21/01/2027) |
| 11 | `www` | CNAME | `aa-alb-prod-203362903.ap-southeast-1.elb.amazonaws.com` | **Legacy Quanskill ALB, target no longer resolves** (NXDOMAIN). Copied for parity |
| 12 | `api` | CNAME | `aa-alb-prod-203362903.ap-southeast-1.elb.amazonaws.com` | **Legacy, same dead target**. Copied for parity |

Checked and **absent** at Namecheap: apex A / AAAA / CAA / CNAME / SRV / HTTPS, `_dmarc`, DS (no DNSSEC — the
switch needs no DS removal), any wildcard (`*.lumiguides.it.com` → NXDOMAIN), `mail`, `webmail`, `autodiscover`,
`_vercel`, `_acme-challenge`, `_amazonses`, `default/google/selector1/selector2/k1/s1/zoho._domainkey`,
`tripplanner`, `api-booking`, `api-tripplanner`, `auth`, `staff-auth`, `api-cis-aa365`, and ~120 other common
names.

## New records Terraform adds with AA-811 (not at Namecheap today)

| Name | Type | Value | Purpose |
|------|------|-------|---------|
| `<token1..3>._domainkey` | CNAME ×3 | `<token>.dkim.amazonses.com` | SES Easy DKIM (tokens known after apply: output `ses_dns_records`) |
| `bounce` | MX | `10 feedback-smtp.us-west-1.amazonses.com` | SES custom MAIL FROM |
| `bounce` | TXT | `v=spf1 include:amazonses.com ~all` | SPF for the MAIL FROM sub-domain |
| `_dmarc` | TXT | `v=DMARC1; p=none; adkim=r; aspf=r` | DMARC monitor-only (add `rua=` via `ses_dmarc_rua_email` if a report mailbox is wanted) |

## Gaps and things to decide

1. **No AXFR**: a record with a name nobody guessed (e.g. a one-off TXT verification, a Namecheap "URL Redirect"
   row, a sub-domain only in someone's head) is not in this list. The Namecheap panel check is the only control.
2. **`api-cis-aa365.lumiguides.it.com`** has an API GW custom domain (`d-4fqcbk7uqk...`, managed by Terraform via
   `var.domain_name`) and an issued cert, but **no CNAME at Namecheap** — the name does not resolve today. Not
   added (parity = same behaviour). If it should resolve, add `api-cis-aa365 CNAME d-4fqcbk7uqk.execute-api.us-west-1.amazonaws.com`.
3. **`www` and `api`** point at the old Quanskill ALB in ap-southeast-1, which is gone. Copied so the switch
   changes nothing; deleting them (or pointing `www` at the TripPlanner site) is a separate decision.
4. **Apex A record**: none. ADR 0006 decision 10 says the Cognito custom domains (`auth.`, `staff-auth.`) need
   one on the parent — AA-703/AA-818 adds it to the Route 53 zone when the custom domains are created.
5. **Zoho**: after the switch, send one mail to and from a `@lumiguides.it.com` Zoho mailbox to prove MX/SPF/DKIM.

## Switch procedure (Nghiệp)

1. Merge + apply AA-811 (zone created; nothing served from it yet).
2. Tick every Namecheap row against the table above; add anything missing to `dns.tf` (PR → CI apply).
3. `terraform output lumiguides_zone_name_servers` (or the CI apply log) → Namecheap → Nameservers →
   **Custom DNS** → the four `ns-*.awsdns-*` values. Namecheap DNS records stop being served from then on.
4. After propagation (minutes to a few hours; parent TTL), from any machine:
   `dig +short NS lumiguides.it.com` (expect awsdns), `dig +short MX lumiguides.it.com`,
   `dig +short CNAME api-cis.lumiguides.it.com`, `curl -s -o /dev/null -w '%{http_code}' https://api-cis.lumiguides.it.com/health`,
   `curl -sI https://aa-cis.lumiguides.it.com`, and
   `aws sesv2 get-email-identity --email-identity lumiguides.it.com --profile aa365-admin --region us-west-1`
   until `DkimAttributes.Status = SUCCESS` and `MailFromAttributes.MailFromDomainStatus = SUCCESS`.
5. Rollback = set the nameservers back to Namecheap BasicDNS. Screenshot / export the Advanced DNS page before
   step 3, so the records can be re-entered if Namecheap does not keep them across the switch.
