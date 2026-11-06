// The studio-audit identity of the UAT write scenarios (AA-855 round 1, W-01..W-04): the partner E2E person who is an
// EDITOR in the four synthetic audit tenants of the T-series audit (kind demo, invented brands; S270). One run works on
// exactly ONE of them: env UAT_STUDIO_TENANT names its slug (default audit-atlas-hearth). Any other value throws, so a
// typo never reaches a real tenant; the pilot guard (lib/pilot-guard.cjs scopesFor) pins every studio-audit scenario to
// that slug, and lib/signin.cjs opens the studio on it by its invented display name.
//   UAT_STUDIO_TENANT=audit-trail-pulse node tools/uat/dryrun.cjs --record W-02 --allow-paid
// Secret (read at run time with the aws CLI, never printed): crm/dev/e2e-test-crm/harbour-lights-owner
// (UAT_STUDIO_AUDIT_SECRET overrides). Pure: no browser, no network.
'use strict';

const DEFAULT_SLUG = 'audit-atlas-hearth';
const SECRET = 'crm/dev/e2e-test-crm/harbour-lights-owner';
// Slug -> the tenant's invented display name (the studio chooser and GET /api/tenant/me show it). Same names as the
// pilot guard's built-in allow-list.
const AUDIT_TENANTS = {
  'audit-atlas-hearth': 'Atlas & Hearth (Audit)',
  'audit-terra-family': 'Terra Family Expeditions (Audit)',
  'audit-trail-pulse': 'Trail Pulse (Audit)',
  'audit-wildkind-travel': 'WildKind Travel (Audit)',
};

/** { slug, name } of this run's audit tenant. Throws for anything that is not one of the four audit slugs. */
function auditTenant(env = process.env) {
  const slug = (env.UAT_STUDIO_TENANT || DEFAULT_SLUG).trim();
  if (!Object.hasOwn(AUDIT_TENANTS, slug)) {
    throw new Error(`UAT_STUDIO_TENANT must be one of ${Object.keys(AUDIT_TENANTS).join(', ')} (got another value)`);
  }
  return { slug, name: AUDIT_TENANTS[slug] };
}

function secretId(env = process.env) {
  return env.UAT_STUDIO_AUDIT_SECRET || SECRET;
}

module.exports = { DEFAULT_SLUG, SECRET, AUDIT_TENANTS, auditTenant, secretId };
