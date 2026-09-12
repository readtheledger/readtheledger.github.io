/* Attribution contract shared by the static build and the reading app.
   Categories describe editorial evidence; validation cannot perform or prove
   a person's factual review. REVIEW.md defines that separate recorded process. */
window.LEDGER_PRODUCTION = (() => {
  const legacyDates = Object.freeze({
    "led-20260817-record": "2026-08-17T09:00:00Z",
    "led-20260817-fed": "2026-08-17T08:30:00Z",
    "led-20260817-consumer": "2026-08-17T08:00:00Z",
    "led-20260817-river": "2026-08-17T07:30:00Z",
    "led-20260817-aitrade": "2026-08-17T07:00:00Z",
    "led-20260817-badnews": "2026-08-17T06:30:00Z",
    "led-20260817-savers": "2026-08-17T06:00:00Z",
    "led-20260817-weekly": "2026-08-17T05:30:00Z"
  });
  const legacyText = "From The Ledger archive. A factual review record is not available for this article.";
  const more = ' <a href="/about/">About our editorial standards</a>.';
  function error(a) {
    if (!a || !["reported", "assisted", "legacy-unrecorded"].includes(a.produced)) {
      return "produced must be explicitly set to reported, assisted or legacy-unrecorded";
    }
    if (a.produced === "legacy-unrecorded" &&
        (!Object.hasOwn(legacyDates, a.id) || a.date !== legacyDates[a.id] ||
         (a.updated !== undefined && a.updated !== a.date))) {
      return "legacy-unrecorded is limited to the eight original archive IDs and publication dates, without a new edition date";
    }
    return null;
  }
  function line(a) {
    // A malformed or stale runtime item must never become a human-writing claim.
    // The build rejects it; a reader with inconsistent local data stays neutral.
    if (error(a)) return "The Ledger. Production status is unavailable." + more;
    if (a.produced === "legacy-unrecorded") return legacyText + more;
    if (a.produced === "assisted") return "Drafted with AI assistance from the credited sources and reviewed by <strong>The Ledger</strong>'s editor before publication.";
    return "Reported and written by <strong>The Ledger</strong>.";
  }
  function archiveNotice(a) {
    return !error(a) && a.produced === "legacy-unrecorded" ? legacyText : "";
  }
  return Object.freeze({ error, line, archiveNotice });
})();
