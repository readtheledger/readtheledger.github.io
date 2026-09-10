/* The Ledger — topic classification for the Newsstand.

   One file, read by the gatherer (fetch_feeds.mjs, at build time) and by the
   app (index.html, only when it has to gather in the browser), so a story is
   filed the same way wherever it was read.

   A story is filed by its actual subject — the headline first, then the opening
   of the summary, then the rest — and by its economic relevance. The publisher's
   own category is supporting evidence, never the verdict: a business desk's feed
   carries politics and human interest, and a weak association must not fill the
   Companies tab. When nothing in the text makes a case, the story stays in the
   Newsstand under no topic at all ("General"), which is honest, rather than in
   whichever tab the feed happened to suggest.

   Two editorial controls sit above the scoring:
     - a source marked fixed:true in sources.js is always filed under its own
       section (a central bank's press feed is Central Banks whatever it says);
     - OVERRIDES below file recurring formats by headline pattern.

   The result carries the section, a confidence ("override", "source", "high",
   "medium", "low", "none") and the reason, so the decision can be inspected and
   evaluated (eval_topics.mjs). */
(function (root) {
  "use strict";

  const SECTIONS = ["Markets", "Companies", "Economics", "Central Banks", "Opinion", "Tech & Finance", "Personal Finance"];
  const GENERAL = "";   // in the Newsstand, under no topic

  /* Each signal is a regular expression and a weight. The weight is multiplied by
     where it matched: 3 in the headline, 2 in the opening of the summary, 1 in
     the rest. A signal counts once per place, so a word repeated ten times is not
     ten times the evidence. */
  const SIGNALS = {
    "Central Banks": [
      [/\b(the fed|fed's|fed\b|fomc|federal reserve|central banks?|monetary policy|ecb|european central bank|bank of england|boe\b|bank of japan|boj\b|rba\b|snb\b|riksbank|bundesbank|pboc)/i, 3],
      [/\b(rate (cut|hike|rise|decision|call|hold|path)s?|basis points|policy rate|interest[- ]rate (decision|call|cut|hike|rise)s?|hold(ing)? rates? (steady|unchanged)|quantitative (easing|tightening)|balance sheet runoff)\b/i, 3],
      [/\b(warsh|powell|lagarde|bailey|ueda|waller|jefferson|hammack|barkin|bowman|elderson|lane|schnabel|de guindos)\b/i, 2],
      [/\b(fed governor|fed chair|fed president|fed official|policymakers?|rate[- ]setters?|dovish|hawkish|dissents?)\b/i, 2],
      [/\b(enforcement actions?|bank supervision|reserve requirements?|discount window|liquidity facility)\b/i, 2]
    ],
    "Companies": [
      [/\b(earnings|quarterly results|q[1-4] results|results beat|profits?|revenues?|sales (rose|fell|grew|slump|jump)|guidance|outlook cut|eps\b|non-gaap)\b/i, 3],
      [/\b(merger|acquisition|acquires?|acquired|takeover|buyout|to buy\b(?! back)|deal (to|with|for)|joint venture|spin-?off|divest\w*|strategic review)\b/i, 3],
      [/\b(ipo\b|listing|goes public|delist\w*|share (buy-?back|repurchase)|buybacks?|dividends?|stake in|shareholders?|boardroom|board (of directors|forces|ousts|votes))\b/i, 3],
      [/\b(ceo|chief executive|chief financial officer|cfo|founder|boss(es)?|executive (pay|chairman)|steps? down|resigns?|appoints?|leave of absence|ousted)\b/i, 2],
      [/\b(layoffs?|job cuts|cuts? \d[\d,]* jobs|creates? \d[\d,]* jobs|\d[\d,]* (uk |us )?jobs|hiring spree|redundanc\w+|strike (action)?|walkout|union(s)? (vote|strike|action))\b/i, 2],
      [/\b(unveils?|launch(es|ed)?|rolls? out|introduc(es|ed)|debuts?|new (model|product|phone|car|service)|recall(s|ed)?|outage|glitch)\b/i, 2],
      [/\b(company|companies|firm|manufacturer|automaker|carmaker|chipmaker|retailer|supermarket|airline|lender|insurer|brewer|drugmaker|conglomerate|plc\b|inc\b|corp\b|ltd\b)\b/i, 1],
      [/\b(antitrust|competition (probe|inquiry|regulator)|fine[ds]? \$|regulator (fines|probes)|lawsuit|sues?|settlement)\b/i, 2],
      [/\b(nasdaq|nyse|lse|tsx)\s*:\s*[a-z]{1,5}\b/i, 3],
      [/\b(supplier|supply deal|contract (win|worth)|valuation|valued at|raises? \$|funding round|series [a-e]\b)\b/i, 2],
      [/\b(makers?|automakers?|carmakers?|chipmakers?|drugmakers?|retailers?|brands?|airlines?)\b.{0,40}\b(shift|pivot|expand|invest|bet|race|plan|set to|warns?|to create|to build|to close|to avoid)\b/i, 3],
      [/\b(ad campaigns?|marketing (spend|push|campaign)|spend big on|sponsorship)\b/i, 2],
      [/\b((sales|deliveries|demand|orders) (slow|slump|fall|drop|rise|jump)|(car|phone|housing|ev) market (slows|cools|stalls))\b/i, 2]
    ],
    "Markets": [
      [/\b(stocks?|equities|shares?|bonds?|gilts?|yields?|treasur(y|ies)|s&p ?500|nasdaq|dow( jones)?|ftse|nikkei|dax|stoxx|index(es)?|indices)\b/i, 2],
      [/\b(crude|brent|wti|oil price\w*|oil('s)? (surge|slump|rally|shock)|barrel|opec|gold price\w*|silver|copper|commodit(y|ies)|sugar|wheat|natural gas)\b/i, 3],
      [/\b(currenc(y|ies)|dollar|yen|euro('s)? (rise|fall|slide)|sterling|pound (rises|falls)|forex|fx\b|exchange rate)\b/i, 2],
      [/\b(rall(y|ies|ied)|sell-?off|slump\w*|plunge\w*|tumble\w*|surge\w*|record high|all-time high|bull market|bear market|volatilit\w+|correction|risk-off|risk-on)\b/i, 2],
      [/\b(investors?|traders?|wall street|hedge funds?|asset managers?|fund managers?|futures|options|short sellers?|positioning|flows)\b/i, 2],
      [/\b(bitcoin|ether(eum)?|crypto\w*|memecoins?|token|chainlink|solana|xrp)\b/i, 2],
      [/\b(premarket|after hours|midday|biggest moves|movers|technical analysis|price (forecast|target)|breakout|resistance|support level)\b/i, 3],
      [/\b(etfs?|reits?|dividend stocks|value stocks|growth stocks|small caps?|large caps?|sector rotation)\b/i, 2],
      [/\b(oil (higher|lower|rises|falls|jumps|climbs|slides)|bond (buy-?backs?|auction|sale)|buys? back .{0,20}(bonds?|debt)|prediction markets?)\b/i, 3]
    ],
    "Tech & Finance": [
      [/\b(a\.?i\.?|artificial intelligence|machine learning|generative|chatbots?|llms?|large language models?|foundation models?|agentic|ai agents?|ai (model|lab|startup|safety|research|assistant|glasses|features?))\b/i, 3],
      [/\b(openai|anthropic|chatgpt|gpt-?\d|claude|gemini|deepmind|xai|mistral|perplexity|copilot)\b/i, 3],
      [/\b(chips?|semiconductors?|chipmakers?|nvidia|amd\b|tsmc|sk hynix|micron|gpus?|data cent(re|er)s?|hyperscalers?|cloud (computing|providers?))\b/i, 3],
      [/\b(startups?|start-ups?|venture capital|vc\b|unicorns?|seed round|series [a-e]\b|term sheet|founders?|y combinator|accelerator)\b/i, 3],
      [/\b(fintech|neobank|digital (bank|wallet|payments?)|payments? (network|rails|standards?)|crypto exchange|crypto platforms?)\b/i, 3],
      [/\b(stablecoins?|blockchain|defi|on-chain|tokeni[sz]ation|smart contracts?)\b/i, 3],
      [/\b(robots?|robotics|humanoids?|autonomous vehicles?|self-driving|drones?|quantum computing|foldable|smartphones?|software|app(s)? (store|maker)|platform)\b/i, 2]
    ],
    "Personal Finance": [
      [/\b(retire(ment|e|es|d)?|401\(?k\)?|iras?\b|roth|pensions?|annuit(y|ies)|social security|inherit(ed|ance)?|estate plan\w*|executor|beneficiar(y|ies)|my will\b|written (my|a) will)\b/i, 3],
      [/\b(mortgages?|remortgag\w+|home ?buyers?|first-time buyers?|renters?|rent (rises|prices)|landlords?|house prices?|housing (ladder|costs?))\b/i, 3],
      [/\b(savings?|savers?|isa\b|cash isa|deposit rates?|high-yield|budget(ing)? tips|budgeting|household (bills?|finances?|budgets?)|cost of living|energy bills?|bills? (rise|cut|fall))\b/i, 2],
      [/\b(credit cards?|credit scores?|debt (repayment|payoff)|loans?|student loans?|buy now pay later|overdrafts?)\b/i, 2],
      [/\b(insurance premiums?|home[- ]insurance|car insurance|life insurance|health insurance|premiums? (hit|rise|jump))\b/i, 3],
      [/\b(financial (advis[eo]rs?|planning|planners?)|wealth management|net worth|millionaires?|portfolios?|index funds?|diversif\w+|asset allocation|rebalanc\w+|your money|personal finance|money (tips|mistakes|questions?))\b/i, 2],
      [/\b(i'm \d\d|i am \d\d|my (wife|husband|siblings?|parents?|kids?|children)|can (i|we) (retire|afford|cash)|should i (retire|invest|buy|sell|pay|save|cash|keep|take)|what are (my|your) rights|your rights)\b/i, 3]
    ],
    "Economics": [
      [/\b(inflation|disinflation|deflation|cpi|pce|price (index|rises|pressures)|prices? (rise|rises|climb|soar|jump|fall|drop|surge)|consumer prices|producer prices|grocery bill|cost of living|(petrol|gasoline|diesel|fuel|energy|food|grocery) prices?)\b/i, 3],
      [/\b(gdp|growth (slows?|accelerat\w+|forecast)|recession|expansion|business cycle|output|productivity|nowcast\w*|forecasts?)\b/i, 3],
      [/\b(unemployment|jobless|payrolls?|jobs report|job (gains|growth|losses)|labou?r (market|force|data)|hiring|wages?|real (average )?hourly earnings|employment)\b/i, 3],
      [/\b(tariffs?|trade (war|deficit|surplus|rift|talks|policy|dispute|barriers)|import (ban|duties)|(new |trade |export )?bans? on|new ban|exports?|imports?|customs|retaliat\w+|sanctions?|supply chains?)\b/i, 3],
      [/\b(econom(y|ies|ic|ics|ist|ists)|fiscal|treasury (bill|bond|secretary)|budget deficit|public (debt|spending|finances)|national debt|debt ceiling|stimulus|austerity|wealth tax|bank (surcharge|tax|levy)|tax (rises?|hikes?|cuts?|policy|reform)|windfall tax)\b/i, 2],
      [/\b(housing starts|home sales|consumer (spending|sentiment|confidence)|retail sales|industrial production|pmi\b|manufacturing (data|activity)|capacity utili[sz]ation)\b/i, 3],
      [/\b(foreign reserves|current account|balance of payments|capital flows|intervention|devaluation|reserves? (drop|fall|rise))\b/i, 3],
      [/\b(census|bls\b|bea\b|ons\b|eurostat|imf\b|world bank|oecd|el ni[ñn]o|climate (risk|shock)|natural disasters?)\b/i, 2],
      [/\b(real (interest )?rates?|neutral rate|r-star|term premium|yield curve|money supply|monetary aggregates?|m2\b)\b/i, 2]
    ],
    "Opinion": [
      [/\b(opinion|commentary|comment:|column|essay|editorial|the guardian view|our view|my view|j\.d\.'s view|the case (for|against)|in defen[cs]e of|why (we|you|i) (can't|should|won't|need))\b/i, 3],
      [/\b((assorted|weekend|sunday|monday|tuesday|wednesday|thursday|friday|saturday|morning|longform|research|adviser|personal finance|top) (links|reads)|links:|\d+ (\w+ )?(am |pm )?reads\b|reads:|sentences to ponder|markets in everything|what should i ask|assorted)\b/i, 3],
      [/\b(podcast|transcript|interview(s|ed)?( me)?|episode|at the money|animal spirits|talk your book|mib:|masters in business|q&a|conversation with|fireside chat)\b/i, 3],
      [/\b(lessons? (from|of)|thoughts on|reflections|a note on|i think|i believe|argues?|argument|debate|philosophy of|should (we|you|the))\b/i, 1]
    ]
  };

  /* Recurring formats that scoring gets wrong or that a desk wants filed a fixed
     way. Each entry: a headline pattern and the section. The first match wins. */
  const OVERRIDES = [
    [/^stocks making the biggest moves/i, "Markets"],
    [/\b(premarket|after hours|midday) (movers|moves)\b/i, "Markets"],
    [/^(what|why|how) .* (fed|fomc)\b/i, "Central Banks"],
    [/^feds note:/i, "Economics"],
    [/^(federal reserve board|fed) (announces|approves|issues|releases|publishes)/i, "Central Banks"],
    [/\b(assorted links|links:|\d+ \w+ (am |pm )?reads)\b/i, "Opinion"],
    [/^(mib:|transcript:|at the money|animal spirits|talk your book)/i, "Opinion"],
    [/\bpersonal finance links\b/i, "Personal Finance"],
    [/\b(to present at|to participate in|announces? (grants? of|the delivery|strategic cooperation|inducement))\b/i, "Companies"],
    [/\b(non-gaap|gaap) eps\b/i, "Companies"]
  ];

  /* Political and international news that a business desk carries. These are
     filed as General unless the text makes an economic case of its own, so a
     Companies tab does not fill with elections and wars. */
  const OFF_TOPIC = /\b(election|midterms?|convention|parliament|congress(ional)?|senate|white house|prime minister|president(ial)?|cabinet|minister|netanyahu|putin|zelensky|houthi|hamas|hezbollah|airstrikes?|missile|war (in|with|on)|ceasefire|troops|military|ukraine|gaza|israel|yemen|iran(ian)?|protest(ers|s)?|immigration|asylum|refugees?|police|court (rules|hears)|trial|verdict|coronation|royal (family|wedding|visit|household)|football|tennis|olympics|orchestra|film|movie|actor|celebrit\w+|tv show|festival)\b/i;

  /* The economic case that keeps an off-topic story on the page: a company or a
     market or the economy is what the headline is actually about. */
  const ECONOMIC = /\b(econom\w+|market\w*|stocks?|shares?|bonds?|yields?|oil|energy|gas|prices?|inflation|tariffs?|trade|exports?|imports?|sanctions?|bank\w*|tax\w*|budget|deficit|debt|jobs?|wages?|investors?|investment|deal|companies|company|firms?|business\w*|ceo|earnings|profits?|revenue|fund\w*|currenc\w+|dollar|pound|euro|yen|supply chain|shortage|bans?|brands?|maker|billion|million|£|\$|€)\b/i;

  function score(section, title, lead, rest) {
    let total = 0; const hits = [];
    for (const [re, w] of SIGNALS[section]) {
      let place = 0;
      if (re.test(title)) place = 3;
      else if (re.test(lead)) place = 2;
      else if (re.test(rest)) place = 1;
      if (place) { total += w * place; hits.push(String(re).slice(1, 40) + "@" + place); }
    }
    return { total, hits };
  }

  function textOf(html) {
    return String(html || "").replace(/<[^>]+>/g, " ").replace(/&[a-z#0-9]+;/gi, " ").replace(/\s+/g, " ").trim();
  }

  /* classify({title, text|html, hint, fixed}) → {section, confidence, reason} */
  function classify(o) {
    const title = String(o.title || "").trim();
    const body = o.text != null ? String(o.text) : textOf(o.html);
    const lead = body.slice(0, 240);
    const rest = body.slice(240, 2000);
    const hint = SECTIONS.includes(o.hint) ? o.hint : "";

    if (o.fixed && hint) return { section: hint, confidence: "source", reason: "source is filed under its own section" };
    for (const [re, sec] of OVERRIDES) if (re.test(title)) return { section: sec, confidence: "override", reason: "headline pattern " + String(re) };

    const scores = {};
    for (const s of SECTIONS) scores[s] = score(s, title, lead, rest);
    // the publisher's category is supporting evidence: worth a little, never the verdict
    if (hint) scores[hint].total += 1;

    const ranked = SECTIONS.slice().sort((a, b) => scores[b].total - scores[a].total);
    let best = ranked[0], second = ranked[1];
    let top = scores[best].total, next = scores[second].total;

    // Companies needs a company doing something, not just a company mentioned:
    // a story with only the weakest Companies signals (the generic nouns) is not
    // a Companies story, whatever the desk that carried it
    const companyAction = SIGNALS["Companies"].slice(0, 6).concat(SIGNALS["Companies"].slice(7)).some(([re]) => re.test(title) || re.test(lead));
    if (best === "Companies" && !companyAction) {
      best = second; top = next; second = ranked[2]; next = scores[second].total;
    }

    // politics and human interest carried by a business desk: filed under a
    // topic only when the headline itself makes an economic case
    const offTopic = OFF_TOPIC.test(title) && !ECONOMIC.test(title);

    if (top >= 6 && top >= next * 1.4 && !offTopic) return { section: best, confidence: "high", reason: scores[best].hits.join(", ") };
    if (top >= 4 && !offTopic) return { section: best, confidence: "medium", reason: scores[best].hits.join(", ") + (next ? " (vs " + second + " " + next + ")" : "") };
    if (top >= 3 && hint === best && !offTopic) return { section: best, confidence: "low", reason: "weak signal agrees with the publisher's category" };
    return { section: GENERAL, confidence: "none", reason: offTopic ? "political or general news with no economic case in the headline" : "no clear subject signal (best " + (best || "-") + " " + top.toFixed(1) + ")" };
  }

  root.LEDGER_TOPICS = { SECTIONS, GENERAL, SIGNALS, OVERRIDES, classify, textOf };
})(typeof window !== "undefined" ? window : globalThis);
