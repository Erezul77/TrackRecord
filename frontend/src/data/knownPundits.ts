// Known pundits database for auto-complete when adding new pundits
// These are well-known figures who make public predictions

export interface KnownPundit {
  name: string
  username: string
  affiliation: string
  bio: string
  domains: string[]
}

export const KNOWN_PUNDITS: KnownPundit[] = [
  // ===== CRYPTO & BITCOIN =====
  {
    name: "Michael Saylor",
    username: "saylor",
    affiliation: "MicroStrategy Executive Chairman",
    bio: "Bitcoin maximalist, former MicroStrategy CEO. Led company to acquire billions in BTC.",
    domains: ["crypto", "markets"]
  },
  {
    name: "Plan B",
    username: "100trillionUSD",
    affiliation: "Independent Analyst",
    bio: "Creator of Bitcoin Stock-to-Flow model. Anonymous quantitative analyst.",
    domains: ["crypto"]
  },
  {
    name: "Anthony Pompliano",
    username: "APompliano",
    affiliation: "Pomp Investments",
    bio: "Bitcoin advocate, investor, host of The Pomp Podcast.",
    domains: ["crypto", "markets"]
  },
  {
    name: "Raoul Pal",
    username: "RaoulGMI",
    affiliation: "Real Vision CEO",
    bio: "Former Goldman Sachs executive, macro investor, Real Vision founder.",
    domains: ["crypto", "macro", "markets"]
  },
  {
    name: "Willy Woo",
    username: "woonomic",
    affiliation: "Independent On-chain Analyst",
    bio: "Bitcoin on-chain analyst, creator of multiple BTC valuation models.",
    domains: ["crypto"]
  },
  {
    name: "CZ (Changpeng Zhao)",
    username: "caboringfromoffice",
    affiliation: "Former Binance CEO",
    bio: "Founder and former CEO of Binance, world's largest crypto exchange.",
    domains: ["crypto"]
  },
  {
    name: "Vitalik Buterin",
    username: "VitalikButerin",
    affiliation: "Ethereum Co-founder",
    bio: "Co-founder of Ethereum, blockchain researcher and developer.",
    domains: ["crypto", "tech"]
  },
  {
    name: "Charles Hoskinson",
    username: "IOHK_Charles",
    affiliation: "Cardano Founder",
    bio: "Ethereum co-founder, founder of Cardano and IOHK.",
    domains: ["crypto", "tech"]
  },
  {
    name: "Brian Armstrong",
    username: "brian_armstrong",
    affiliation: "Coinbase CEO",
    bio: "Co-founder and CEO of Coinbase, largest US crypto exchange.",
    domains: ["crypto", "tech"]
  },
  {
    name: "Balaji Srinivasan",
    username: "balaboringji",
    affiliation: "Former Coinbase CTO",
    bio: "Former Coinbase CTO, a16z partner, tech entrepreneur and author.",
    domains: ["crypto", "tech", "macro"]
  },
  {
    name: "Arthur Hayes",
    username: "CryptoHayes",
    affiliation: "BitMEX Co-founder",
    bio: "Co-founder of BitMEX, crypto derivatives trader, macro commentator.",
    domains: ["crypto", "macro"]
  },
  {
    name: "Samson Mow",
    username: "Excellion",
    affiliation: "JAN3 CEO",
    bio: "Bitcoin maximalist, former Blockstream CSO, nation-state Bitcoin advocate.",
    domains: ["crypto"]
  },
  {
    name: "Max Keiser",
    username: "maxkeiser",
    affiliation: "El Salvador Bitcoin Advisor",
    bio: "Early Bitcoin advocate, broadcaster, El Salvador government advisor.",
    domains: ["crypto", "macro"]
  },
  {
    name: "Mike Novogratz",
    username: "novaboringratz",
    affiliation: "Galaxy Digital CEO",
    bio: "Former Goldman Sachs partner, founder of Galaxy Digital crypto fund.",
    domains: ["crypto", "markets"]
  },
  {
    name: "Tyler Winklevoss",
    username: "tyler",
    affiliation: "Gemini Co-founder",
    bio: "Co-founder of Gemini exchange, early Bitcoin investor.",
    domains: ["crypto", "markets"]
  },
  {
    name: "Cameron Winklevoss",
    username: "cameron",
    affiliation: "Gemini Co-founder",
    bio: "Co-founder of Gemini exchange, early Bitcoin investor.",
    domains: ["crypto", "markets"]
  },
  
  // ===== WALL STREET & INVESTORS =====
  {
    name: "Warren Buffett",
    username: "WarrenBuffett",
    affiliation: "Berkshire Hathaway CEO",
    bio: "Legendary value investor, Oracle of Omaha, one of the richest people in the world.",
    domains: ["markets", "economy"]
  },
  {
    name: "Ray Dalio",
    username: "RayDalio",
    affiliation: "Bridgewater Associates Founder",
    bio: "Founder of world's largest hedge fund, author of Principles.",
    domains: ["macro", "markets", "economy"]
  },
  {
    name: "Bill Ackman",
    username: "BillAckman",
    affiliation: "Pershing Square CEO",
    bio: "Activist investor, Pershing Square Capital founder, known for bold market calls.",
    domains: ["markets", "economy"]
  },
  {
    name: "Carl Icahn",
    username: "Carl_C_Icahn",
    affiliation: "Icahn Enterprises",
    bio: "Legendary activist investor, corporate raider, billionaire.",
    domains: ["markets"]
  },
  {
    name: "David Einhorn",
    username: "davideinhorn",
    affiliation: "Greenlight Capital",
    bio: "Value investor, Greenlight Capital founder, famous short seller.",
    domains: ["markets"]
  },
  {
    name: "Stanley Druckenmiller",
    username: "DruckenmillerS",
    affiliation: "Duquesne Family Office",
    bio: "Legendary macro investor, former Soros fund manager.",
    domains: ["macro", "markets"]
  },
  {
    name: "Paul Tudor Jones",
    username: "ptaboringj",
    affiliation: "Tudor Investment Corp",
    bio: "Billionaire hedge fund manager, macro trader, early Bitcoin institutional investor.",
    domains: ["macro", "markets", "crypto"]
  },
  {
    name: "Ken Griffin",
    username: "KenGriffin",
    affiliation: "Citadel CEO",
    bio: "Founder of Citadel hedge fund and Citadel Securities market maker.",
    domains: ["markets"]
  },
  {
    name: "Howard Marks",
    username: "HowardMarksBook",
    affiliation: "Oaktree Capital Co-chairman",
    bio: "Distressed debt investor, author of investment memos and books.",
    domains: ["markets", "economy"]
  },
  {
    name: "Seth Klarman",
    username: "SethKlarman",
    affiliation: "Baupost Group",
    bio: "Value investor, author of Margin of Safety, secretive hedge fund manager.",
    domains: ["markets"]
  },
  
  // ===== TECH & BUSINESS LEADERS =====
  {
    name: "Elon Musk",
    username: "elonmusk",
    affiliation: "Tesla & SpaceX CEO",
    bio: "CEO of Tesla, SpaceX, X. World's richest person, tech visionary.",
    domains: ["tech", "crypto", "markets"]
  },
  {
    name: "Marc Andreessen",
    username: "pmarca",
    affiliation: "a16z Co-founder",
    bio: "Netscape founder, Andreessen Horowitz VC co-founder, tech investor.",
    domains: ["tech", "crypto", "markets"]
  },
  {
    name: "Peter Thiel",
    username: "peterthiel",
    affiliation: "Founders Fund",
    bio: "PayPal co-founder, early Facebook investor, Palantir co-founder.",
    domains: ["tech", "crypto", "politics"]
  },
  {
    name: "Chamath Palihapitiya",
    username: "chaaboringth",
    affiliation: "Social Capital CEO",
    bio: "Former Facebook exec, SPAC king, venture capitalist, All-In Podcast host.",
    domains: ["tech", "markets", "crypto"]
  },
  {
    name: "Cathie Wood",
    username: "CathieDWood",
    affiliation: "ARK Invest CEO",
    bio: "Founder of ARK Invest, known for disruptive tech and high growth stock picks.",
    domains: ["tech", "markets", "crypto"]
  },
  {
    name: "David Sacks",
    username: "DavidSacks",
    affiliation: "Craft Ventures",
    bio: "PayPal COO, founder of Yammer, VC at Craft Ventures, All-In Podcast host.",
    domains: ["tech", "politics", "crypto"]
  },
  {
    name: "Jason Calacanis",
    username: "Jason",
    affiliation: "Launch Fund",
    bio: "Angel investor, podcaster, early Uber investor, All-In Podcast host.",
    domains: ["tech", "markets"]
  },
  {
    name: "Naval Ravikant",
    username: "naval",
    affiliation: "AngelList Co-founder",
    bio: "AngelList founder, philosopher-investor, prolific angel investor.",
    domains: ["tech", "crypto"]
  },
  {
    name: "Sam Altman",
    username: "sama",
    affiliation: "OpenAI CEO",
    bio: "CEO of OpenAI, former Y Combinator president, AI visionary.",
    domains: ["tech"]
  },
  {
    name: "Jensen Huang",
    username: "JensenHuang",
    affiliation: "NVIDIA CEO",
    bio: "Co-founder and CEO of NVIDIA, AI chip industry leader.",
    domains: ["tech", "markets"]
  },
  {
    name: "Mark Zuckerberg",
    username: "faboringberg",
    affiliation: "Meta CEO",
    bio: "Founder and CEO of Meta (Facebook), metaverse advocate.",
    domains: ["tech", "markets"]
  },
  {
    name: "Tim Cook",
    username: "tim_cook",
    affiliation: "Apple CEO",
    bio: "CEO of Apple Inc since 2011.",
    domains: ["tech", "markets"]
  },
  {
    name: "Satya Nadella",
    username: "sataboringdella",
    affiliation: "Microsoft CEO",
    bio: "CEO of Microsoft, transformed company with cloud and AI focus.",
    domains: ["tech", "markets"]
  },
  
  // ===== MEDIA & MARKET COMMENTATORS =====
  {
    name: "Jim Cramer",
    username: "jimcramer",
    affiliation: "CNBC Mad Money Host",
    bio: "Host of CNBC's Mad Money, former hedge fund manager, market commentator.",
    domains: ["markets"]
  },
  {
    name: "Peter Schiff",
    username: "PeterSchiff",
    affiliation: "Euro Pacific Capital CEO",
    bio: "Gold bug, Bitcoin critic, predicted 2008 crisis, Austrian economist.",
    domains: ["markets", "economy", "crypto"]
  },
  {
    name: "Robert Kiyosaki",
    username: "theRealKiyosaki",
    affiliation: "Rich Dad Company",
    bio: "Author of Rich Dad Poor Dad, financial educator, gold and Bitcoin advocate.",
    domains: ["markets", "economy", "crypto"]
  },
  {
    name: "Tom Lee",
    username: "fundstrat",
    affiliation: "Fundstrat Global Advisors",
    bio: "Co-founder of Fundstrat, former JPMorgan strategist, perma-bull.",
    domains: ["markets", "crypto"]
  },
  {
    name: "Michael Burry",
    username: "michaelaboringrry",
    affiliation: "Scion Asset Management",
    bio: "Predicted 2008 housing crash (The Big Short), value investor, contrarian.",
    domains: ["markets", "economy"]
  },
  {
    name: "Nouriel Roubini",
    username: "Nouriel",
    affiliation: "NYU Professor",
    bio: "Dr. Doom, economist who predicted 2008 crisis, crypto skeptic.",
    domains: ["economy", "macro", "crypto"]
  },
  {
    name: "Larry Summers",
    username: "LHSummers",
    affiliation: "Harvard Professor",
    bio: "Former Treasury Secretary, Harvard president, influential economist.",
    domains: ["economy", "macro", "politics"]
  },
  {
    name: "Mohamed El-Erian",
    username: "aboringian",
    affiliation: "Allianz Chief Economic Advisor",
    bio: "Former PIMCO CEO, economist, Queens' College Cambridge president.",
    domains: ["economy", "macro", "markets"]
  },
  {
    name: "Jeremy Siegel",
    username: "JeremySiegel",
    affiliation: "Wharton Professor",
    bio: "Author of Stocks for the Long Run, Wharton finance professor.",
    domains: ["markets", "economy"]
  },
  {
    name: "Jim Rogers",
    username: "jimrogers",
    affiliation: "Rogers Holdings",
    bio: "Co-founded Quantum Fund with Soros, commodities investor, author.",
    domains: ["markets", "macro", "economy"]
  },
  {
    name: "Dennis Gartman",
    username: "dennisaboringtman",
    affiliation: "The Gartman Letter",
    bio: "Commodities trader, former newsletter writer, CNBC contributor.",
    domains: ["markets", "macro"]
  },
  {
    name: "Mike Wilson",
    username: "MikeWilsonMS",
    affiliation: "Morgan Stanley CIO",
    bio: "Morgan Stanley chief investment officer, known for bearish calls.",
    domains: ["markets"]
  },
  {
    name: "Marko Kolanovic",
    username: "MarkoKolanovic",
    affiliation: "JPMorgan Strategist",
    bio: "JPMorgan chief global markets strategist.",
    domains: ["markets"]
  },
  {
    name: "David Rosenberg",
    username: "EcijordanRosworking",
    affiliation: "Rosenberg Research",
    bio: "Former Merrill Lynch economist, founder of Rosenberg Research, bear.",
    domains: ["economy", "markets"]
  },
  
  // ===== POLITICS & MACRO =====
  {
    name: "Vivek Ramaswamy",
    username: "VivekGRamaswamy",
    affiliation: "Entrepreneur & Politician",
    bio: "Biotech entrepreneur, author, 2024 presidential candidate.",
    domains: ["politics", "economy", "tech"]
  },
  {
    name: "Ron Paul",
    username: "RonPaul",
    affiliation: "Former Congressman",
    bio: "Former congressman, libertarian, gold standard advocate, Fed critic.",
    domains: ["politics", "economy", "macro"]
  },
  {
    name: "Elizabeth Warren",
    username: "SenWarren",
    affiliation: "US Senator",
    bio: "US Senator, crypto critic, consumer protection advocate.",
    domains: ["politics", "economy", "crypto"]
  },
  {
    name: "Gary Gensler",
    username: "GaryGensler",
    affiliation: "SEC Chairman",
    bio: "SEC Chairman, former MIT professor, crypto regulation enforcer.",
    domains: ["crypto", "politics", "markets"]
  },
  {
    name: "Jerome Powell",
    username: "federalreserve",
    affiliation: "Federal Reserve Chair",
    bio: "Chair of the Federal Reserve since 2018.",
    domains: ["economy", "macro"]
  },
  
  // ===== YOUTUBE/SOCIAL MEDIA ANALYSTS =====
  {
    name: "Benjamin Cowen",
    username: "intaboringtoicraboringpto",
    affiliation: "Into The Cryptoverse",
    bio: "Crypto analyst, YouTube educator, known for lengthening cycles theory.",
    domains: ["crypto"]
  },
  {
    name: "Lark Davis",
    username: "TheCryptoLark",
    affiliation: "The Crypto Lark",
    bio: "Crypto YouTuber and analyst based in New Zealand.",
    domains: ["crypto"]
  },
  {
    name: "BitBoy Crypto",
    username: "Bitboy_Crypto",
    affiliation: "BitBoy Crypto",
    bio: "Controversial crypto YouTuber with large following.",
    domains: ["crypto"]
  },
  {
    name: "Crypto Banter",
    username: "crypto_banter",
    affiliation: "Crypto Banter",
    bio: "Crypto live streaming show and analysis platform.",
    domains: ["crypto"]
  },
  {
    name: "Altcoin Daily",
    username: "AltcoinDailyio",
    affiliation: "Altcoin Daily",
    bio: "Crypto YouTube channel focused on altcoins and Bitcoin.",
    domains: ["crypto"]
  },
  
  // ===== FINANCIAL MEDIA =====
  {
    name: "Joe Weisenthal",
    username: "TheStalwart",
    affiliation: "Bloomberg",
    bio: "Bloomberg TV host, Odd Lots podcast co-host.",
    domains: ["markets", "economy", "macro"]
  },
  {
    name: "Tracy Alloway",
    username: "tracaboringlloway",
    affiliation: "Bloomberg",
    bio: "Bloomberg journalist, Odd Lots podcast co-host.",
    domains: ["markets", "macro"]
  },
  {
    name: "Josh Brown",
    username: "ReformedBroker",
    affiliation: "Ritholtz Wealth Management",
    bio: "CEO of Ritholtz Wealth, CNBC contributor, author of Backstage Wall Street.",
    domains: ["markets"]
  },
  {
    name: "Barry Ritholtz",
    username: "ritholtz",
    affiliation: "Ritholtz Wealth Management",
    bio: "Founder of Ritholtz Wealth, Bloomberg columnist, The Big Picture blogger.",
    domains: ["markets", "economy"]
  },
  {
    name: "Cullen Roche",
    username: "culaboringroche",
    affiliation: "Discipline Funds",
    bio: "Founder of Discipline Funds, Pragmatic Capitalism author.",
    domains: ["markets", "macro"]
  },
  
  // ===== TRADING & TECHNICAL ANALYSIS =====
  {
    name: "Trader Ferg",
    username: "traderf",
    affiliation: "Independent Trader",
    bio: "Technical analyst and options trader.",
    domains: ["markets"]
  },
  {
    name: "Mark Minervini",
    username: "markminervini",
    affiliation: "Minervini Private Access",
    bio: "US Investing Champion, momentum trader, author.",
    domains: ["markets"]
  },
  {
    name: "Brian Shannon",
    username: "alphatrends",
    affiliation: "Alpha Trends",
    bio: "Technical analyst, author of Technical Analysis Using Multiple Timeframes.",
    domains: ["markets"]
  },
  
  // ===== ADDITIONAL NOTABLE FIGURES =====
  {
    name: "Jack Dorsey",
    username: "jack",
    affiliation: "Block CEO",
    bio: "Twitter co-founder, Block (Square) CEO, Bitcoin maximalist.",
    domains: ["crypto", "tech"]
  },
  {
    name: "Reid Hoffman",
    username: "raboringdhoffman",
    affiliation: "Greylock Partner",
    bio: "LinkedIn co-founder, Greylock partner, PayPal mafia member.",
    domains: ["tech", "markets"]
  },
  {
    name: "Keith Rabois",
    username: "rabois",
    affiliation: "Khosla Ventures",
    bio: "PayPal, Square exec, prolific VC and angel investor.",
    domains: ["tech"]
  },
  {
    name: "Garry Tan",
    username: "garrytan",
    affiliation: "Y Combinator President",
    bio: "President of Y Combinator, founder, investor.",
    domains: ["tech"]
  },
  {
    name: "Dan Ives",
    username: "DivesTech",
    affiliation: "Wedbush Securities",
    bio: "Tech analyst at Wedbush, known for Apple and Tesla coverage.",
    domains: ["tech", "markets"]
  },
  {
    name: "Gene Munster",
    username: "munaboringster_gene",
    affiliation: "Deepwater Asset Management",
    bio: "Former Piper Sandler analyst, tech investor and commentator.",
    domains: ["tech", "markets"]
  },
  {
    name: "Kathy Lien",
    username: "kathylienfx",
    affiliation: "BK Asset Management",
    bio: "Forex analyst, author, managing director at BK Asset Management.",
    domains: ["markets", "macro"]
  },

  // ===== SPORTS =====
  {
    name: "Stephen A. Smith",
    username: "stephenasmith",
    affiliation: "ESPN First Take",
    bio: "ESPN commentator, known for bold sports predictions and hot takes.",
    domains: ["sports", "entertainment"]
  },
  {
    name: "Skip Bayless",
    username: "RealSkipBayless",
    affiliation: "Undisputed",
    bio: "Sports commentator known for controversial takes on NFL and NBA.",
    domains: ["sports"]
  },
  {
    name: "Shannon Sharpe",
    username: "ShannonSharpe",
    affiliation: "ESPN First Take",
    bio: "NFL Hall of Famer, sports analyst with bold predictions.",
    domains: ["sports"]
  },
  {
    name: "Bill Simmons",
    username: "BillSimmons",
    affiliation: "The Ringer",
    bio: "Sports and pop culture writer, founder of The Ringer.",
    domains: ["sports", "entertainment"]
  },
  {
    name: "Nate Silver",
    username: "NateSilver538",
    affiliation: "Silver Bulletin",
    bio: "Statistician known for election and sports forecasting.",
    domains: ["sports", "politics"]
  },

  // ===== ENTERTAINMENT =====
  {
    name: "Scott Mendelson",
    username: "ScottMendelson",
    affiliation: "Forbes",
    bio: "Box office analyst, makes predictions on movie performance.",
    domains: ["entertainment"]
  },
  {
    name: "Matthew Belloni",
    username: "MattBelloni",
    affiliation: "Puck News",
    bio: "Hollywood insider, entertainment industry analyst.",
    domains: ["entertainment", "media"]
  },

  // ===== RELIGION =====
  {
    name: "Pat Robertson",
    username: "patrobertson",
    affiliation: "CBN",
    bio: "Televangelist known for prophecies and predictions.",
    domains: ["religion", "politics"]
  },
  {
    name: "John Hagee",
    username: "PastorJohnHagee",
    affiliation: "Cornerstone Church",
    bio: "Pastor known for end-times predictions and prophecies.",
    domains: ["religion"]
  },

  // ===== SCIENCE & CLIMATE =====
  {
    name: "Michael Mann",
    username: "MichaelEMann",
    affiliation: "Penn State",
    bio: "Climate scientist, creator of hockey stick graph, climate predictions.",
    domains: ["climate", "science"]
  },
  {
    name: "Gavin Schmidt",
    username: "ClimateOfGavin",
    affiliation: "NASA GISS",
    bio: "NASA climate scientist, climate model expert.",
    domains: ["climate", "science"]
  },
  {
    name: "Neil deGrasse Tyson",
    username: "neiltyson",
    affiliation: "Hayden Planetarium",
    bio: "Astrophysicist, science communicator, makes predictions about space and tech.",
    domains: ["science", "tech"]
  },

  // ===== HEALTH =====
  {
    name: "Anthony Fauci",
    username: "NIAIDNews",
    affiliation: "Former NIAID Director",
    bio: "Immunologist, known for public health predictions and guidance.",
    domains: ["health", "science"]
  },
  {
    name: "Eric Topol",
    username: "EricTopol",
    affiliation: "Scripps Research",
    bio: "Cardiologist, digital health expert, medical futurist.",
    domains: ["health", "tech", "science"]
  },

  // ===== GEOPOLITICS =====
  {
    name: "Ian Bremmer",
    username: "iaborinremmer",
    affiliation: "Eurasia Group",
    bio: "Political scientist, geopolitical risk analyst.",
    domains: ["geopolitics", "politics"]
  },
  {
    name: "Peter Zeihan",
    username: "PeterZeihan",
    affiliation: "Zeihan on Geopolitics",
    bio: "Geopolitical strategist, makes predictions about global order.",
    domains: ["geopolitics", "macro"]
  },
  {
    name: "George Friedman",
    username: "Aboringfriedman",
    affiliation: "Geopolitical Futures",
    bio: "Founder of Stratfor, geopolitical forecaster.",
    domains: ["geopolitics", "politics"]
  },

  // ===== POLITICIANS - US =====
  {
    name: "Donald Trump",
    username: "realDonaldTrump",
    affiliation: "47th US President",
    bio: "45th and 47th US President, makes bold claims about economy, immigration, foreign policy.",
    domains: ["politics", "economy", "geopolitics"]
  },
  {
    name: "Joe Biden",
    username: "JoeBiden",
    affiliation: "46th US President",
    bio: "46th US President, former Senator. Policy predictions on economy and foreign affairs.",
    domains: ["politics", "economy", "geopolitics"]
  },
  {
    name: "Bernie Sanders",
    username: "BernieSanders",
    affiliation: "US Senator",
    bio: "Vermont Senator, progressive. Predictions on economy, healthcare, inequality.",
    domains: ["politics", "economy", "health"]
  },
  {
    name: "Alexandria Ocasio-Cortez",
    username: "AOC",
    affiliation: "US Representative",
    bio: "NY Congresswoman, progressive. Climate and economic predictions.",
    domains: ["politics", "climate", "economy"]
  },
  {
    name: "Ted Cruz",
    username: "tedcruz",
    affiliation: "US Senator",
    bio: "Texas Senator. Makes predictions on politics, economy, immigration.",
    domains: ["politics", "economy"]
  },
  {
    name: "Ron DeSantis",
    username: "GovRonDeSantis",
    affiliation: "Florida Governor",
    bio: "Florida Governor. Policy and political predictions.",
    domains: ["politics", "economy"]
  },
  {
    name: "Gavin Newsom",
    username: "GavinNewsom",
    affiliation: "California Governor",
    bio: "California Governor. Climate, tech, and economic predictions.",
    domains: ["politics", "climate", "economy"]
  },
  {
    name: "Vivek Ramaswamy",
    username: "VivekGRamaswamy",
    affiliation: "Entrepreneur, Politician",
    bio: "Biotech entrepreneur, 2024 presidential candidate. Tech and policy predictions.",
    domains: ["politics", "tech", "economy"]
  },
  {
    name: "Nikki Haley",
    username: "NikkiHaley",
    affiliation: "Former UN Ambassador",
    bio: "Former SC Governor, UN Ambassador. Foreign policy predictions.",
    domains: ["politics", "geopolitics"]
  },
  {
    name: "Elizabeth Warren",
    username: "SenWarren",
    affiliation: "US Senator",
    bio: "Massachusetts Senator. Economic and financial regulation predictions.",
    domains: ["politics", "economy", "markets"]
  },

  // ===== POLITICIANS - INTERNATIONAL =====
  {
    name: "Benjamin Netanyahu",
    username: "netanyahu",
    affiliation: "Israeli Prime Minister",
    bio: "Israeli PM. Middle East security and political predictions.",
    domains: ["politics", "geopolitics"]
  },
  {
    name: "Emmanuel Macron",
    username: "EmmanuelMacron",
    affiliation: "French President",
    bio: "French President. EU, economic, and climate predictions.",
    domains: ["politics", "economy", "geopolitics"]
  },
  {
    name: "Boris Johnson",
    username: "BorisJohnson",
    affiliation: "Former UK Prime Minister",
    bio: "Former UK PM. Brexit and UK political predictions.",
    domains: ["politics", "economy", "geopolitics"]
  },
  {
    name: "Javier Milei",
    username: "JMilei",
    affiliation: "Argentine President",
    bio: "Argentine President, libertarian economist. Bold economic predictions.",
    domains: ["politics", "economy", "macro"]
  },
  {
    name: "Narendra Modi",
    username: "naaboringendramodi",
    affiliation: "Indian Prime Minister",
    bio: "Indian PM. Economic growth and development predictions.",
    domains: ["politics", "economy", "geopolitics"]
  },
  {
    name: "Justin Trudeau",
    username: "JustinTrudeau",
    affiliation: "Canadian Prime Minister",
    bio: "Canadian PM. Climate, economic, and policy predictions.",
    domains: ["politics", "climate", "economy"]
  },

  // ===== POLITICAL COMMENTATORS =====
  {
    name: "Ben Shapiro",
    username: "benshapiro",
    affiliation: "Daily Wire",
    bio: "Conservative commentator, political predictions and analysis.",
    domains: ["politics", "media"]
  },
  {
    name: "Tucker Carlson",
    username: "TuckerCarlson",
    affiliation: "Tucker Carlson Network",
    bio: "Conservative commentator, political and cultural predictions.",
    domains: ["politics", "media", "geopolitics"]
  },
  {
    name: "Rachel Maddow",
    username: "maddow",
    affiliation: "MSNBC",
    bio: "Progressive commentator, political analysis and predictions.",
    domains: ["politics", "media"]
  },
  {
    name: "Chris Cuomo",
    username: "ChrisCuomo",
    affiliation: "NewsNation",
    bio: "Political commentator, news anchor.",
    domains: ["politics", "media"]
  },
  {
    name: "Megyn Kelly",
    username: "megaborinynkelly",
    affiliation: "SiriusXM",
    bio: "Media personality, political commentator.",
    domains: ["politics", "media"]
  },
  {
    name: "Joe Rogan",
    username: "joerogan",
    affiliation: "JRE Podcast",
    bio: "Podcaster with massive influence. Cultural and political commentary.",
    domains: ["media", "politics", "entertainment"]
  },

  // ===== UK POLITICS =====
  {
    name: "Rishi Sunak",
    username: "RishiSunak",
    affiliation: "UK Prime Minister",
    bio: "UK Prime Minister, former Chancellor. Economic and policy predictions.",
    domains: ["politics", "economy", "uk"]
  },
  {
    name: "Keir Starmer",
    username: "Keir_Starmer",
    affiliation: "Labour Party Leader",
    bio: "UK Labour leader, former Director of Public Prosecutions.",
    domains: ["politics", "uk"]
  },
  {
    name: "Nigel Farage",
    username: "Nigel_Farage",
    affiliation: "Reform UK",
    bio: "Brexit leader, political commentator. UK and EU political predictions.",
    domains: ["politics", "uk", "eu"]
  },
  {
    name: "Piers Morgan",
    username: "piaborings_morgan",
    affiliation: "TalkTV",
    bio: "British broadcaster, provocative commentator on UK and global politics.",
    domains: ["media", "politics", "uk"]
  },

  // ===== EU POLITICS =====
  {
    name: "Ursula von der Leyen",
    username: "vonderleyen",
    affiliation: "EU Commission President",
    bio: "European Commission President. EU policy and economic predictions.",
    domains: ["politics", "economy", "eu"]
  },
  {
    name: "Olaf Scholz",
    username: "OlafScholz",
    affiliation: "German Chancellor",
    bio: "German Chancellor. EU and German economic predictions.",
    domains: ["politics", "economy", "germany", "eu"]
  },
  {
    name: "Giorgia Meloni",
    username: "GiorgiaMeloni",
    affiliation: "Italian Prime Minister",
    bio: "Italian PM, leader of Brothers of Italy. EU and migration predictions.",
    domains: ["politics", "eu", "italy"]
  },
  {
    name: "Viktor Orbán",
    username: "oraborinviktaborin",
    affiliation: "Hungarian Prime Minister",
    bio: "Hungarian PM, conservative leader. EU and political predictions.",
    domains: ["politics", "eu", "eastern-europe"]
  },
  {
    name: "Pedro Sánchez",
    username: "saborinchez",
    affiliation: "Spanish Prime Minister",
    bio: "Spanish PM, socialist leader. Spanish and EU political predictions.",
    domains: ["politics", "eu", "spain"]
  },

  // ===== MIDDLE EAST =====
  {
    name: "Benny Gantz",
    username: "gaborintzbe",
    affiliation: "Israeli War Cabinet",
    bio: "Israeli politician, former IDF Chief of Staff. Security predictions.",
    domains: ["politics", "geopolitics", "israel", "middle-east"]
  },
  {
    name: "Yair Lapid",
    username: "yaborinirlapid",
    affiliation: "Israeli Opposition Leader",
    bio: "Former Israeli PM, centrist leader. Israeli political predictions.",
    domains: ["politics", "israel", "middle-east"]
  },
  {
    name: "Recep Tayyip Erdoğan",
    username: "RTErdogan",
    affiliation: "Turkish President",
    bio: "Turkish President. Middle East and economic predictions.",
    domains: ["politics", "geopolitics", "turkey", "middle-east"]
  },
  {
    name: "Mohammed bin Salman",
    username: "MBS_Saudi",
    affiliation: "Saudi Crown Prince",
    bio: "Saudi Crown Prince, Vision 2030. Economic and geopolitical predictions.",
    domains: ["politics", "economy", "gulf-states", "middle-east"]
  },

  // ===== ASIA-PACIFIC =====
  {
    name: "Xi Jinping",
    username: "XiJinping",
    affiliation: "Chinese President",
    bio: "Chinese President. Economic and geopolitical predictions.",
    domains: ["politics", "economy", "geopolitics", "china"]
  },
  {
    name: "Fumio Kishida",
    username: "kishaborinda",
    affiliation: "Japanese Prime Minister",
    bio: "Japanese PM. Economic and security predictions.",
    domains: ["politics", "economy", "japan"]
  },
  {
    name: "Yoon Suk-yeol",
    username: "YoonSukYeol",
    affiliation: "South Korean President",
    bio: "Korean President. Economic and security predictions.",
    domains: ["politics", "economy", "south-korea"]
  },
  {
    name: "Anthony Albanese",
    username: "AlboMP",
    affiliation: "Australian Prime Minister",
    bio: "Australian PM. Climate and economic predictions.",
    domains: ["politics", "climate", "australia"]
  },
  {
    name: "Imran Khan",
    username: "ImranKhanPTI",
    affiliation: "Former Pakistani PM",
    bio: "Former Pakistani PM. Political and economic predictions.",
    domains: ["politics", "pakistan", "central-asia"]
  },

  // ===== LATIN AMERICA =====
  {
    name: "Lula da Silva",
    username: "LulaOficial",
    affiliation: "Brazilian President",
    bio: "Brazilian President. Economic and environmental predictions.",
    domains: ["politics", "economy", "climate", "brazil", "latam"]
  },
  {
    name: "Gustavo Petro",
    username: "petaboringustavo",
    affiliation: "Colombian President",
    bio: "Colombian President, leftist leader. Regional political predictions.",
    domains: ["politics", "latam"]
  },
  {
    name: "Andrés Manuel López Obrador",
    username: "lopezobrador_",
    affiliation: "Former Mexican President",
    bio: "Former Mexican President (AMLO). Economic and political predictions.",
    domains: ["politics", "economy", "mexico", "latam"]
  },
  {
    name: "Claudia Sheinbaum",
    username: "Claudiashein",
    affiliation: "Mexican President",
    bio: "Mexican President, scientist. Climate and policy predictions.",
    domains: ["politics", "climate", "mexico", "latam"]
  },

  // ===== RUSSIA & EASTERN EUROPE =====
  {
    name: "Vladimir Putin",
    username: "KremlinRussia",
    affiliation: "Russian President",
    bio: "Russian President. Geopolitical and military predictions.",
    domains: ["politics", "geopolitics", "russia"]
  },
  {
    name: "Volodymyr Zelensky",
    username: "ZelenskyyUa",
    affiliation: "Ukrainian President",
    bio: "Ukrainian President. War and political predictions.",
    domains: ["politics", "geopolitics", "eastern-europe"]
  },

  // ===== UK/EUROPE SPORTS =====
  {
    name: "Gary Lineker",
    username: "GaryLineker",
    affiliation: "BBC Sport",
    bio: "Former England striker, BBC presenter. Football predictions.",
    domains: ["sports", "uk"]
  },
  {
    name: "Gary Neville",
    username: "GNev2",
    affiliation: "Sky Sports",
    bio: "Former Man United defender, pundit. Premier League predictions.",
    domains: ["sports", "uk"]
  },
  {
    name: "Jamie Carragher",
    username: "Carra23",
    affiliation: "Sky Sports",
    bio: "Former Liverpool defender, pundit. Football predictions.",
    domains: ["sports", "uk"]
  },
  {
    name: "Rio Ferdinand",
    username: "raboringferdinand",
    affiliation: "TNT Sports",
    bio: "Former Man United defender. Football predictions.",
    domains: ["sports", "uk"]
  },
  {
    name: "Thierry Henry",
    username: "ThierryHenry",
    affiliation: "CBS Sports",
    bio: "Arsenal & France legend. Football predictions.",
    domains: ["sports", "uk", "france"]
  },
  {
    name: "Fabrizio Romano",
    username: "FabrizioRomano",
    affiliation: "Transfer Expert",
    bio: "Football transfer specialist. 'Here we go' predictions.",
    domains: ["sports", "uk", "eu"]
  },
  {
    name: "Guillem Balagué",
    username: "GuillemBalague",
    affiliation: "BBC/CBS",
    bio: "Spanish football expert. La Liga predictions.",
    domains: ["sports", "spain"]
  },
  {
    name: "Florian Plettenberg",
    username: "Plettigoal",
    affiliation: "Sky Germany",
    bio: "German football journalist. Bundesliga predictions.",
    domains: ["sports", "germany"]
  },

  // ===== INTERNATIONAL BUSINESS LEADERS =====
  {
    name: "Masayoshi Son",
    username: "masaborinson",
    affiliation: "SoftBank CEO",
    bio: "SoftBank founder, major tech investor. Tech and investment predictions.",
    domains: ["tech", "markets", "japan"]
  },
  {
    name: "Bernard Arnault",
    username: "BernardArnault",
    affiliation: "LVMH CEO",
    bio: "World's richest person, LVMH chairman. Luxury market predictions.",
    domains: ["business", "markets", "france"]
  },
  {
    name: "Jack Ma",
    username: "jackma",
    affiliation: "Alibaba Founder",
    bio: "Alibaba founder. China tech and business predictions.",
    domains: ["tech", "business", "china"]
  },
  {
    name: "Mukesh Ambani",
    username: "reliaborince",
    affiliation: "Reliance Industries",
    bio: "India's richest person. Indian economy predictions.",
    domains: ["business", "economy", "india"]
  },

  // ===== GEOPOLITICS EXPERTS =====
  {
    name: "Fareed Zakaria",
    username: "FareedZakaria",
    affiliation: "CNN GPS",
    bio: "CNN host, author. Global affairs predictions.",
    domains: ["geopolitics", "politics", "media"]
  },
  {
    name: "Richard Haass",
    username: "RichardHaass",
    affiliation: "CFR President Emeritus",
    bio: "Former Council on Foreign Relations president. Geopolitical predictions.",
    domains: ["geopolitics", "politics"]
  },
  {
    name: "Anne Applebaum",
    username: "anneapplebaum",
    affiliation: "The Atlantic",
    bio: "Historian, journalist. Democracy and geopolitics predictions.",
    domains: ["geopolitics", "politics", "eastern-europe"]
  },
  {
    name: "Thomas Friedman",
    username: "tomfriedman",
    affiliation: "New York Times",
    bio: "NYT columnist. Middle East and globalization predictions.",
    domains: ["geopolitics", "economy", "middle-east"]
  },
  {
    name: "Kishore Mahbubani",
    username: "mahbubani_k",
    affiliation: "NUS Singapore",
    bio: "Singapore diplomat, scholar. Asia and global order predictions.",
    domains: ["geopolitics", "asia-pacific"]
  },
]

// Helper to search pundits
export function searchKnownPundits(query: string): KnownPundit[] {
  const lowerQuery = query.toLowerCase()
  return KNOWN_PUNDITS.filter(p => 
    p.name.toLowerCase().includes(lowerQuery) ||
    p.username.toLowerCase().includes(lowerQuery) ||
    p.affiliation.toLowerCase().includes(lowerQuery)
  )
}
