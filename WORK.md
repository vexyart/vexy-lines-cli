---
this_file: WORK.md
---

# Work log

## 2026-11-24 — Documentation theme

- `bash build.sh --docs --strict` rebuilt `docs/` with fly-january 0.2.1 and zero warnings. All 11 HTML pages load the packaged Fly assets and include the Vexy menu and footer.
- The combined print guide uses the print-site 2.9 renderer inside a normal Fly page. All nine chapters and their fragment links passed the generated-guide check.
- `uv run --frozen --python 3.13 --with pytest python -m pytest tests` passed all 138 tests.

## 2026-10-18: documentation plugins

- Use MaterialX search, inherited metadata and a topic index; keep ordered navigation in awesome-nav.
- The documentation wrapper installs the plugins required by this site.
- Strict documentation build and rendered output checks passed.
- Documentation CI now uses the same isolated ProperDocs/plugin wrapper as local builds.
