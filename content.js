/* The Ledger — editorial content.
   Every article here is original writing by The Ledger, researched from the
   credited sources listed with each piece. This file is the publication:
   replace or add articles and redeploy to publish. Nothing in here is copied
   from another outlet; quotations are brief and attributed.

   Fields: id (stable), kind ("news" | "analysis" | "deep"), section, title,
   standfirst, date (ISO), produced (explicit; see REVIEW.md), html body,
   sources [{t: title, u: url, p: publisher}],
   weekly: true on the current deep-dive feature. */
window.LEDGER_CONTENT = {
  updated: "2026-08-17",
  articles: [

  {
    id: "led-20260817-record",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-record/hero-1200.jpg", alt:"A rising staircase of teal blocks is connected by a pulley and cord to an ochre counterweight.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"Rising markets and the counterweight of interest-rate uncertainty, shown conceptually."},
    kind: "news", section: "Markets",
    date: "2026-08-17T09:00:00Z",
    title: "Stocks sit at records while the Fed debates a hike — the strangest bull market in years",
    standfirst: "The S&P 500 closed last week at an all-time high of 7,798.99 after two inflation reports came in softer than feared. What makes this rally unusual is the direction of the argument behind it: the next Federal Reserve move under debate is a rise, not a cut.",
    html: `<p>The S&P 500 ended Thursday at 7,798.99, a record close, up 0.65% on the day, with the Nasdaq up 0.81%, in a session Reuters reported was driven by memory-chip makers — Sandisk up 13.7%, Micron up 4.2% — and the big platforms. The trigger was July's producer-price report, which came in flat on the month and slowed to 4.7% year-on-year from June's 5.5%, a day after consumer prices rose just 0.1% in July, leaving headline CPI at 3.4% and core CPI at 2.5% — its lowest since March 2021.</p>
    <p>That data did something unusual to the market's Fed arithmetic. Futures pricing tracked by CME's FedWatch had put the odds of a September rate <em>hike</em> above 70% earlier this summer; after the week's inflation and jobs data those odds collapsed to roughly 30%, per coverage in American Banker and Reuters. The rally, in other words, is not about cheap money coming — markets still price a better-than-90% chance of a <em>higher</em> policy rate by year-end — it is about tightening arriving more slowly than feared.</p>
    <p>Underneath the macro relief sits an earnings season that has broken records of its own. With over 90% of the S&P 500 reported, LSEG data cited by Reuters puts profit growth at 32.7% year-on-year excluding mark-to-market gains at Alphabet and Amazon; Bessemer Trust's tally has aggregate growth near 50% with 87% of companies beating estimates and ten of eleven sectors growing. Notably, the market has climbed 22% over twelve months while its forward price-to-earnings multiple <em>fell</em> from 22.4 to 20.2 — the gains have been paid for by profits, not by stretching valuations.</p>
    <p>The Ledger's read: a record set against hike risk is sturdier than one set against cut hopes, because it doesn't depend on rescue. The vulnerability is specific instead — index-level results now lean heavily on AI-linked earnings continuing to compound, and on oil, which has eased but answers to the unresolved situation around Iran and the Strait of Hormuz, staying quiet. Watch the week's FOMC minutes and Walmart's results for the first tests.</p>`,
    sources: [
      {t:"S&P 500 notches record-high close as rate-hike worries ease", u:"https://www.reuters.com/business/retail-consumer/wall-st-futures-tick-higher-oil-retreats-ahead-inflation-data-2026-08-13/", p:"Reuters"},
      {t:"US stocks rise to a record as oil prices drop and inflation gets less bad", u:"https://apnews.com/article/stock-markets-ai-semiconductors-fed-energy-3a23f22469cd0e0062f711096906525c", p:"AP"},
      {t:"Markets eye Fed hold after retail sales, consumer confidence fall", u:"https://www.americanbanker.com/news/markets-eye-fed-hold-after-retail-sales-consumer-confidence-fall", p:"American Banker"},
      {t:"Weekly Investment Update (08/14/2026)", u:"https://www.bessemertrust.com/insights/weekly-investment-update-08142026", p:"Bessemer Trust"}
    ]
  },

  {
    id: "led-20260817-fed",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-fed/hero-1200.jpg", alt:"Two folded arrows point in opposing directions across an empty conference table, with mountains behind it.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"Opposing policy directions meet around a conference table, in a conceptual illustration."},
    kind: "news", section: "Central Banks",
    date: "2026-08-17T08:30:00Z",
    title: "A Fed at war with itself heads for Jackson Hole",
    standfirst: "Three dissents at the last meeting, governors openly split, a chair who won't show his hand, and a president demanding cuts while part of the committee argues for a hike. The minutes on Wednesday and the Jackson Hole symposium later this month will show which faction is winning.",
    html: `<p>Kevin Warsh took over the Federal Reserve in May with the policy rate at 3.50–3.75% and inflation above target for a fifth year, aggravated early in 2026 by the U.S.–Israeli war with Iran and its effect on energy prices. His first meetings have exposed a committee genuinely divided: the July decision to hold was carried over three dissents in favour of an immediate hike, including Cleveland Fed President Beth Hammack, and Reuters reports governors Christopher Waller and Lisa Cook have both said they would support increases unless inflation cools soon.</p>
    <p>"The question is, how quickly do we need to deliver on that 2% objective," Hammack said last week, in remarks reported by Reuters — the hawks' case in a sentence. The doves' case is that the shocks doing the damage are the kind that fade: Richmond's Thomas Barkin noted that tariffs, oil and the AI investment boom account for much of the acceleration and "should pass." July's data leant their way — core CPI at 2.5%, producer prices flat on the month — and market odds of a September hike fell from a coin-flip to roughly a third.</p>
    <p>Warsh himself has refused to spell out a reaction function, an omission American Banker reports has kept policy uncertainty unusually high, while President Trump publicly blames the chair's "hostile" colleagues for blocking the cuts he wants. Into that vacuum come two events: Wednesday's minutes of the July meeting, which will show how close the committee actually came to moving, and the Jackson Hole symposium on August 27–29, a chair's traditional stage for declaring a framework.</p>
    <p>The Ledger's read: the substantive fight is not about September — it is about whether five years above target has started to move the public's expectations, which the University of Michigan survey puts at 4.3% for the year ahead. If the committee concludes it has, the glide-path argument dies and the hike case writes itself, whatever this month's prints say. Read the minutes for the word "expectations," not for the vote.</p>`,
    sources: [
      {t:"Fed may hold rates amid cooling inflation, jobs data", u:"https://finance-commerce.com/2026/08/fed-interest-rates-inflation-jobs-outlook/", p:"Reuters (Howard Schneider and Ann Saphir)"},
      {t:"Markets eye Fed hold after retail sales, consumer confidence fall", u:"https://www.americanbanker.com/news/markets-eye-fed-hold-after-retail-sales-consumer-confidence-fall", p:"American Banker"},
      {t:"Economic Week Ahead: August 17–21", u:"https://www.yardeniquicktakes.com/economic-week-ahead-august-17-21/", p:"Yardeni QuickTakes"}
    ]
  },

  {
    id: "led-20260817-consumer",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-consumer/hero-1200.jpg", alt:"A grocery trolley pauses at a small folded receipt placed against its front wheel.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"A pause in household spending, represented by a shopping trolley meeting a small obstacle."},
    kind: "news", section: "Economics",
    date: "2026-08-17T08:00:00Z",
    title: "The American consumer just blinked",
    standfirst: "Retail sales fell 0.6% in July despite a World Cup boost, consumer sentiment dropped hard, and real wages have been falling for six months. The economy's engine hasn't stalled — but it is knocking.",
    html: `<p>July's retail sales report, tracked by the Census Bureau at $763.6 billion, showed spending down 0.6% from June — and still down 0.2% after stripping out autos and petrol. The same morning, the University of Michigan's sentiment survey fell 7.6% on the month and 12.4% on the year, with the damage concentrated in expectations for business conditions rather than households' own finances. Only 8% of respondents expect their incomes to outpace inflation over the coming year, and the survey's year-ahead inflation expectation ticked up to 4.3%.</p>
    <p>The softness has company. Initial jobless claims rose to 209,000 in the week to August 7, ending a run of sub-200,000 readings, though the four-week average of 199,000 still describes a historically tight labour market and unemployment sits at 4.1%. Reuters reports wages have declined in real terms over the past six months — which is the quiet arithmetic behind the sentiment numbers: prices at 3.4% against tepid pay growth is a pay cut, whatever the payroll count says.</p>
    <p>Markets, in the current configuration, treated all this as good news, because a cooling consumer argues against the rate hike part of the Fed was pushing for. "It's a case of be careful what you wish for," Northlight Asset Management's Chris Zaccarelli told American Banker — consumer spending traces to nearly 70% of GDP, and a slowdown big enough to keep the Fed on hold is also big enough, if it runs, to reach corporate profits.</p>
    <p>The Ledger's read: one soft month after a World Cup-flattered quarter is a wobble, not a turn — Q2 spending was boosted by the tournament and tax relief, so some July payback was mechanical. The number that matters more is the expectations one: consumers acting on 4.3% expected inflation demand raises, resist prices and pull forward purchases, and that behaviour is self-fulfilling. Walmart's results this week are the single best read on whether the blink becomes a flinch.</p>`,
    sources: [
      {t:"Markets eye Fed hold after retail sales, consumer confidence fall", u:"https://www.americanbanker.com/news/markets-eye-fed-hold-after-retail-sales-consumer-confidence-fall", p:"American Banker"},
      {t:"Economic Week Ahead: August 17–21", u:"https://www.yardeniquicktakes.com/economic-week-ahead-august-17-21/", p:"Yardeni QuickTakes"},
      {t:"Fed may hold rates amid cooling inflation, jobs data", u:"https://finance-commerce.com/2026/08/fed-interest-rates-inflation-jobs-outlook/", p:"Reuters"}
    ]
  },

  {
    id: "led-20260817-river",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-river/hero-1200.jpg", alt:"Coins pour from a watering can beside a sapling with circuit-like leaves growing from a microchip planter.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"Capital flows toward a young AI venture, shown as a conceptual illustration."},
    kind: "news", section: "Tech & Finance",
    date: "2026-08-17T07:30:00Z",
    title: "A two-month-old startup just raised $1.1bn — inside the week AI funding lost its speed limit",
    standfirst: "River AI, founded weeks ago by an xAI co-founder, closed a billion-dollar first round. Lovable tripled its valuation to $13.3bn in eight months. The venture market is now pricing AI teams the way public markets price proven companies.",
    html: `<p>The week's venture headlines read like a decimal-point error. River AI, founded this summer by xAI co-founder Igor Babuschkin, raised $1.1 billion in a combined seed and Series A led by General Catalyst and AMP PBC, with Nvidia, AMD Ventures, Y Combinator and Temasek participating — TechCrunch reports the company is two months old. Sweden's Lovable confirmed a $400 million Series C at a $13.3 billion valuation, double its December mark of $6.6 billion, on the back of reaching $500 million in annualised revenue in June. Dictation startup Wispr raised $280 million at $2 billion on Monday, and code-testing firm Blacksmith's $45 million round valued it at $550 million — up almost tenfold in under a year.</p>
    <p>Three things distinguish this from the 2021 vintage of venture excess. First, some of these companies have real revenue growing at rates venture capital has rarely seen — Lovable's $500 million run rate is months old. Second, the buyers are different: strategic capital from Nvidia and AMD sits inside rounds like River's, which makes funding partly a supply-chain decision by chipmakers seeding their own future demand. Third, the size of a "seed" round now reflects the entry price of frontier AI — talent and compute are so expensive that a credible attempt costs a billion dollars before product exists.</p>
    <p>That last point is the risk. TechCrunch's own reporting flags River's round as "perhaps another indication of the overheated AI atmosphere" — when the ante is $1 billion, the venture model's tolerance for failure, its whole design principle, gets expensive. And when a company is priced at twenty-plus times a months-old run rate, the valuation assumes not just success but uncontested success.</p>
    <p>The Ledger's read: watch what the round <em>buys</em>, not what it says. Rounds that purchase compute capacity are converging with infrastructure finance and should be judged like it — on utilisation and pricing power, the same tests facing the hyperscalers, not on the software multiples their decks borrow.</p>`,
    sources: [
      {t:"General Catalyst leads $1.1B round into 2-month-old River AI", u:"https://techcrunch.com/2026/08/11/general-catalyst-leads-1-1b-round-into-2-month-old-river-ai/", p:"TechCrunch"},
      {t:"Lovable confirms new $13.3B valuation, raises another $400M", u:"https://techcrunch.com/2026/08/12/lovable-confirms-new-13-3b-valuation-raises-another-400m/", p:"TechCrunch"},
      {t:"Wispr raises $280M at $2B valuation as it looks beyond dictation", u:"https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/", p:"TechCrunch"},
      {t:"Blacksmith's valuation jumps 10x to $550M as AI coding fuels software validation", u:"https://techcrunch.com/2026/08/12/blacksmiths-valuation-jumps-10x-to-550m-as-ai-coding-fuels-software-validation/", p:"TechCrunch"}
    ]
  },

  {
    id: "led-20260817-aitrade",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-aitrade/hero-1200.jpg", alt:"A microchip and a stack of coins sit on a desk as a long receipt unfurls into the foreground.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"AI hardware earnings and the investment costs still coming due, illustrated conceptually."},
    kind: "news", section: "Markets",
    date: "2026-08-17T07:00:00Z",
    title: "The AI trade passed its earnings exam — the bill arrives later",
    standfirst: "Super Micro jumped 19% on results, memory makers surged, and Big Tech's AI spending is on course to top $700bn this year. The earnings are real; so is the size of the cheque being written to keep them coming.",
    html: `<p>The AI complex spent the week proving it can still clear the bar it keeps raising. Super Micro Computer reported quarterly earnings 84% above analyst estimates and jumped 19%, AP reported, with guidance above expectations too. The next session, Sandisk surged 13.7% and Micron 4.2% after strong results from Lenovo read across to the memory market, helping push the S&P 500 to its record. AI computing supplier CoreWeave also featured in the advance.</p>
    <p>The demand side of those results is a spending number without modern precedent: Reuters-cited estimates put Big Tech's AI investment above $700 billion this year, up from roughly $400 billion in 2025. Earnings season suggested the market has, for now, stopped punishing the spenders — Reuters reports investors have come to read aggressive capital expenditure as a response to visible demand rather than hubris, helped by strong forecasts from Microsoft and Amazon and by the financial strength of the companies writing the cheques.</p>
    <p>The strength is also broader than the megacaps. Bessemer Trust's season tally shows ten of eleven S&P sectors growing earnings, with the breadth extending well beyond the AI leaders — an important detail, because it means the market's profit base is less concentrated than its market capitalisation.</p>
    <p>The Ledger's read: the exam that matters has moved. The question is no longer whether AI-linked companies can grow into their guidance this quarter — they keep doing so — but whether $700 billion a year of capacity finds paying use before the hardware inside it ages. That is a utilisation question, not an earnings question, and it will be answered in compute prices and depreciation schedules over quarters. Our deep dive this week takes that question apart properly.</p>`,
    sources: [
      {t:"US stocks rise back towards records as AI companies report strong profits", u:"https://apnews.com/article/stocks-markets-rates-trump-iran-chips-db541ced9f928f993bd3a17958a3deaa", p:"AP"},
      {t:"S&P 500 notches record-high close as rate-hike worries ease", u:"https://www.reuters.com/business/retail-consumer/wall-st-futures-tick-higher-oil-retreats-ahead-inflation-data-2026-08-13/", p:"Reuters"},
      {t:"US Stock Market: Fed uncertainty, oil prices in focus as earnings sustain market optimism", u:"https://economictimes.indiatimes.com/markets/us-stocks/wall-street-guide/us-stock-market-fed-uncertainty-oil-prices-in-focus-as-earnings-sustain-market-optimism/articleshow/133286178.cms", p:"The Economic Times, citing Reuters"},
      {t:"Weekly Investment Update (08/14/2026)", u:"https://www.bessemertrust.com/insights/weekly-investment-update-08142026", p:"Bessemer Trust"}
    ]
  },

  {
    id: "led-20260817-badnews",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-badnews/hero-1200.jpg", alt:"A newspaper weighs down one side of a seesaw while three ascending blocks rise on the other side.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"Economic news and market expectations in a shifting balance, shown conceptually."},
    kind: "analysis", section: "Markets",
    date: "2026-08-17T06:30:00Z",
    title: "Why 'bad news is good news' is back — and how to tell when it stops working",
    standfirst: "Weak retail sales and soft jobs data lifted stocks last week because they argue against a rate hike. That logic has a shelf life, and the expiry conditions are visible in advance.",
    html: `<p>Last week produced a market pattern that reads as nonsense to anyone outside finance: shops sold less, hiring data disappointed, and equities rose. The mechanism is rate expectations. With part of the Federal Reserve arguing for a hike, every piece of soft economic data lowers the odds of tighter policy — so bad news for workers arrives as good news for asset prices. Northlight's Chris Zaccarelli described the week to American Banker as "three positive reports in a row," two of which were positive only in that inverted sense.</p>
    <p>The regime has a well-defined failure mode, and it is worth stating before it happens rather than after. Bad news supports equities only while it stays small enough not to threaten earnings. The moment soft demand data starts cutting revenue forecasts, the same reports flip sign: they stop promising a gentler Fed and start promising weaker profits. With consumer spending traceable to nearly 70% of GDP, the distance between "cooling enough to hold rates" and "cooling into the earnings line" is not large.</p>
    <p>Three indicators mark the boundary. Watch real yields rather than the policy rate — the ten-year Treasury near 4.69% against easing inflation means the bond market is doing some tightening on its own, and Reuters notes it is real yields that pressure the AI-heavy long-duration end of the equity market. Watch guidance rather than results: this season's rare negative outlooks are the tell to count. And watch the shops directly — which is why a Walmart print, this week, carries more regime information than any Fed speech.</p>
    <p>The Ledger's read: enjoy the inversion while it lasts, but treat it as a phase, not a law. The trades that work in "bad news is good news" — long duration, long the index — are precisely the ones that break when the regime flips, and regimes flip mid-quarter, not at scheduled meetings.</p>`,
    sources: [
      {t:"Markets eye Fed hold after retail sales, consumer confidence fall", u:"https://www.americanbanker.com/news/markets-eye-fed-hold-after-retail-sales-consumer-confidence-fall", p:"American Banker"},
      {t:"US Stock Market: Fed uncertainty, oil prices in focus as earnings sustain market optimism", u:"https://economictimes.indiatimes.com/markets/us-stocks/wall-street-guide/us-stock-market-fed-uncertainty-oil-prices-in-focus-as-earnings-sustain-market-optimism/articleshow/133286178.cms", p:"The Economic Times, citing Reuters"}
    ]
  },

  {
    id: "led-20260817-savers",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-savers/hero-1200.jpg", alt:"A stack of coins casts a long shadow toward a basket containing bread and groceries.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"Cash savings and the everyday purchases they support, shown as a conceptual illustration."},
    kind: "analysis", section: "Personal Finance",
    date: "2026-08-17T06:00:00Z",
    title: "What 4.3% expected inflation means for your cash",
    standfirst: "Households now expect prices to rise faster over the next year than most savings accounts pay. The gap between the rates savers see and the inflation they expect is quietly deciding who gets poorer.",
    html: `<p>Buried in last week's University of Michigan survey is the number that matters most to household finance: consumers expect 4.3% inflation over the year ahead, up from 4.2%, and only 8% of respondents expect their incomes to keep pace. Set that against the rate environment — a Fed policy rate of 3.50–3.75%, and measured inflation at 3.4% — and the household arithmetic is uncomfortable: cash in a typical account earning below the policy rate loses purchasing power at roughly the gap between its yield and whichever inflation number you believe.</p>
    <p>Which number you believe is the crux. Measured CPI has been easing — core is at 2.5%, its best since 2021 — while expectations have been rising. Both cannot describe the coming year. If the official trajectory holds, cash and short-duration savings are close to whole in real terms for the first time in years. If households' expectations prove right — and five years above target is why they distrust the official path, a concern several Fed policymakers share, per Reuters — then unhedged cash keeps leaking value at 2026's pace.</p>
    <p>The practical responses are unglamorous. Money parked long-term at a rate below the policy rate is an unforced error in either scenario — the spread between lazy deposit rates and best available short-term yields is pure cost. Fixed long-term borrowing gets cheaper in real terms if expectations are right, so the panic refinance has a case against it. And wage negotiation is where expectations become reality: the 92% who don't expect to keep pace mostly won't ask.</p>
    <p>The Ledger's read: the expectations number is a better guide to household behaviour than to actual inflation — surveys overshoot in both directions. But personal finance is played against your own costs, not the CPI basket, and the only universally correct move in a 3–4% world is refusing to hold cash at 1%.</p>`,
    sources: [
      {t:"Markets eye Fed hold after retail sales, consumer confidence fall", u:"https://www.americanbanker.com/news/markets-eye-fed-hold-after-retail-sales-consumer-confidence-fall", p:"American Banker"},
      {t:"Fed may hold rates amid cooling inflation, jobs data", u:"https://finance-commerce.com/2026/08/fed-interest-rates-inflation-jobs-outlook/", p:"Reuters"}
    ]
  },

  {
    id: "led-20260817-weekly",
    produced: "legacy-unrecorded",
    image:{u:"/assets/editorial/led-20260817-weekly/hero-1200.jpg", alt:"A server cabinet imagined as a building under construction, with a crane above and power cables flowing toward it.", w:1200, h:800, widths:[480,768,1200], ai:true, credit:"The Ledger", caption:"A conceptual view of the infrastructure and financial commitments behind AI expansion."},
    kind: "deep", section: "Tech & Finance", weekly: true,
    date: "2026-08-17T05:30:00Z",
    title: "The capex ledger: what a $700bn AI build-out does to the market's balance sheet",
    standfirst: "The deep dive for the week of 17 August. Big Tech's AI spending is on course to nearly double in a year, to more than $700 billion. That is no longer a software story — it is an infrastructure cycle, and it moves the risk somewhere the equity market isn't used to looking.",
    html: `<p>For its first act, the AI boom ran on the prettiest business model in history: software margins on top of someone else's infrastructure. The second act looks very different. Estimates cited by Reuters put the large platform companies' AI spending above $700 billion this year, up from roughly $400 billion in 2025 — commitment to chips, data centres and power on a scale that belongs in the same sentence as railways and telecoms. When spending of that size shows up anywhere, the correct instinct is not excitement or dread. It is accounting.</p>
    <h2>From income statement to balance sheet</h2>
    <p>A software business sells the same code twice at almost no extra cost, which is why the market pays so richly for it. A data centre is the opposite: enormous cost up front, revenue later, maybe. As the hyperscalers pour cash into physical capacity, a growing share of their value rests not on the economics they have, but on the economics they expect. Depreciation is where that bet becomes visible. Concrete and turbines depreciate over decades; the accelerators inside are superseded in a few years. Small changes in assumed useful life move reported earnings by billions, in businesses the market still prices as if capital hardly mattered.</p>
    <blockquote>Every technology bubble in history has been a dispute about depreciation schedules that called itself a dispute about the future.</blockquote>
    <p>That is only mildly unfair. The fibre glut of 2000 was a bet that traffic would arrive before the equipment aged; traffic arrived, but a decade late and at prices that ruined the people who laid the glass. The lesson was never that the optimists were wrong about demand. It was that being right about demand and wrong about timing is, financially, the same thing as being wrong.</p>
    <h2>Why this cycle is different — in both directions</h2>
    <p>The bull case has evidence the fibre era lacked. This earnings season, profit growth broadened to ten of eleven S&P sectors, per Bessemer Trust's tally, and the index climbed 22% over a year while its forward multiple fell from 22.4 to 20.2 — growth paid for by earnings, not valuation. Reuters reports investors now read the capex as a response to demonstrated demand, with strong forecasts from Microsoft and Amazon underwriting the mood. The spenders are the most profitable companies that have ever existed, funding much of this from operating cash flow.</p>
    <p>The bear case is about what "much" conceals. At $700 billion a year the marginal dollar increasingly arrives through financing — bonds, leases, joint ventures and special-purpose vehicles that place assets a step away from the sponsor's balance sheet. Risk that equity holders chose knowingly is migrating toward credit markets that price it like infrastructure. Sometimes it is. The difference between a toll road and a warehouse of accelerators is that nobody re-invents the toll road every thirty months. Meanwhile index concentration means the trade lives in pension portfolios that never chose it — and with the ten-year Treasury near 4.69%, the AI complex is being marked against real yields that no longer flatter long-duration bets.</p>
    <h2>What would tell you the story is turning</h2>
    <p>Watch utilisation and pricing rather than announcements: committed capacity is a press release, while the rental price of compute is a market clearing in real time — if it falls while build-out accelerates, supply is winning. Watch the gap between capex guidance and free cash flow, and note the first big spender to describe its depreciation assumptions as conservative. Watch power, the one input no financing structure can conjure. And watch credit terms on data-centre deals: when lenders start writing covenants like it's speculative construction, they will have concluded something the equity market hasn't said aloud.</p>
    <p>None of this says the technology disappoints. The railways were transformative and ruinous at the same time, for different people, in that order. The question for anyone reading AI headlines through a financial lens is never only whether the future arrives. It is who is paying for the track, at what cost of capital, and what they have promised themselves about how long it lasts.</p>`,
    sources: [
      {t:"US Stock Market: Fed uncertainty, oil prices in focus as earnings sustain market optimism", u:"https://economictimes.indiatimes.com/markets/us-stocks/wall-street-guide/us-stock-market-fed-uncertainty-oil-prices-in-focus-as-earnings-sustain-market-optimism/articleshow/133286178.cms", p:"The Economic Times, citing Reuters and LSEG"},
      {t:"Weekly Investment Update (08/14/2026)", u:"https://www.bessemertrust.com/insights/weekly-investment-update-08142026", p:"Bessemer Trust"},
      {t:"US stocks rise back towards records as AI companies report strong profits", u:"https://apnews.com/article/stocks-markets-rates-trump-iran-chips-db541ced9f928f993bd3a17958a3deaa", p:"AP"},
      {t:"General Catalyst leads $1.1B round into 2-month-old River AI", u:"https://techcrunch.com/2026/08/11/general-catalyst-leads-1-1b-round-into-2-month-old-river-ai/", p:"TechCrunch"}
    ]
  }

]};
