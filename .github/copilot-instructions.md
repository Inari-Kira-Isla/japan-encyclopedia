# Japan Encyclopedia

## Project
Static AEO-optimized encyclopedia of Japan's 8 regions. Built with HTML/CSS/JS, deployed via GitHub Pages.

## Conventions
- Use semantic HTML5 elements
- Include Schema.org structured data for SEO
- Generate llms.txt for LLM accessibility
- Keep content in Traditional Chinese (繁體中文)
- Group content by 8 regions: 北海道, 東北, 關東, 中部, 近畿, 中國, 四國, 九州沖繩
- Include culture, food, architecture, nature articles per region

## Naming
- Use lowercase kebab-case for file names
- Use descriptive, SEO-friendly titles
- Follow: `{region}-{topic}.html` pattern

## Architecture
- Static site with no build step
- GitHub Pages deployment from gh-pages branch
- Schema.org: EducationalOrganization, Article, FAQPage
- sitemap.xml and robots.txt at root

## Commands
- `git checkout -b gh-pages && git push -u origin gh-pages` — Deploy to GitHub Pages
- Validate HTML with W3C validator before commit
- Ensure llms.txt updates when content changes

## Do Not
- Do not add JavaScript frameworks (React, Vue, etc.)
- Do not use server-side rendering
- Do not modify content without updating llms.txt
- Do not remove CC BY 4.0 license attribution