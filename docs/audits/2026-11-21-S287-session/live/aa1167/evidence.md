---
id: OPS-08-s287-aa1167-live-evidence
title: "S287 live evidence: AA-1167 allow-list HTML sanitizer on the WordPress publish path"
description: "Agent-run live check on Dev, 21/11/2026: one test post with script, iframe, on* handlers and javascript: links published to the test WordPress site through the CIS publish route, read back, taken down; HTML exports checked."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-21
review_every_days: 30
related: [AA-1167]
---

# AA-1167 live check: HTML sanitizer on publish (S287)

Run: 2026-11-21, 08:28 to 08:29 UTC, by a Claude Code subagent. Cost: 0 USD. There was no model call.
Under test: CIS #1634 `350353eb` (api `/health/ready`: git_sha `350353eb`, schema_version `468`).

Identity: the E2E owner of the synthetic agency `pilot-rehearsal-01` (saved UAT state `studio-rehearsal`, still valid,
so no new sign-in code was needed). Every write went through the product's own BFF (`/api/tenant/v1/*` to CIS `/v1/*`).
The WordPress test-site credentials were used only by CIS inside its publish route. This run never read the secret.
The site was read back with public, unauthenticated GETs only. This file holds no site host, token or Page id.

Piece used: blog `7e07c0c0-9e9e-4a64-a76f-7bfc228afa24`. This is the same Ready-to-Publish piece S286 used for AA-1168.
Its original text (5035 characters, sha256 prefix `8661f6bcf547`) has no raw `<script>`, `<iframe>` or `on*=` markup.

Writes, five in all:

1. `PATCH .../content-writing/pieces/{id}` saved the test block ahead of the original text.
2. `POST .../publish-log/{id}/publish` published the post.
3. `DELETE .../publish-log/{publish_id}` took the post down.
4. A second `PATCH` put the original text back.
5. The edit records a tenant writing signal for this synthetic agency (AA-916). It is a DB row with no model call.

Raw numbers: `aa1167-result.json`.

## Test block (Markdown, as the tenant edit saved it)

```markdown
## Sanitizer check heading (aa1167-h2)

A normal paragraph with **bold text** and a [normal link](https://en.wikipedia.org/wiki/Forbidden_City) (aa1167-normal-link).

<script>window.aa1167 = "aa1167-script-body";</script>

<iframe src="https://example.com/aa1167-iframe-src" width="300" height="200"></iframe>

<p onclick="alert('aa1167-onclick-attr')">Paragraph that carried a click handler (aa1167-onclick-text).</p>

[Markdown link with a script URL (aa1167-js-md-text)](javascript:alert(1))

<a href="javascript:alert(2)" onmouseover="alert('aa1167-onmouseover-attr')">Raw link with a script URL (aa1167-js-raw-text)</a>

- First list item (aa1167-li-1)
- Second list item with a [link](https://en.wikipedia.org/wiki/Beijing) (aa1167-li-2)

1. Ordered item one (aa1167-ol-1)
2. Ordered item two (aa1167-ol-2)

### Sub heading (aa1167-h3)

End of the sanitizer check block (aa1167-end).
```

## Results

| # | Done-when item | Result |
|---|---|---|
| 1 | The test post publishes to the test WordPress site through the CIS publish route | **PASS**: `POST /publish` 200, `success: true`, `status: published`, `replayed: false`, `last_error: null`, WordPress post id 4 |
| 2 | Read back (WP REST GET): no `<script>`, no `<iframe>`, no `on*=` attribute, no `javascript:` URL | **PASS**: public `GET /wp-json/wp/v2/posts/4` 200, `status: publish`. `content.rendered` (6842 characters) has no script tag or script text, no iframe tag or src, no `on*=` attribute or handler value, and no `javascript:` |
| 3 | Normal markup survives | **PASS**: h2, h3, `<strong>`, both Wikipedia links with their `href`, the `<ul>` items, and the text of the handler paragraph and both script-URL links (now `<a>` with no `href`) |
| 4 | The live post page runs nothing from the piece | **PASS**: the `<article data-ai-generated="true">` on the public page has no script, iframe, `on*` or `javascript:`. `window.aa1167` is undefined |
| 5 | Screenshot of the published post | **PASS**: `aa1167-01-wordpress-post-sanitized.png` (51 KiB). The test block is outlined in red and no byline is on screen |
| 6 | Take-down (as S286) | **PASS**: `DELETE /publish-log/6e9b686e-…` 200. The row is `unpublished` with `unpublished_at` set. The public `GET /wp-json/wp/v2/posts/4` now answers 401 (trashed, not public) |
| 7 | HTML export (fragment) of an existing Dev blog piece: no script, iframe or `on*` | **PASS**: the original text gave `export?format=html&mode=fragment` 200 (6012 characters). It starts with `<article`, and the only tags are `a, article, br, em, h2, meta, p, strong`. There is no script, iframe, `on*=` or `javascript:` |
| 8 | End state restored | **PASS**: the text equals the original again (PATCH 200). The piece is `ready` and back in Ready to Publish. The publish log has 12 rows and 0 `published` |

### Who removed the markup: CIS, not WordPress

WordPress can filter post HTML itself (kses), so a clean read-back alone would not prove the CIS sanitizer works. The
same edited text was therefore exported from CIS before the publish. The export reads the same
`render_markdown_body()` render as the WordPress body:

- **fragment** export, 200: none of the dangerous markup, and every survivor of item 3. The excerpt is below.
- **document** export, 200: none of the dangerous markup.
- **plain-text** export, 200: no tag before the disclosure trailer and no `javascript:`. The heading text and the
  paragraph text are kept.

The CIS fragment and the WordPress `content.rendered` hold the same markup for the test block. CIS sent the clean HTML,
and WordPress did not have to strip anything.

The test block as CIS rendered it (fragment export; WordPress shows the same):

```html
<h2>Sanitizer check heading (aa1167-h2)</h2>
<p>A normal paragraph with <strong>bold text</strong> and a <a href="https://en.wikipedia.org/wiki/Forbidden_City">normal link</a> (aa1167-normal-link).</p>
<p>Paragraph that carried a click handler (aa1167-onclick-text).</p>
<p><a>Markdown link with a script URL (aa1167-js-md-text)</a></p>
<p><a>Raw link with a script URL (aa1167-js-raw-text)</a></p>
<ul>
<li>First list item (aa1167-li-1)</li>
<li>
<p>Second list item with a <a href="https://en.wikipedia.org/wiki/Beijing">link</a> (aa1167-li-2)</p>
</li>
<li>
<p>Ordered item one (aa1167-ol-1)</p>
</li>
<li>Ordered item two (aa1167-ol-2)</li>
</ul>
<h3>Sub heading (aa1167-h3)</h3>
<p>End of the sanitizer check block (aa1167-end).</p>
```

## Notes

- The `<script>` and `<iframe>` were dropped together with their content, so the script text and the iframe src are gone
  too. The `onclick` and `onmouseover` attributes were dropped. Their elements and visible text stayed. Both
  `javascript:` hrefs were removed, and the link text stayed as an `<a>` with no `href`.
- The numbered list came out as items of the bullet list above it. Python-Markdown joins a numbered list that follows a
  bullet list directly, and it did so before the sanitizer ran; the sanitizer did not cause it. `ol` is on the
  allow-list, and the unit tests in `tests/unit/test_aa1167_html_sanitizer.py` cover it. Not a defect of AA-1167.
- WordPress reused post id 4, the post S286 had trashed. The publish answered `replayed: false`, which means a new
  publish-log row (`6e9b686e-08e9-47ff-99da-d2d86946531f`). After the take-down, post 4 is back in the trash.
- The two edits and the publish wrote audit rows, writing-signal rows and a publish-log row for the synthetic agency
  only. No other agency was touched.
- Not checked in this run:
  - Facebook. The sanitizer's plain-text path covers the message, and the plain-text export above shows it.
  - The WordPress title and meta, which were not given markup in this test.
  - The agency portal preview (AA-Partner, a follow-up named in the PR).
