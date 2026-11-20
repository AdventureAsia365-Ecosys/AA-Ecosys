# AA-1168 live verification: EU AI Act Art. 50(2) marks and disclosure (S286)

Run: 2026-11-20, about 01:30 to 01:50 UTC, by a Claude Code subagent. Cost: $0. There was no model call and no paid run.
Under test: CIS #1619 `daec5413` (api + worker), AA-Partner #369 `b163d81a` (web), root #917 (AI Use Register v1.15).

The identity was the E2E owner of the synthetic agency `pilot-rehearsal-01` ("E2E Pilot Rehearsal Travel"). The
session came from the saved UAT state (`tools/uat/lib/signin.cjs`, identity `studio-rehearsal`). Both test channels
were already connected and verified on this agency.

Two pieces were used. Both were already written and ready, so nothing was generated:

- blog `7e07c0c0-9e9e-4a64-a76f-7bfc228afa24`
- facebook `eed54407-6b52-47ee-a7bf-59f3f071b55d`

All calls went through the product's own BFF (`/api/tenant/v1/*` to CIS `/v1/*`). The channel secrets
(`aa-cis/dev/e2e-wordpress-test`, `aa-cis/dev/e2e-facebook-test`) were read in memory by
`lib/rehearsal.cjs channelCreds()` and were never printed. This file holds no tokens and no Page id.

| # | Check | Result |
|---|-------|--------|
| 1 | WordPress post: `<article data-ai-generated="true">`, the `ai-disclosure` paragraph ends the article, then unpublish | **PASS** |
| 2 | Facebook post message ends with the disclosure and `#AIgenerated`, then delete | **PASS** |
| 3 | Plain-text export: `---`, the disclosure line, an `AI-Content:` line, and the `X-AI-Generated: true` header | **PASS** |
| 4 | My Content CSV has the four AI columns and ends with the disclosure | **PASS** (Playwright UI download) |

## 1. WordPress: PASS

- Test site `GET /wp-json/` answered 200 `application/json; charset=UTF-8`. The site is up and is no longer a TasteWP
  host.
- `POST /api/tenant/v1/publish-log/7e07c0c0…/publish` answered 200 with `success: true` and `replayed: false`.
  - The response keys were `publish_id, success, status, external_id, external_url, published_at, last_error,
    replayed`.
  - publish_id: `8d78c7f5-769a-482d-984f-539d2d7d622d`
  - WordPress post id: 4
- `GET /wp-json/wp/v2/posts/4?context=edit` (Application Password auth) answered 200 with `status: publish`.
  `content.raw` contained:
  - The opening tag `<article data-ai-generated="true" data-ai-generator="Adventure Asia Content studio" data-ai-model="sonnet-5-5" data-ai-generated-at="2026-11-13T13:48:04.302437+00:00" data-ai-human-edited="true">`.
  - The last element inside the article: `<p class="ai-disclosure" data-ai-disclosure="true"><em>This content was created with the help of AI.</em></p>\n</article>`.
  - After `</article>`, the `<meta name="ai-generated" …>`, `ai-generator`, `ai-model`, `ai-generated-at`,
    `ai-human-edited` and `digital-source-type` (IPTC `trainedAlgorithmicMedia`) tags. These come from the earlier
    AA-1040 marking.
- `meta` shows `{"footnotes": ""}` only. The `ai_*` post meta that CIS sends is not stored because this test site has
  not registered those keys. The PR body says WordPress stores them only on sites that register them, so this matches
  the design and is not a defect.
- On the public post page, the HTML carries the `<article>` mark and the disclosure text. Screenshot
  `aa1168-01-wordpress-post-disclosure.png` shows the bottom of the article, with the disclosure outlined in red. No
  byline was on screen.
- Unpublish: `DELETE /api/tenant/v1/publish-log/8d78c7f5…` answered 200.
  - The publish-log row is `unpublished` with `unpublished_at` set, and the piece has no live row.
  - WordPress `context=edit` shows `status: trash`. The public `GET /wp-json/wp/v2/posts/4` answers 401, so the post is
    not public.
  - The site's published list holds only the default "Hello world" post. Post 4 is in the trash only.

## 2. Facebook: PASS

- A Graph `/me` check with the stored Page token returned 200, so the token is valid and belongs to the stored Page.
- `POST /api/tenant/v1/publish-log/eed54407…/publish` answered 200 with `success: true`, `replayed: false` and
  `last_error: null`. publish_id: `84054a87-f054-451e-b5ad-3011bf70a833`.
- Graph `GET /{post_id}?fields=message` answered 200. The message is 1409 characters and ends exactly with
  `"\n\nThis content was created with the help of AI. #AIgenerated"`. The last 90 characters are
  `"…to plan this journey with you.\n\nThis content was created with the help of AI. #AIgenerated"`.
- Delete: `DELETE /api/tenant/v1/publish-log/84054a87…` answered 200.
  - The publish-log row is `unpublished` with `unpublished_at` set.
  - Graph `GET /{post_id}` now answers 400 (OAuthException code 10). The post is no longer readable.
  - `/{page}/published_posts` lists only four 2017 posts. None carries `#AIgenerated` or this piece's text, so the
    test post is gone.
- No screenshot of the post was taken because the Page is the tech lead's personal Page. The Graph read-back above is
  the evidence.

## 3. Plain-text export: PASS

`GET /api/tenant/v1/content-writing/pieces/{id}/export?format=text` was called as the E2E tenant for both pieces. Both
answered 200 with `content-type: text/plain; charset=utf-8` and the headers `X-AI-Generated: true`,
`X-AI-Generator: Adventure Asia Content studio` and `X-AI-Model: sonnet-5-5`.

The last lines of the blog piece:

```
---
This content was created with the help of AI.
AI-Content: ai-generated=true; ai-generator=Adventure Asia Content studio; ai-model=sonnet-5-5; ai-generated-at=2026-11-13T13:48:04.302437+00:00; ai-human-edited=true; digital-source-type=http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia
```

The facebook piece has the same trailer, with `ai-human-edited=false` and its own `ai-generated-at`.

## 4. My Content CSV export: PASS (Playwright, the real UI download)

- The test opened `https://portal.lumiguides.it.com/portal/tours/mine` (My Tours, CatalogTab), selected two rows and
  clicked the bulk **CSV (2)** button. The browser downloaded `my-catalog.csv`.
- The page was guarded read-only: any non-GET under `/api/` was aborted. The only requests aborted were three Sentry
  envelope posts. There was no app write.
- The header is `Name, Subtitle, Country, Duration, SEO Title, SEO Meta, Summary, Highlights, Itineraries, Created At,
  Language, AI generated, AI generator, AI generated at, AI human edited`. The eleven old columns keep their order, and
  the four AI columns come last.
- Both rows hold `AI generated=true`, `AI generator=Adventure Asia Content studio`, an ISO `AI generated at`, and
  `AI human edited=false`.
- The last line of the file is `This content was created with the help of AI.`.
- Screenshots:
  - `aa1168-02-my-content-csv-button.png`: the bulk bar, with the CSV (2) button outlined.
  - `aa1168-03-my-catalog-csv-columns.png`: the downloaded file's header and rows (long text cut for the shot) and the
    disclosure line, with the AI columns highlighted.
- The XLSX export was not opened in this run.

## Cleanup and end state

- The pilot-rehearsal-01 publish log has 10 rows and 0 `published`.
- Both pieces are back in Ready to Publish (`GET /v1/publish-log/pending`).
- The WordPress and Facebook connections are untouched: still connected, with no verify error.
- Nothing is left live on the test WordPress site or the test Page.

Screenshots were compressed with `tools/docs/compress_images.py` (19, 34 and 44 KiB).
