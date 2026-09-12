/* The Ledger — reviewed context for individual Newsstand stories.

   The Newsstand's standing notes (WIM_NOTES in index.html) are general
   background by desk, and the app labels them "Background". A note here is
   different: it is about one story, was written and checked by a person against
   the sources it names, and is the only thing the app ever shows under the
   heading "Why it matters" for a Newsstand item. Nothing here is generated or
   filled in automatically; an item with no entry simply shows Background.

   Keyed by the story's link as the feed carried it (tracking parameters, the
   fragment and a trailing slash are ignored when matching). Fields:
     why       the reviewed context, plain text, one or two paragraphs at most
     sources   what it rests on: [{t: title, u: https URL, p: publisher}]
     reviewed  ISO date of the review
     by        who reviewed it (a name or "The Ledger's editor")

   Example (not live — copy it, fill it in, and remove the leading //):
   // "https://example.com/story": {
   //   why: "…",
   //   sources: [{t: "…", u: "https://…", p: "…"}],
   //   reviewed: "2026-09-10", by: "The Ledger's editor"
   // }
*/
window.LEDGER_CONTEXT = {};
