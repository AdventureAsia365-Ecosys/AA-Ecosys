# AA-995 — production Lighthouse mobile after TripPlanner #178 (S256, 29/10/2026 ~08:00 +07)

CIS 960 w rendition: migration 301 (CIS #1124, Infra #490), code CIS #1125 (`5923c46b`), backfill 3,229 photos written / 0 failed / 0 remaining.

```
page           runs  perf  LCP s  FCP s  TBT ms    CLS  LCP runs (s)  element / first high-priority image
bhutan            3    88   3.88   1.06      15  0.000  [4.76, 3.88, 1.88]  div.aa-site > main#main > section.tp-page-hero > img.tp-hero-img ('1GcwUTa2SNGnIerRlikwcnl5wsz0W__E3-960.webp?v=b9447b91556c', 107882)
destinations      3    92   3.38   0.94      14  0.000  [1.4, 3.38, 3.38]  ul.grid > li > a.tp-lift > img.tp-lift-img ('1eIyF-AtunPHBNhJl5oOz9ywtqoBofWQ3-600.webp?v=bde509793577', 41702)
home              3   100   1.54   1.00      20  0.000  [1.77, 1.54, 1.54]  main#main > section.tp-hero > picture > img.tp-hero-img ('home-port-756.avif', 60460)
tour              3   100   1.57   1.00      14  0.000  [2.31, 1.57, 1.54]  div.relative > ul.tp-snap-row > li.relative > img.h-full ('1eIyF-AtunPHBNhJl5oOz9ywtqoBofWQ3-600.webp?v=bde509793577', 41705)
```
