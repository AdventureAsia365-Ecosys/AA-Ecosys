---
identifier: "AA-7"
title: "Legacy image migration → S3 + CloudFront CDN"
state: "Canceled"
state_type: "canceled"
project: null
parent: null
labels: []
priority: 2
assignee: null
creator: "nghiep pham quoc"
created_at: "2026-05-06T09:25:39.301Z"
started_at: null
completed_at: null
canceled_at: "2026-08-21T09:26:58.006Z"
updated_at: "2026-08-21T09:26:58.025Z"
trashed: false
url: "https://linear.app/aa-ecosys/issue/AA-7/legacy-image-migration-s3-cloudfront-cdn"
---

# AA-7 — Legacy image migration → S3 + CloudFront CDN

# Legacy Image Migration → S3 + CloudFront CDN

## Why URGENT 🔴

Legacy images nằm trên old server filesystem (`disk='public'`, `path='uploads/tours/...'`).
Nếu server cũ tắt hoặc hosting hết hạn → **mất toàn bộ ảnh vĩnh viễn**.
Must be done BEFORE any DB migration.

## Legacy Structure (from backup.sql)

* `files` table: `disk='public'`, `path='uploads/tours/[hashed_name].jpg'`
* `entity_files`: maps file_id → entity (Tour / Itinerary / Country), zone='images'
* Ảnh live tại: `https://adventure.asia/storage/uploads/tours/[filename].jpg`
* \~2000+ entity_file records, hundreds of unique image files

## 7-Step Migration Plan

1. Create S3 Bucket: `aa-prod-media-007050358335` (block all public access, ap-southeast-1)
2. Setup CloudFront distribution: `cdn.adventure.asia` → S3 with OAC (Origin Access Control)
3. Write Python script to download all images from `adventure.asia/storage/` using backup.sql entries
4. Upload to S3 with prefixes:
   * `legacy/tours/` — Tour entity images
   * `legacy/itineraries/` — Itinerary images
   * `legacy/countries/` — Country cover images
5. INSERT into new `files` table: s3_bucket, s3_key, entity_type, entity_id, zone
6. Update old website config: redirect `adventure.asia/storage/` → `cdn.adventure.asia/legacy/` (HTTP 301)
7. Verify 20 sample images across all entity types via CDN URL

## files Table Convention (locked)

* Store: `s3_key` (relative path) NOT full URL
* API generates: `cdn_url = 'https://cdn.adventure.asia' + '/' + s3_key` at response time
* Example: `s3_key = 'legacy/tours/uk9Vh94qQFaVcSgazkUAnumnvXObPcuo7sAHzArk.jpg'`

## S3 Folder Structure (new uploads going forward)

* `uploads/countries/{country_slug}/` — hero + gallery
* `uploads/destinations/{dest_slug}/`
* `uploads/trip_plans/{plan_id}/`
* `uploads/payments/{payment_id}/` — payment proof docs

## AWS Accounts

* Bucket in PROD: account 007050358335, profile aa-prod-admin
* Region: ap-southeast-1

## Decision Needed (D-05)

Old website image redirect: 301 redirect `adventure.asia/storage/` → CDN (recommended) or dual-serve both paths?
