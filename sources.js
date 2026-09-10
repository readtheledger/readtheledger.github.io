/* The Ledger — the public feeds the Newsstand reads.

   Every feed here was checked by hand: public, free to read, no paywall and no
   login. Nothing from the FT, WSJ, Bloomberg or The Economist is included by
   design. The same list drives the app (index.html) and the build-time fetcher
   (fetch_feeds.mjs), so a source is added or removed in exactly one place.

   Fields:
     n       display name
     u       RSS or Atom URL
     s       fallback section when the text gives no clearer signal
     h       true for a heavy full-text feed (fetched in a second wave in the app)
     q       quality weight used when choosing the lead story
     k       editorial kind — "news", "analysis" or "deep" — which decides where
             the source's stories sit in the front-page mix
     lic     the reuse licence, only where one genuinely exists
     fixed   true when the feed is about one subject and its category is the
             verdict, not just evidence — a central bank's press feed is Central
             Banks whatever a headline says; everything else is filed by its
             actual subject (topics.js), with s as supporting evidence
     rights  what The Ledger may carry from this feed, recorded explicitly:
               "summary" — a summary, at most one short attributed quote, and a
                           link out; the article itself stays with the publisher
               "full"    — the whole article, under the licence named in lic
             The fetcher refuses a source with no rights value, and a "full"
             source with no licence, so nothing ships without a recorded
             permission for the use it is put to. */
window.LEDGER_SOURCES = [
  // ---- news desks with open feeds ----
  {n:"CNBC Markets",       u:"https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", s:"Markets", q:0.9, k:"news", rights:"summary"},
  {n:"CNBC Economy",       u:"https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", s:"Economics", q:0.95, k:"news", rights:"summary"},
  {n:"MarketWatch",        u:"https://feeds.content.dowjones.io/public/rss/mw_topstories", s:"Markets", q:0.95, k:"news", rights:"summary"},
  {n:"Yahoo Finance",      u:"https://finance.yahoo.com/news/rssindex",                   s:"Markets", q:0.85, k:"news", rights:"summary"},
  {n:"Business Insider",   u:"https://markets.businessinsider.com/rss/news",              s:"Markets", q:0.85, k:"news", rights:"summary"},
  {n:"BBC Business",       u:"https://feeds.bbci.co.uk/news/business/rss.xml",            s:"Companies", q:1.0, k:"news", rights:"summary"},
  {n:"The Guardian",       u:"https://www.theguardian.com/uk/business/rss",               s:"Companies", h:true, q:1.05, k:"news", rights:"summary"},
  {n:"Fortune",            u:"https://fortune.com/feed/fortune-feeds/?id=3230629",        s:"Companies", h:true, q:1.0, k:"news", rights:"summary"},
  {n:"Semafor Business",   u:"https://www.semafor.com/rss.xml",                           s:"Companies", h:true, q:1.05, k:"news", rights:"summary"},
  // ---- startups & AI ----
  {n:"TechCrunch",         u:"https://techcrunch.com/feed/",                              s:"Tech & Finance", q:0.95, k:"news", rights:"summary"},
  {n:"VentureBeat AI",     u:"https://venturebeat.com/category/ai/feed/",                 s:"Tech & Finance", q:0.9, k:"news", rights:"summary"},
  // ---- central banks & official research ----
  {n:"Federal Reserve",    u:"https://www.federalreserve.gov/feeds/press_all.xml",        s:"Central Banks", q:1.15, k:"news", lic:"US government work, public domain", fixed:true, rights:"full"},
  {n:"Fed Speeches",       u:"https://www.federalreserve.gov/feeds/speeches.xml",         s:"Central Banks", q:1.15, k:"news", lic:"US government work, public domain", fixed:true, rights:"full"},
  {n:"FEDS Notes",         u:"https://www.federalreserve.gov/feeds/feds_notes.xml",       s:"Economics", q:1.25, k:"deep", lic:"US government work, public domain", fixed:true, rights:"full"},
  {n:"ECB",                u:"https://www.ecb.europa.eu/rss/press.html",                  s:"Central Banks", q:1.15, k:"news", lic:"ECB — reproduction permitted with acknowledgement", fixed:true, rights:"full"},
  {n:"Bank of England",    u:"https://www.bankofengland.co.uk/rss/news",                  s:"Central Banks", q:1.15, k:"news", fixed:true, rights:"summary"},
  {n:"FRED Blog",          u:"https://fredblog.stlouisfed.org/feed/",                     s:"Economics", q:1.2, k:"analysis", fixed:true, rights:"summary"},
  // ---- Creative Commons / academic ----
  {n:"The Conversation",   u:"https://theconversation.com/us/business/articles.atom",     s:"Opinion", h:true, q:1.2, k:"deep", lic:"CC BY-ND 4.0", rights:"full"},
  // ---- independent analysts publishing in full ----
  {n:"Calculated Risk",    u:"https://calculatedrisk.substack.com/feed",                  s:"Economics", h:true, q:1.25, k:"analysis", rights:"summary"},
  {n:"Marginal Revolution",u:"https://marginalrevolution.com/feed",                       s:"Economics", q:1.2, k:"analysis", rights:"summary"},
  {n:"Econbrowser",        u:"https://econbrowser.com/feed",                              s:"Economics", q:1.25, k:"deep", rights:"summary"},
  {n:"Apricitas",          u:"https://www.apricitas.io/feed",                             s:"Economics", h:true, q:1.3, k:"deep", rights:"summary"},
  {n:"Noahpinion",         u:"https://www.noahpinion.blog/feed",                          s:"Opinion", h:true, q:1.25, k:"analysis", rights:"summary"},
  {n:"Klement on Investing",u:"https://klementoninvesting.substack.com/feed",             s:"Opinion", h:true, q:1.25, k:"analysis", rights:"summary"},
  {n:"The Big Picture",    u:"https://ritholtz.com/feed/",                                s:"Opinion", h:true, q:1.15, k:"analysis", rights:"summary"},
  {n:"Damodaran",          u:"https://aswathdamodaran.blogspot.com/feeds/posts/default?alt=rss", s:"Opinion", h:true, q:1.3, k:"deep", rights:"summary"},
  {n:"Abnormal Returns",   u:"https://abnormalreturns.com/feed/",                         s:"Markets", h:true, q:1.05, k:"analysis", rights:"summary"},
  {n:"A Wealth of Common Sense",u:"https://awealthofcommonsense.com/feed/",               s:"Personal Finance", q:1.2, k:"analysis", fixed:true, rights:"summary"},
  {n:"Of Dollars And Data",u:"https://ofdollarsanddata.com/feed/",                        s:"Personal Finance", h:true, q:1.2, k:"analysis", fixed:true, rights:"summary"}
];
