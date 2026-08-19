# Changelog

All notable changes to The Ledger. Dates are UTC.

## 2026-08-19

### Fixed
- **The publication now actually deploys.** The Pages workflow assembled the site
  without `content.js` — the file that carries every Ledger article — so the live
  front page fell back to the built-in demo page alone. `content.js` is now copied
  into the artifact, and a new workflow step fails the build if any file referenced
  by `index.html`, `sw.js` or the manifest is missing from `_site`, so this class of
  bug cannot ship silently again.
- Playback-speed button label rendered `2.×` and `1.×` at whole-number rates; it now
  shows `2.0×` / `1.0×`.
- Pressing Escape in the reader now leaves through history exactly like the back
  button, so the reader's history entry no longer lingers after the panel closes.

### Improved
- **Keyboard accessibility:** article cards and the long-reads rail are focusable
  and open with Enter or Space; a visible `:focus-visible` outline was added; the
  active section tab is now marked with `aria-current="page"`; the search input
  gained an accessible label.
- The `theme-color` status-bar colour now follows the in-app light/dark toggle,
  not just the system preference.
- Added canonical URL and Open Graph / Twitter card metadata so shared links
  preview properly.
- Service worker cache version bumped to 3 so installed clients re-precache the
  full shell (including `content.js`).

## 2026-08-18

- First deployment of the site to https://readtheledger.github.io/ (mirror of the
  tested build, commit `d733a6f`).
