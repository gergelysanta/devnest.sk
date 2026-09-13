#!/bin/bash
# Packages the site for deployment. Cloudflare Pages has no ignore-file
# support, so it would otherwise upload the whole repo — including
# drafts/ and tools/, which must stay private. This copies only the
# public site into dist/ and points Pages at that folder instead.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist

cp index.html 404.html robots.txt sitemap.xml dist/
cp -R apps company privacy support assets dist/
