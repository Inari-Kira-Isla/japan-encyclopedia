# Encyclopedia Maintenance Anomalies

## 2026-05-24
- **Issue**: Git push failed with exit code 129 on all three sites (JP/HK/TW)
- **Root cause**: Script used invalid git option `--rebase=false` (not supported in modern git)
- **Fix applied**: Changed to `git push` (no flags) in encyclopedia_maintenance.py line 216
- **Resolution**: Manual push succeeded after fix

```
  日本百科       | sitemap +92 → 2992 | articles.json +2990 → 2990 | ✅ pushed
  香港百科      | sitemap +192 → 2860 | articles.json +2858 → 2858 | ✅ pushed
  台灣百科      | sitemap +164 → 2332 | articles.json +2330 → 2330 | ✅ pushed
```