#!/usr/bin/env bash
# AA-995 S256: image preload hints per page — in the HTML <head> and in the inline Flight payload (HL rows).
S=/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/ff81ce35-ad69-438a-8e57-da54285435ff/scratchpad
for u in / /destinations /destinations/bhutan /tours/sri-lanka-cultural-tour-kandy-dambulla-and-sigiriya-3-days-sri-lanka-28e22489; do
  curl -s http://localhost:3995$u > $S/p.html
  echo "== $u  html-preloads=$(grep -o '<link rel="preload" as="image"' $S/p.html | wc -l)  flight-image-hints=$(grep -o 'HL\[[^]]*\\"image\\"' $S/p.html | wc -l)"
  grep -o 'HL\[[^]]*\\"image\\"' $S/p.html | cut -c1-110
done
