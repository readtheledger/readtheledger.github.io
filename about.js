/* The Ledger — the About page.
   Shared by the app (index.html shows it in the reader, as a card at the foot of
   the front page) and the build (build.mjs writes it as /about/). It is part of
   the app, not an article: it carries no date and takes no place in the
   chronology. Everything here is a description of how the publication works,
   drawn from README.md and REVIEW.md; nothing about people or credentials that
   the publication has not stated. */
window.LEDGER_ABOUT = {
  title: "About The Ledger: a quiet place to read the market, one story at a time",
  standfirst: "What The Ledger is, how its own reporting is labelled, where the Newsstand comes from, and how to reach the desk. This page is part of the app, not an article, and carries no date.",
  html: `<p>The Ledger does one thing: it puts financial journalism in front of you without clutter. There are no adverts, no pop-ups asking for your email, and nothing here reaches past a publisher's paywall.</p>
  <h2>What The Ledger writes</h2>
  <p>The front page and the topic pages carry only The Ledger's own journalism: complete pieces written in The Ledger's own voice from credited research, not summaries of someone else's story. Every material source behind a piece is credited and linked in the <em>Sources &amp; further reading</em> box at its foot. Each piece has an address of its own, and its date is the date it was published; a news story more than a week old is marked <em>From the archive</em>.</p>
  <p>Each piece also says how it was produced. <strong>Reported and written by The Ledger</strong> means a person wrote it from the credited sources. <strong>Drafted with AI assistance</strong> means a model drafted it from the credited sources and a person checked every claim against them before publication. The label is set per piece, never by default, and the review that makes it true is written down in the publication's source repository.</p>
  <h2>The Newsstand</h2>
  <p>The Newsstand is a separate, labelled view: what the desk is reading from public feeds, gathered by the build about every half hour, with the time it was actually gathered shown on the page. A third-party story appears there only as a brief summary with attribution and a link to the original, never as a Ledger article. Full text renders only under an explicit reuse licence, and that licence is named beside the piece. The context box on a Newsstand story is labelled honestly: <em>Background</em> is the desk's standing note on that kind of story; <em>Why it matters</em> appears only for a note an editor wrote about that particular story and checked against the sources it names.</p>
  <h2>Listening and copying</h2>
  <p>The headphone button reads a piece aloud. With your own OpenAI API key, entered in Settings and kept only on your device, it uses OpenAI's speech models; without one it falls back to the voice built into your phone, so the button always works. The copy button puts the whole piece on your clipboard as plain text: headline, publication, author, date, the original link, then the body.</p>
  <h2>Corrections and contact</h2>
  <p>The Ledger is published at readtheledger.github.io and its source, including every article, is public. To report an error, ask for a correction or write to the desk, open an issue on the repository: <a href="https://github.com/readtheledger/readtheledger.github.io/issues" target="_blank" rel="noopener noreferrer">github.com/readtheledger/readtheledger.github.io/issues</a>. A correction is made to the piece itself, at its own address.</p>
  <p>The app keeps your saved stories, settings and any API key in this browser only. It sends one thing on your behalf: a page-view count to GoatCounter, which sets no cookies. There is no other analytics, and no advertising.</p>`
};
