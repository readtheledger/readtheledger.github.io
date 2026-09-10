# Topic classification — evaluation

Edition: `live edition of 2026-09-10T01:25:46Z (the deployed `data/feed.json`, recovered from the site; not committed — publisher excerpts stay out of the repository)`; the path shown by the tool was a local copy: `../../../tmp/claude-0/-home-user-readtheledger-github-io/16ab2554-a4e4-525b-a204-65877d25b587/scratchpad/live-feed.json` (gathered 2026-09-10T01:25:46.534Z). Sample: `docs/package-1/topic-sample.json`, 86 stories from 21 publishers.

**Result: 86/86 placed appropriately (100.0%), 69 exactly as expected, 0 outside the accepted placements, 0 not found in the edition (classified on the headline alone).**

Labels in the sample were assigned by the implementing agent (agent-reviewed), not by a human editor. "Accepted" lists other placements judged defensible for an ambiguous story; a story counts as appropriately placed when the classifier's verdict is the expected placement or one of the accepted ones. "General" means the story stays in the Newsstand under no topic tab.

| Source | Headline | Expected | Also accepted | Got | Confidence | OK |
|---|---|---|---|---|---|---|
| The Guardian | Anthropic researchers say AI could cause human extinction by 2030 | Tech & Finance | General | Tech & Finance | high | ✓ |
| BBC Business | Tax banks to give some households energy bill cut, unions tell Burnham | Economics | Personal Finance | Personal Finance | high | ✓ |
| TechCrunch | AI research startup Listen Labs scrubbed a $1.5B funding round for Salesforce talks | Tech & Finance | Companies | Tech & Finance | high | ✓ |
| CNBC Markets | Ant International partners with Visa, Mastercard on developing AI payments | Tech & Finance | Companies | Tech & Finance | high | ✓ |
| BBC Business | AI is becoming harder to control – can humans stay in charge? | Tech & Finance | General | Tech & Finance | high | ✓ |
| TechCrunch | Automattic’s board forces CEO Matt Mullenweg into leave of absence | Companies |  | Companies | high | ✓ |
| BBC Business | The one thing you need to do to succeed - according to top bosses | General | Opinion / Companies | Companies | high | ✓ |
| MarketWatch | Diesel prices hit another record high. If you’re shocked, wait until you see your grocery  | Economics | Markets | Economics | medium | ✓ |
| Semafor Business | Republicans kick off 'Trump-a-Palooza' midterm convention | General |  | General | none | ✓ |
| Semafor Business | EU unveils new 'Made in Europe' guidelines to counter China | Economics | Companies | Companies | high | ✓ |
| Semafor Business | Anthropic skirts UK safety review amid rising AI transparency concerns | Tech & Finance |  | Tech & Finance | high | ✓ |
| Semafor Business | US bond yields spike after Bessent increases buybacks | Markets |  | Markets | high | ✓ |
| MarketWatch | I’m a single 58-year-old veteran in California with $1.5 million and a VA pension. Can I r | Personal Finance |  | Personal Finance | high | ✓ |
| Semafor Business | Netanyahu denies he ignored UAE's warning ahead of Oct. 7 attacks | General |  | General | none | ✓ |
| TechCrunch | OpenAI adds a prominent AI doomer to its board of directors | Tech & Finance | Companies | Tech & Finance | high | ✓ |
| Semafor Business | Hostilities between Saudi and Houthi rebels escalate in Yemen | General |  | General | none | ✓ |
| MarketWatch | Home-insurance premiums just hit a record high. Here’s where they spiked the most. | Personal Finance |  | Personal Finance | medium | ✓ |
| MarketWatch | Hunter Biden’s memecoin flops, falling 95% just hours after launch | Markets | Tech & Finance | Markets | high | ✓ |
| The Big Picture | At The Money: Becoming a “FinFluencer” | Opinion |  | Opinion | override | ✓ |
| MarketWatch | ‘We fear financial exploitation’: Who will manage our finances if my wife and I become inc | Personal Finance |  | Personal Finance | high | ✓ |
| TechCrunch | Massachusetts hits data centers with new clean power rules | Tech & Finance | Economics | Tech & Finance | high | ✓ |
| Fortune | OpenAI’s rogue AI agents reached at least 12 more websites, researchers say | Tech & Finance |  | Tech & Finance | high | ✓ |
| Semafor Business | AI researcher Andrew Tulloch is leaving Meta | Tech & Finance | Companies | Tech & Finance | high | ✓ |
| Semafor Business | ’We all agree that big government is bad, but…’: White House shrugs off Republican clashes | General | Economics | General | none | ✓ |
| MarketWatch | The bull market’s biggest enemy right now could be Bessent’s interventions | Markets |  | Markets | high | ✓ |
| MarketWatch | ‘I’m the executor’: My two siblings and I inherited an IRA. Can we just cash it out? | Personal Finance |  | Personal Finance | high | ✓ |
| Econbrowser | High Real Interest Rates Because of Incipient Rapid Growth? | Economics |  | Economics | high | ✓ |
| TechCrunch | Apple’s new CEO is reviving a Steve Jobs strategy from 25 years ago | Companies | Tech & Finance | Companies | high | ✓ |
| Fortune | Hollywood’s ‘new business model’ comes into view as Gen Z shows a moviegoing taste that co | Companies | General | General | none | ✓ |
| Fortune | Prediction markets spend big on celebrity campaigns even as Sydney Sweeney and LeBron Jame | Companies | Markets | Markets | medium | ✓ |
| MarketWatch | Oil’s surge back above $100 fuels fresh inflation fears at a crucial time for interest rat | Markets | Economics | Markets | high | ✓ |
| MarketWatch | You should always have energy stocks in your 401(k). Yes, even when oil is at $100. | Personal Finance | Markets | Personal Finance | medium | ✓ |
| Business Insider | CooperCompanies Announces Third Quarter 2026 Results | Companies |  | Companies | high | ✓ |
| Business Insider | Fuel Tech To Present At H.C. Wainwright 28th Annual Global Investment Conference | Companies |  | Companies | override | ✓ |
| Business Insider | AeroVironment Non-GAAP EPS of $0.59 beats by $0.34, revenue of $480.5M beats by $24.41M | Companies |  | Companies | override | ✓ |
| BBC Business | Apple's new boss starts with big gamble on costly first folding iPhone | Companies |  | Companies | high | ✓ |
| Semafor Business | Treasury to buy back triple the bonds | Markets | Economics | Markets | high | ✓ |
| MarketWatch | Canadian whisky on the rocks? Crown Royal is set to avoid Trump’s new ban. | Companies | Economics | Economics | high | ✓ |
| The Guardian | Oil prices rise above $100 a barrel for first time since July as Iran war escalates | Markets |  | Markets | medium | ✓ |
| Semafor Business | Why we can't rely on governments to handle AI safety | Opinion | Tech & Finance | Opinion | medium | ✓ |
| TechCrunch | Harvey hits $15.5B valuation, months after reaching $11B | Tech & Finance | Companies | Tech & Finance | high | ✓ |
| BBC Business | Air traffic failure was avoidable, says transport secretary | General | Companies | Companies | medium | ✓ |
| Abnormal Returns | Wednesday links: a moment of sheer luck | Opinion | Markets | Markets | high | ✓ |
| Marginal Revolution | What should I ask Kevin Roose? | Opinion | General | Opinion | high | ✓ |
| CNBC Markets | Stocks making the biggest moves midday: Meta, Centerspace, Apple, Casey's General Stores,  | Markets |  | Markets | override | ✓ |
| The Guardian | The Guardian view on UK-EU relations: voters would reward greater ambition \| Editorial | General | Opinion | Opinion | high | ✓ |
| The Guardian | The Guardian view on Donald Trump’s oil deal: Venezuela pays for his vanity \| Editorial | Opinion | Economics / Markets | Opinion | high | ✓ |
| ECB | Christine Lagarde: The choice facing Europeans | Central Banks |  | Central Banks | source | ✓ |
| The Guardian | JP Morgan boss Jamie Dimon warns UK chancellor against bank tax hike | Companies | Economics | Economics | medium | ✓ |
| CNBC Economy | U.S. reveals import ban on slew of Canadian goods as trade war escalates | Economics |  | Economics | high | ✓ |
| The Guardian | Air traffic control boss given a week to report after UK flight chaos causes 2,000 cancell | Companies | General | Companies | high | ✓ |
| BBC Business | Petrol prices rise by 5p over a week as Iran war sends oil higher | Economics | Markets / Personal Finance | Markets | medium | ✓ |
| BBC Business | Learner drivers still forced to wait months to book tests | General |  | General | none | ✓ |
| The Guardian | UK airport disruption: what are your rights if you have been affected? | Personal Finance | General | Personal Finance | high | ✓ |
| CNBC Economy | Why the Fed's interest rate call could come down to a few hundredths of a percentage point | Central Banks |  | Central Banks | override | ✓ |
| A Wealth of Common Sense | Animal Spirits: Everywhere Millionaires | Personal Finance | Opinion | Personal Finance | source | ✓ |
| BBC Business | US to ban imports of some Canadian alcohol, dairy goods and motorbikes | Economics |  | Economics | high | ✓ |
| Noahpinion | Liberalism needs a new philosophy of immigration | General | Opinion | General | none | ✓ |
| The Guardian | Supercar maker McLaren to create 1,000 UK jobs in £450m tech investment | Companies |  | Companies | high | ✓ |
| The Guardian | I co-founded an orchestra 18 years ago. Since then, I’ve seen doors close for working-clas | General |  | General | none | ✓ |
| CNBC Markets | Adani Enterprises shares jump as airport unit enters into $1 billion fundraising deal | Companies | Markets | Markets | high | ✓ |
| BBC Business | Singaporean man pleads guilty in US to massive crypto heist | General | Tech & Finance / Markets | Markets | high | ✓ |
| The Guardian | Burnham urged to tackle inequality with policies including wealth tax | Economics |  | Economics | high | ✓ |
| CNBC Markets | China's EV makers shift gears to focus on humanoids as car market slows | Companies | Tech & Finance | Companies | high | ✓ |
| The Guardian | ‘Miserable and impossible’: food scarce in Kyiv as Russia targets supply chains | General | Economics | Economics | high | ✓ |
| BBC Business | I'm 27 and I've already written my will - here's why | Personal Finance |  | Personal Finance | high | ✓ |
| CNBC Markets | How one hedge-fund manager built his firm to be powered entirely by AI agents | Tech & Finance | Markets | Tech & Finance | medium | ✓ |
| BBC Business | OpenAI says it cracked 90-year-old maths problem in 88 hours | Tech & Finance |  | Tech & Finance | high | ✓ |
| Econbrowser | Wisconsin Dairy Hit With Retaliatory Tariffs: | Economics |  | Economics | high | ✓ |
| CNBC Economy | Canada's retaliatory tariffs worth CA$27.6 billion take effect as trade rift with U.S. dee | Economics |  | Economics | high | ✓ |
| CNBC Economy | Japan's foreign reserves drop by a record $80 billion in August following yen intervention | Economics | Markets | Economics | high | ✓ |
| Yahoo Finance | Chainlink Price Forecast: LINK Breakout Targets $18 Rally | Markets |  | Markets | high | ✓ |
| Yahoo Finance | Corning Shares Rise on Multi-Billion-Dollar Verizon Fibre Agreement | Companies | Markets | Markets | high | ✓ |
| The Big Picture | Corporate vs Treasury Debt Duration | Markets | Opinion | Markets | high | ✓ |
| Of Dollars And Data | Living Poor to Die Rich | Personal Finance |  | Personal Finance | source | ✓ |
| CNBC Markets | Visa tells CNBC it is expanding data offering for blockchain lenders as demand for stablec | Tech & Finance | Companies | Tech & Finance | medium | ✓ |
| CNBC Economy | Trump turns up the heat on Warsh as Fed rate hike looms | Central Banks |  | Central Banks | high | ✓ |
| CNBC Economy | U.S. payrolls rose 162,000 in August, much more than expected; unemployment rate at 4.1% | Economics |  | Economics | high | ✓ |
| Federal Reserve | Federal Reserve Board announces termination of enforcement actions with United Texas Bank, | Central Banks |  | Central Banks | source | ✓ |
| FEDS Notes | FEDS Note: New Forms of Money and the U.S. Monetary Aggregates | Economics |  | Economics | source | ✓ |
| Fed Speeches | Waller, The Economic Outlook and Some Comments on My Policy Communication | Central Banks |  | Central Banks | source | ✓ |
| CNBC Markets | Bitcoin heads for third winning week in a row as macro pressures mount | Markets |  | Markets | high | ✓ |
| CNBC Markets | Sugar is outperforming the stock market this year. Here's what's driving it, and where it  | Markets |  | Markets | high | ✓ |
| CNBC Economy | From ‘mystery vacations’ to hostels, budget travelers get thrifty as prices rise | Economics | Personal Finance | Economics | high | ✓ |
| Semafor Business | Students perform better academically with less AI, study finds | General | Tech & Finance | Tech & Finance | high | ✓ |
| Marginal Revolution | Next Wins Appeal | Companies | General / Economics | Economics | medium | ✓ |

## Misplacements and ambiguities

- none outside the accepted placements

Stories classified on the headline alone because they were not found in the edition: 0.

## How to read this

- **Two modes.** The table above is the classifier run with each story's excerpt, as the gatherer runs it at build time. Run on the **headlines alone** (what `qa_package1.py` does in CI, because the edition is not committed) the same sample scores: 83/86 placed appropriately (96.5%), 67 exactly as expected, 3 outside the accepted placements, 86 not found in the edition (classified on the headline alone).
- **Who labelled the sample.** The expected placements were assigned by the implementing agent after reading each headline and excerpt — **agent-reviewed, not human-reviewed**. Where two placements were defensible the second is listed as accepted; that judgement is the agent's too. A human editor may disagree with individual labels; the sample file is meant to be edited, and the score re-run, when they do.
- **What "General" means.** The story stays in the Newsstand list with the kicker *Newsstand* and appears under no topic tab. This is the conservative fallback the package asked for: a weak association no longer fills Companies.
- **Overrides.** A source marked `fixed:true` in `sources.js` is always filed under its section (central-bank feeds, FRED Blog, the two personal-finance blogs — 8 of 29 sources). Headline patterns in `topics.js` `OVERRIDES` file recurring formats (market-movers lists, links round-ups, wire press-release boilerplate). Both are editorial controls a person can change without touching the scoring.
- **Ambiguities worth a human look:** "Tax banks to give some households energy bill cut" (fiscal policy or household finance); "The Guardian view on Donald Trump's oil deal" (an editorial about a resource deal); "Petrol prices rise by 5p" (consumer prices or oil); "Corning shares rise on Verizon agreement" (a company deal reported as a share move); "Next wins appeal" (a company story with no company signal in a three-word headline).
