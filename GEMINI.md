# Japan Encyclopedia

## Overview
A comprehensive, AEO-optimized encyclopedia guide to Japan's 8 regions (Hokkaido to Okinawa). Focuses on cultural, food, architecture, and nature content. Published via GitHub Pages under CC BY 4.0 license.

## Tech Stack
Static Site (HTML/CSS/JS or SSG), GitHub Pages, Schema.org (JSON-LD).

## Architecture
- **Root:** `index.html`, `llms.txt`, `sitemap.xml`.
- **Content:** Organized by 8 regions (北海道, 東北, 關東, 中部, 近畿, 中國, 四國, 九州沖繩).
- **SEO/AEO:** Schema types (EducationalOrganization, Article, FAQPage) embedded via JSON-LD.
- **Deployment:** Auto-deploys from `gh-pages` branch.

## Commands
- **Update Content:** Commit changes to `main` branch.
  ```bash
  git add .
  git commit -m "Update region content"
  git push origin main
  ```
- **Local Dev (if applicable):** Standard static server (e.g., `npx serve`, `jekyll serve`).

## Coding Style
- **Semantic HTML:** Use `<article>`, `<section>`, `<h1>`-`<h6>` for structure and SEO.
- **AEO:** Ensure all new pages are added to `llms.txt` and include valid JSON-LD schemas.
- **Content:** Focus on high-quality, factual descriptions of regions.

## Important Rules
- **AEO Integrity:** Do not break the `llms.txt` or sitemap generation. These are critical for AI visibility.
- **License:** Respect CC BY 4.0. All external contributions must be compatible.
- **Branch Policy:** Deployment happens automatically via GitHub Actions or branch push to `gh-pages`. Do not manually force push to `gh-pages`.