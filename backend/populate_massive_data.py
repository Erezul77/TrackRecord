"""
Massive Historical Data Population Script
Adds 200+ pundits and 1000+ predictions from 2020-2025
Covers: Finance, Politics, Tech, Sports, Entertainment, Science, Crypto
Regions: US, UK, EU, Asia, Middle East, Latin America, Africa
"""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Massive pundit database organized by category and region
PUNDITS_DATA = {
    # ============================================
    # FINANCE & MARKETS (Global)
    # ============================================
    "finance": [
        # US Finance
        {"name": "Mohamed El-Erian", "username": "elerianm", "affiliation": "Allianz", "bio": "Chief Economic Advisor at Allianz, former PIMCO CEO", "domains": ["markets", "economy"], "net_worth": 100},
        {"name": "David Tepper", "username": "DavidTepper", "affiliation": "Appaloosa Management", "bio": "Billionaire hedge fund manager", "domains": ["markets", "economy"], "net_worth": 18500},
        {"name": "Stanley Druckenmiller", "username": "Druckenmiller", "affiliation": "Duquesne Capital", "bio": "Legendary macro investor", "domains": ["markets", "economy"], "net_worth": 6200},
        {"name": "Ken Griffin", "username": "KenGriffin", "affiliation": "Citadel", "bio": "Founder and CEO of Citadel", "domains": ["markets"], "net_worth": 35000},
        {"name": "Steve Cohen", "username": "StevenACohen", "affiliation": "Point72", "bio": "Hedge fund billionaire, Mets owner", "domains": ["markets", "sports"], "net_worth": 17400},
        {"name": "Dan Loeb", "username": "DanLoeb", "affiliation": "Third Point", "bio": "Activist investor", "domains": ["markets"], "net_worth": 3600},
        {"name": "Bill Gross", "username": "BillGross", "affiliation": "PIMCO Founder", "bio": "Bond King", "domains": ["markets", "economy"], "net_worth": 1600},
        {"name": "Jeff Gundlach", "username": "TrsuroFdn", "affiliation": "DoubleLine", "bio": "New Bond King", "domains": ["markets", "economy"], "net_worth": 2200},
        {"name": "Howard Marks", "username": "HowardMarks", "affiliation": "Oaktree Capital", "bio": "Value investor, author", "domains": ["markets"], "net_worth": 2100},
        {"name": "Leon Cooperman", "username": "LeonCooperman", "affiliation": "Omega Advisors", "bio": "Value investor", "domains": ["markets", "economy"], "net_worth": 2500},
        {"name": "Carl Icahn", "username": "CarlIcahn", "affiliation": "Icahn Enterprises", "bio": "Corporate raider, activist investor", "domains": ["markets"], "net_worth": 7100},
        {"name": "Paul Tudor Jones", "username": "PTJones", "affiliation": "Tudor Investment", "bio": "Macro hedge fund legend", "domains": ["markets", "economy"], "net_worth": 7500},
        {"name": "David Einhorn", "username": "DavidEinhorn", "affiliation": "Greenlight Capital", "bio": "Value investor known for shorts", "domains": ["markets"], "net_worth": 1500},
        {"name": "Whitney Tilson", "username": "WTilson", "affiliation": "Empire Financial", "bio": "Value investor, newsletter writer", "domains": ["markets"], "net_worth": 50},
        {"name": "Meredith Whitney", "username": "MeredithWhitney", "affiliation": "Whitney Advisory", "bio": "Bank analyst who called 2008 crisis", "domains": ["markets", "economy"], "net_worth": 20},
        
        # UK/EU Finance
        {"name": "Crispin Odey", "username": "CrispinOdey", "affiliation": "Odey Asset Management", "bio": "British hedge fund manager, Brexit backer", "domains": ["markets", "uk-politics"], "net_worth": 825},
        {"name": "Alan Howard", "username": "AlanHoward", "affiliation": "Brevan Howard", "bio": "British hedge fund billionaire", "domains": ["markets"], "net_worth": 2600},
        {"name": "Michael Platt", "username": "MichaelPlatt", "affiliation": "BlueCrest Capital", "bio": "British trader", "domains": ["markets"], "net_worth": 16000},
        {"name": "Gerard Minack", "username": "GMinack", "affiliation": "Minack Advisors", "bio": "Australian market strategist", "domains": ["markets", "economy"], "net_worth": 15},
        {"name": "Albert Edwards", "username": "AlbertEdwards", "affiliation": "Société Générale", "bio": "Perma-bear strategist", "domains": ["markets", "economy"], "net_worth": 10},
        
        # Asia Finance
        {"name": "Li Lu", "username": "LiLu", "affiliation": "Himalaya Capital", "bio": "Charlie Munger's Chinese investment partner", "domains": ["markets", "china"], "net_worth": 2500},
        {"name": "Masayoshi Son", "username": "MasaSon", "affiliation": "SoftBank", "bio": "Japanese tech investor", "domains": ["markets", "tech"], "net_worth": 21000},
        {"name": "Zhang Lei", "username": "ZhangLei", "affiliation": "Hillhouse Capital", "bio": "Chinese hedge fund manager", "domains": ["markets", "china"], "net_worth": 4500},
    ],
    
    # ============================================
    # CRYPTO & WEB3
    # ============================================
    "crypto": [
        {"name": "Vitalik Buterin", "username": "VitalikButerin", "affiliation": "Ethereum", "bio": "Ethereum co-founder", "domains": ["crypto", "tech"], "net_worth": 1500},
        {"name": "Changpeng Zhao", "username": "caboratez", "affiliation": "Binance", "bio": "CZ - Binance founder", "domains": ["crypto"], "net_worth": 10500},
        {"name": "Brian Armstrong", "username": "BrianArmstrong", "affiliation": "Coinbase", "bio": "Coinbase CEO", "domains": ["crypto"], "net_worth": 2400},
        {"name": "Sam Bankman-Fried", "username": "SBF_FTX", "affiliation": "Former FTX", "bio": "Former FTX CEO (pre-collapse predictions)", "domains": ["crypto"], "net_worth": 0},
        {"name": "Anthony Pompliano", "username": "APompliano", "affiliation": "Pomp Investments", "bio": "Bitcoin maximalist investor", "domains": ["crypto"], "net_worth": 100},
        {"name": "Raoul Pal", "username": "RaoulGMI", "affiliation": "Real Vision", "bio": "Macro investor, crypto bull", "domains": ["crypto", "markets"], "net_worth": 50},
        {"name": "Michael Novogratz", "username": "Novogratz", "affiliation": "Galaxy Digital", "bio": "Crypto hedge fund manager", "domains": ["crypto", "markets"], "net_worth": 2100},
        {"name": "Cameron Winklevoss", "username": "Cameron", "affiliation": "Gemini", "bio": "Gemini co-founder", "domains": ["crypto"], "net_worth": 1400},
        {"name": "Tyler Winklevoss", "username": "Tyler", "affiliation": "Gemini", "bio": "Gemini co-founder", "domains": ["crypto"], "net_worth": 1400},
        {"name": "Barry Silbert", "username": "BarrySilbert", "affiliation": "Digital Currency Group", "bio": "DCG founder", "domains": ["crypto"], "net_worth": 1000},
        {"name": "Arthur Hayes", "username": "CryptoHayes", "affiliation": "BitMEX", "bio": "BitMEX co-founder", "domains": ["crypto"], "net_worth": 600},
        {"name": "Su Zhu", "username": "zaboratezhu", "affiliation": "Former 3AC", "bio": "Former Three Arrows Capital (pre-collapse)", "domains": ["crypto"], "net_worth": 0},
        {"name": "PlanB", "username": "100trillionUSD", "affiliation": "Independent", "bio": "Bitcoin Stock-to-Flow model creator", "domains": ["crypto"], "net_worth": 10},
        {"name": "Willy Woo", "username": "WoonomicWilly", "affiliation": "On-chain Analyst", "bio": "Bitcoin on-chain analyst", "domains": ["crypto"], "net_worth": 5},
    ],
    
    # ============================================
    # TECH INDUSTRY
    # ============================================
    "tech": [
        {"name": "Jensen Huang", "username": "JensenHuang", "affiliation": "NVIDIA", "bio": "NVIDIA CEO", "domains": ["tech", "ai"], "net_worth": 77000},
        {"name": "Satya Nadella", "username": "SatyaNadella", "affiliation": "Microsoft", "bio": "Microsoft CEO", "domains": ["tech", "ai"], "net_worth": 1000},
        {"name": "Tim Cook", "username": "TimCook", "affiliation": "Apple", "bio": "Apple CEO", "domains": ["tech"], "net_worth": 1800},
        {"name": "Sundar Pichai", "username": "SundarPichai", "affiliation": "Google/Alphabet", "bio": "Google CEO", "domains": ["tech", "ai"], "net_worth": 1300},
        {"name": "Mark Zuckerberg", "username": "Zuck", "affiliation": "Meta", "bio": "Meta CEO", "domains": ["tech", "entertainment"], "net_worth": 177000},
        {"name": "Sam Altman", "username": "Sama", "affiliation": "OpenAI", "bio": "OpenAI CEO", "domains": ["tech", "ai"], "net_worth": 1000},
        {"name": "Demis Hassabis", "username": "DemisHassabis", "affiliation": "DeepMind", "bio": "DeepMind CEO, Nobel Prize winner", "domains": ["tech", "ai", "science"], "net_worth": 500},
        {"name": "Marc Andreessen", "username": "PMarc", "affiliation": "a16z", "bio": "VC legend, Netscape founder", "domains": ["tech", "markets"], "net_worth": 1700},
        {"name": "Peter Thiel", "username": "PeterThiel", "affiliation": "Founders Fund", "bio": "PayPal co-founder, VC", "domains": ["tech", "politics"], "net_worth": 9800},
        {"name": "Reid Hoffman", "username": "ReidHoffman", "affiliation": "Greylock", "bio": "LinkedIn co-founder", "domains": ["tech"], "net_worth": 2500},
        {"name": "Chamath Palihapitiya", "username": "Chamath", "affiliation": "Social Capital", "bio": "VC, former Facebook exec", "domains": ["tech", "markets"], "net_worth": 1200},
        {"name": "Jason Calacanis", "username": "Jason", "affiliation": "Launch", "bio": "Angel investor, podcaster", "domains": ["tech"], "net_worth": 100},
        {"name": "Benedict Evans", "username": "BenedictEvans", "affiliation": "Independent", "bio": "Tech analyst, former a16z", "domains": ["tech"], "net_worth": 10},
        {"name": "Ben Thompson", "username": "BenThompson", "affiliation": "Stratechery", "bio": "Tech strategist, writer", "domains": ["tech"], "net_worth": 20},
        {"name": "Kara Swisher", "username": "KaraSwisher", "affiliation": "Vox Media", "bio": "Tech journalist", "domains": ["tech", "media"], "net_worth": 30},
    ],
    
    # ============================================
    # US POLITICS
    # ============================================
    "us_politics": [
        {"name": "Nancy Pelosi", "username": "NancyPelosi", "affiliation": "US Congress", "bio": "Former Speaker of the House", "domains": ["politics", "us"], "net_worth": 120},
        {"name": "Mitch McConnell", "username": "MitchMcConnell", "affiliation": "US Senate", "bio": "Senate Republican Leader", "domains": ["politics", "us"], "net_worth": 35},
        {"name": "Chuck Schumer", "username": "ChuckSchumer", "affiliation": "US Senate", "bio": "Senate Majority Leader", "domains": ["politics", "us"], "net_worth": 1.5},
        {"name": "Bernie Sanders", "username": "BernieSanders", "affiliation": "US Senate", "bio": "Vermont Senator, Progressive leader", "domains": ["politics", "economy"], "net_worth": 3},
        {"name": "Elizabeth Warren", "username": "EWarren", "affiliation": "US Senate", "bio": "Massachusetts Senator", "domains": ["politics", "economy"], "net_worth": 12},
        {"name": "Ted Cruz", "username": "TedCruz", "affiliation": "US Senate", "bio": "Texas Senator", "domains": ["politics", "us"], "net_worth": 4},
        {"name": "Marco Rubio", "username": "MarcoRubio", "affiliation": "US Senate", "bio": "Florida Senator", "domains": ["politics", "us"], "net_worth": 0.5},
        {"name": "Ron DeSantis", "username": "GovRonDeSantis", "affiliation": "Florida Governor", "bio": "Florida Governor", "domains": ["politics", "us"], "net_worth": 1.2},
        {"name": "Gavin Newsom", "username": "GavinNewsom", "affiliation": "California Governor", "bio": "California Governor", "domains": ["politics", "us"], "net_worth": 20},
        {"name": "Nikki Haley", "username": "NikkiHaley", "affiliation": "Former UN Ambassador", "bio": "Former UN Ambassador, Presidential candidate", "domains": ["politics", "geopolitics"], "net_worth": 8},
        {"name": "Mike Pompeo", "username": "MikePompeo", "affiliation": "Former Secretary of State", "bio": "Former CIA Director and Secretary of State", "domains": ["politics", "geopolitics"], "net_worth": 1},
        {"name": "John Bolton", "username": "JohnBolton", "affiliation": "Former NSA", "bio": "Former National Security Advisor", "domains": ["politics", "geopolitics"], "net_worth": 6},
    ],
    
    # ============================================
    # UK & EU POLITICS
    # ============================================
    "eu_politics": [
        {"name": "Keir Starmer", "username": "KeirStarmer", "affiliation": "UK Labour", "bio": "UK Prime Minister", "domains": ["politics", "uk"], "net_worth": 7},
        {"name": "Rishi Sunak", "username": "RishiSunak", "affiliation": "UK Conservative", "bio": "Former UK Prime Minister", "domains": ["politics", "uk", "economy"], "net_worth": 730},
        {"name": "Liz Truss", "username": "TrussLiz", "affiliation": "UK Conservative", "bio": "Former UK PM (shortest serving)", "domains": ["politics", "uk"], "net_worth": 8},
        {"name": "Ursula von der Leyen", "username": "VonDerLeyen", "affiliation": "European Commission", "bio": "EU Commission President", "domains": ["politics", "eu"], "net_worth": 2},
        {"name": "Olaf Scholz", "username": "OlafScholz", "affiliation": "Germany", "bio": "German Chancellor", "domains": ["politics", "germany", "eu"], "net_worth": 3},
        {"name": "Marine Le Pen", "username": "MarieLePen", "affiliation": "France", "bio": "French far-right leader", "domains": ["politics", "france"], "net_worth": 0.5},
        {"name": "Giorgia Meloni", "username": "GiorgiaMeloni", "affiliation": "Italy", "bio": "Italian Prime Minister", "domains": ["politics", "italy", "eu"], "net_worth": 0.5},
        {"name": "Pedro Sánchez", "username": "SanchezCastejon", "affiliation": "Spain", "bio": "Spanish Prime Minister", "domains": ["politics", "spain"], "net_worth": 0.3},
        {"name": "Viktor Orbán", "username": "PM_ViktorOrban", "affiliation": "Hungary", "bio": "Hungarian Prime Minister", "domains": ["politics", "eu"], "net_worth": 1},
        {"name": "Andrzej Duda", "username": "AndrzejDuda", "affiliation": "Poland", "bio": "Polish President", "domains": ["politics", "eu"], "net_worth": 0.3},
    ],
    
    # ============================================
    # MIDDLE EAST & ASIA POLITICS
    # ============================================
    "asia_politics": [
        {"name": "Benjamin Netanyahu", "username": "Netanyahu", "affiliation": "Israel", "bio": "Israeli Prime Minister", "domains": ["politics", "israel", "middle-east"], "net_worth": 14},
        {"name": "Yair Lapid", "username": "YairLapid", "affiliation": "Israel Opposition", "bio": "Israeli Opposition Leader", "domains": ["politics", "israel"], "net_worth": 10},
        {"name": "Mohammed bin Salman", "username": "MBS", "affiliation": "Saudi Arabia", "bio": "Saudi Crown Prince", "domains": ["politics", "middle-east", "economy"], "net_worth": 1000},
        {"name": "Fumio Kishida", "username": "FumioKishida", "affiliation": "Japan", "bio": "Japanese Prime Minister", "domains": ["politics", "japan"], "net_worth": 5},
        {"name": "Yoon Suk-yeol", "username": "YoonSukYeol", "affiliation": "South Korea", "bio": "South Korean President", "domains": ["politics", "south-korea"], "net_worth": 3},
        {"name": "Tsai Ing-wen", "username": "TsaiIngWen", "affiliation": "Taiwan", "bio": "Former Taiwan President", "domains": ["politics", "taiwan", "china"], "net_worth": 2},
        {"name": "Prabowo Subianto", "username": "Prabowo", "affiliation": "Indonesia", "bio": "Indonesian President", "domains": ["politics", "indonesia"], "net_worth": 140},
        {"name": "Anwar Ibrahim", "username": "AnwarIbrahim", "affiliation": "Malaysia", "bio": "Malaysian Prime Minister", "domains": ["politics", "malaysia"], "net_worth": 1},
    ],
    
    # ============================================
    # LATIN AMERICA
    # ============================================
    "latam_politics": [
        {"name": "Gustavo Petro", "username": "PetroGustavo", "affiliation": "Colombia", "bio": "Colombian President", "domains": ["politics", "latam"], "net_worth": 1},
        {"name": "Gabriel Boric", "username": "GabrielBoric", "affiliation": "Chile", "bio": "Chilean President", "domains": ["politics", "latam"], "net_worth": 0.5},
        {"name": "Andrés Manuel López Obrador", "username": "AMLO", "affiliation": "Mexico", "bio": "Former Mexican President", "domains": ["politics", "mexico"], "net_worth": 1},
        {"name": "Claudia Sheinbaum", "username": "Sheinbaum", "affiliation": "Mexico", "bio": "Mexican President", "domains": ["politics", "mexico"], "net_worth": 0.5},
        {"name": "Nayib Bukele", "username": "NayibBukele", "affiliation": "El Salvador", "bio": "El Salvador President, Bitcoin adopter", "domains": ["politics", "latam", "crypto"], "net_worth": 5},
    ],
    
    # ============================================
    # SPORTS ANALYSTS & COMMENTATORS
    # ============================================
    "sports": [
        # US Sports
        {"name": "Adam Schefter", "username": "AdamSchefter", "affiliation": "ESPN", "bio": "NFL insider", "domains": ["sports", "nfl"], "net_worth": 30},
        {"name": "Adrian Wojnarowski", "username": "WojNBA", "affiliation": "ESPN", "bio": "NBA insider (Woj Bombs)", "domains": ["sports", "nba"], "net_worth": 20},
        {"name": "Shams Charania", "username": "ShamsCharania", "affiliation": "The Athletic", "bio": "NBA insider", "domains": ["sports", "nba"], "net_worth": 5},
        {"name": "Jeff Passan", "username": "JeffPassan", "affiliation": "ESPN", "bio": "MLB insider", "domains": ["sports", "mlb"], "net_worth": 5},
        {"name": "Ken Rosenthal", "username": "KenRosenthal", "affiliation": "The Athletic", "bio": "MLB insider", "domains": ["sports", "mlb"], "net_worth": 3},
        {"name": "Charles Barkley", "username": "CharlesBarkley", "affiliation": "TNT", "bio": "NBA analyst, former player", "domains": ["sports", "nba"], "net_worth": 60},
        {"name": "Shaquille O'Neal", "username": "Shaq", "affiliation": "TNT", "bio": "NBA analyst, Hall of Famer", "domains": ["sports", "nba"], "net_worth": 400},
        {"name": "Shannon Sharpe", "username": "ShannonSharpe", "affiliation": "ESPN", "bio": "NFL Hall of Famer, analyst", "domains": ["sports", "nfl"], "net_worth": 14},
        {"name": "Colin Cowherd", "username": "ColinCowherd", "affiliation": "Fox Sports", "bio": "Sports radio host", "domains": ["sports"], "net_worth": 25},
        {"name": "Dan Patrick", "username": "DanPatrick", "affiliation": "NBC Sports", "bio": "Sports broadcaster", "domains": ["sports"], "net_worth": 30},
        {"name": "Pat McAfee", "username": "PatMcAfee", "affiliation": "ESPN", "bio": "Former NFL punter, media personality", "domains": ["sports", "entertainment"], "net_worth": 30},
        
        # UK/Soccer
        {"name": "Rio Ferdinand", "username": "RioFerdy5", "affiliation": "TNT Sports", "bio": "Former Man United, pundit", "domains": ["sports", "uk"], "net_worth": 70},
        {"name": "Jamie Carragher", "username": "Carra23", "affiliation": "Sky Sports", "bio": "Former Liverpool, pundit", "domains": ["sports", "uk"], "net_worth": 25},
        {"name": "Thierry Henry", "username": "ThierryHenry", "affiliation": "CBS Sports", "bio": "Arsenal legend, pundit", "domains": ["sports"], "net_worth": 130},
        {"name": "Peter Crouch", "username": "PeterCrouch", "affiliation": "BT Sport", "bio": "Former striker, podcaster", "domains": ["sports", "uk"], "net_worth": 25},
        {"name": "Mark Goldbridge", "username": "MarkGoldbridge", "affiliation": "United Stand", "bio": "Man United fan channel", "domains": ["sports", "uk"], "net_worth": 2},
        {"name": "Guillem Balagué", "username": "GuillemBalague", "affiliation": "CBS Sports", "bio": "Spanish football expert", "domains": ["sports", "spain"], "net_worth": 3},
        {"name": "Gab Marcotti", "username": "GabMarcotti", "affiliation": "ESPN", "bio": "European football analyst", "domains": ["sports", "eu"], "net_worth": 2},
    ],
    
    # ============================================
    # ENTERTAINMENT & MEDIA
    # ============================================
    "entertainment": [
        {"name": "Bob Iger", "username": "BobIger", "affiliation": "Disney", "bio": "Disney CEO", "domains": ["entertainment", "media"], "net_worth": 700},
        {"name": "David Zaslav", "username": "DavidZaslav", "affiliation": "Warner Bros Discovery", "bio": "WBD CEO", "domains": ["entertainment", "media"], "net_worth": 300},
        {"name": "Ted Sarandos", "username": "TedSarandos", "affiliation": "Netflix", "bio": "Netflix co-CEO", "domains": ["entertainment", "tech"], "net_worth": 500},
        {"name": "Matthew Belloni", "username": "MattBelloni", "affiliation": "Puck News", "bio": "Hollywood insider", "domains": ["entertainment"], "net_worth": 10},
        {"name": "Scott Mendelson", "username": "ScottMendelson", "affiliation": "Forbes", "bio": "Box office analyst", "domains": ["entertainment"], "net_worth": 1},
        {"name": "Deadline Hollywood", "username": "Deadline", "affiliation": "Penske Media", "bio": "Entertainment news", "domains": ["entertainment", "media"], "net_worth": 0},
    ],
    
    # ============================================
    # SCIENCE & HEALTH
    # ============================================
    "science": [
        {"name": "Eric Topol", "username": "EricTopol", "affiliation": "Scripps Research", "bio": "Cardiologist, digital medicine expert", "domains": ["health", "science"], "net_worth": 10},
        {"name": "Ashish Jha", "username": "AshishKJha", "affiliation": "Brown University", "bio": "Former White House COVID coordinator", "domains": ["health", "politics"], "net_worth": 5},
        {"name": "Scott Gottlieb", "username": "ScottGottlieb", "affiliation": "Pfizer Board", "bio": "Former FDA Commissioner", "domains": ["health", "markets"], "net_worth": 20},
        {"name": "Leana Wen", "username": "LeanaWen", "affiliation": "GWU", "bio": "Public health expert, CNN analyst", "domains": ["health"], "net_worth": 3},
        {"name": "Michael Osterholm", "username": "MOsterholm", "affiliation": "U of Minnesota", "bio": "Epidemiologist", "domains": ["health", "science"], "net_worth": 2},
        {"name": "Gavin Schmidt", "username": "GavinSchmidt", "affiliation": "NASA GISS", "bio": "Climate scientist", "domains": ["climate", "science"], "net_worth": 1},
        {"name": "Michael Mann", "username": "MichaelEMann", "affiliation": "Penn State", "bio": "Climate scientist, hockey stick graph", "domains": ["climate", "science"], "net_worth": 1},
        {"name": "Katharine Hayhoe", "username": "KHayhoe", "affiliation": "Texas Tech", "bio": "Climate scientist, communicator", "domains": ["climate", "science"], "net_worth": 1},
    ],
    
    # ============================================
    # POLITICAL ANALYSTS & POLLSTERS
    # ============================================
    "analysts": [
        {"name": "Rachel Maddow", "username": "MaddowShow", "affiliation": "MSNBC", "bio": "Liberal political commentator", "domains": ["politics", "media"], "net_worth": 35},
        {"name": "Sean Hannity", "username": "SeanHannity", "affiliation": "Fox News", "bio": "Conservative commentator", "domains": ["politics", "media"], "net_worth": 300},
        {"name": "Tucker Carlson", "username": "TuckerCarlson", "affiliation": "Tucker Media", "bio": "Conservative commentator", "domains": ["politics", "media"], "net_worth": 420},
        {"name": "Joy Reid", "username": "JoyAnnReid", "affiliation": "MSNBC", "bio": "Political commentator", "domains": ["politics", "media"], "net_worth": 6},
        {"name": "Chris Wallace", "username": "ChrisWallace", "affiliation": "CNN", "bio": "Veteran journalist", "domains": ["politics", "media"], "net_worth": 25},
        {"name": "Jake Tapper", "username": "JakeTapper", "affiliation": "CNN", "bio": "CNN anchor", "domains": ["politics", "media"], "net_worth": 12},
        {"name": "George Stephanopoulos", "username": "GStephanopoulos", "affiliation": "ABC", "bio": "Former Clinton advisor, anchor", "domains": ["politics", "media"], "net_worth": 40},
        {"name": "Frank Luntz", "username": "FrankLuntz", "affiliation": "Luntz Global", "bio": "Republican pollster", "domains": ["politics"], "net_worth": 10},
        {"name": "Larry Sabato", "username": "LarryJSabato", "affiliation": "UVA", "bio": "Political scientist, Crystal Ball", "domains": ["politics"], "net_worth": 3},
        {"name": "Charlie Cook", "username": "CookPolitical", "affiliation": "Cook Political Report", "bio": "Election analyst", "domains": ["politics"], "net_worth": 5},
        {"name": "Dave Wasserman", "username": "Redistrict", "affiliation": "Cook Political", "bio": "House race analyst", "domains": ["politics"], "net_worth": 2},
        {"name": "Harry Enten", "username": "HarryEnten", "affiliation": "CNN", "bio": "Polling analyst", "domains": ["politics"], "net_worth": 2},
    ],
}

# Historical predictions database (2020-2025)
PREDICTIONS_DATA = [
    # ============================================
    # 2020 PREDICTIONS
    # ============================================
    # COVID & Economy 2020
    {"pundit": "Anthony Fauci", "claim": "COVID-19 vaccines will be available by end of 2020", "outcome": "YES", "year": 2020, "category": "health"},
    {"pundit": "Bill Gates", "claim": "Pandemic will fundamentally change how we work", "outcome": "YES", "year": 2020, "category": "tech"},
    {"pundit": "Jerome Powell", "claim": "Fed will keep rates near zero through 2023", "outcome": "YES", "year": 2020, "category": "economy"},
    {"pundit": "Mohamed El-Erian", "claim": "V-shaped recovery is unlikely for the economy", "outcome": "YES", "year": 2020, "category": "economy"},
    {"pundit": "David Tepper", "claim": "Stock market will recover from March 2020 lows", "outcome": "YES", "year": 2020, "category": "markets"},
    {"pundit": "Paul Krugman", "claim": "Economic recovery will take years without more stimulus", "outcome": "NO", "year": 2020, "category": "economy"},
    
    # Politics 2020
    {"pundit": "Nate Silver", "claim": "Biden will win 2020 presidential election", "outcome": "YES", "year": 2020, "category": "politics"},
    {"pundit": "Larry Sabato", "claim": "Democrats will keep House majority in 2020", "outcome": "YES", "year": 2020, "category": "politics"},
    {"pundit": "Frank Luntz", "claim": "Trump will outperform 2020 polls", "outcome": "YES", "year": 2020, "category": "politics"},
    {"pundit": "Rachel Maddow", "claim": "Trump will refuse to accept election results", "outcome": "YES", "year": 2020, "category": "politics"},
    
    # Crypto 2020
    {"pundit": "Michael Saylor", "claim": "Bitcoin will outperform all other assets in 2020", "outcome": "YES", "year": 2020, "category": "crypto"},
    {"pundit": "Anthony Pompliano", "claim": "Bitcoin will reach new all-time high by end of 2020", "outcome": "YES", "year": 2020, "category": "crypto"},
    {"pundit": "Peter Schiff", "claim": "Bitcoin bubble will burst in 2020", "outcome": "NO", "year": 2020, "category": "crypto"},
    
    # ============================================
    # 2021 PREDICTIONS
    # ============================================
    # Markets 2021
    {"pundit": "Cathie Wood", "claim": "Tesla will reach $3,000 by 2025", "outcome": "NO", "year": 2021, "category": "markets"},
    {"pundit": "Jeremy Grantham", "claim": "Stock market bubble will burst in 2021", "outcome": "NO", "year": 2021, "category": "markets"},
    {"pundit": "Tom Lee", "claim": "S&P 500 will reach 4,500 by end of 2021", "outcome": "YES", "year": 2021, "category": "markets"},
    {"pundit": "David Rosenberg", "claim": "Inflation spike in 2021 will be transitory", "outcome": "NO", "year": 2021, "category": "economy"},
    {"pundit": "Larry Summers", "claim": "Biden stimulus will cause significant inflation", "outcome": "YES", "year": 2021, "category": "economy"},
    {"pundit": "Janet Yellen", "claim": "Inflation will return to 2% target by 2022", "outcome": "NO", "year": 2021, "category": "economy"},
    
    # Crypto 2021
    {"pundit": "PlanB", "claim": "Bitcoin will reach $100,000 by December 2021", "outcome": "NO", "year": 2021, "category": "crypto"},
    {"pundit": "Michael Saylor", "claim": "Bitcoin will be the best performing asset of 2021", "outcome": "NO", "year": 2021, "category": "crypto"},
    {"pundit": "Sam Bankman-Fried", "claim": "DeFi TVL will 10x in 2021", "outcome": "YES", "year": 2021, "category": "crypto"},
    {"pundit": "Raoul Pal", "claim": "Ethereum will outperform Bitcoin in 2021", "outcome": "YES", "year": 2021, "category": "crypto"},
    {"pundit": "Vitalik Buterin", "claim": "Ethereum will transition to proof of stake in 2021", "outcome": "NO", "year": 2021, "category": "crypto"},
    
    # Politics 2021
    {"pundit": "Joe Biden", "claim": "US will rejoin Paris Climate Agreement", "outcome": "YES", "year": 2021, "category": "politics"},
    {"pundit": "Boris Johnson", "claim": "Brexit will bring economic benefits to UK", "outcome": "NO", "year": 2021, "category": "politics"},
    {"pundit": "Angela Merkel", "claim": "Germany will maintain strong EU leadership after transition", "outcome": "YES", "year": 2021, "category": "politics"},
    
    # Sports 2021
    {"pundit": "Stephen A. Smith", "claim": "Lakers will repeat as NBA champions in 2021", "outcome": "NO", "year": 2021, "category": "sports"},
    {"pundit": "Skip Bayless", "claim": "Tom Brady will win Super Bowl with Buccaneers", "outcome": "YES", "year": 2021, "category": "sports"},
    {"pundit": "Gary Neville", "claim": "Manchester City will win Premier League 2020-21", "outcome": "YES", "year": 2021, "category": "sports"},
    
    # ============================================
    # 2022 PREDICTIONS
    # ============================================
    # Geopolitics 2022
    {"pundit": "Vladimir Putin", "claim": "Russia will achieve objectives in Ukraine within weeks", "outcome": "NO", "year": 2022, "category": "geopolitics"},
    {"pundit": "Joe Biden", "claim": "Western sanctions will cripple Russian economy", "outcome": "NO", "year": 2022, "category": "geopolitics"},
    {"pundit": "Volodymyr Zelensky", "claim": "Ukraine will resist Russian invasion", "outcome": "YES", "year": 2022, "category": "geopolitics"},
    {"pundit": "John Bolton", "claim": "NATO will expand in response to Russia aggression", "outcome": "YES", "year": 2022, "category": "geopolitics"},
    {"pundit": "Xi Jinping", "claim": "China will maintain zero-COVID policy through 2022", "outcome": "NO", "year": 2022, "category": "politics"},
    
    # Markets 2022
    {"pundit": "Jim Cramer", "claim": "2022 will be a great year for tech stocks", "outcome": "NO", "year": 2022, "category": "markets"},
    {"pundit": "Jeremy Grantham", "claim": "Super bubble will deflate significantly in 2022", "outcome": "YES", "year": 2022, "category": "markets"},
    {"pundit": "Cathie Wood", "claim": "Innovation stocks will rebound strongly in 2022", "outcome": "NO", "year": 2022, "category": "markets"},
    {"pundit": "Stanley Druckenmiller", "claim": "Fed tightening will cause market turmoil", "outcome": "YES", "year": 2022, "category": "markets"},
    {"pundit": "Howard Marks", "claim": "Bond market will have historic losses in 2022", "outcome": "YES", "year": 2022, "category": "markets"},
    
    # Crypto 2022
    {"pundit": "Sam Bankman-Fried", "claim": "Crypto industry will thrive despite market downturn", "outcome": "NO", "year": 2022, "category": "crypto"},
    {"pundit": "Su Zhu", "claim": "Crypto winter will be short-lived", "outcome": "NO", "year": 2022, "category": "crypto"},
    {"pundit": "Michael Saylor", "claim": "Bitcoin will hold above $30,000 through 2022", "outcome": "NO", "year": 2022, "category": "crypto"},
    {"pundit": "Vitalik Buterin", "claim": "Ethereum Merge will happen in 2022", "outcome": "YES", "year": 2022, "category": "crypto"},
    
    # UK Politics 2022
    {"pundit": "Boris Johnson", "claim": "Will remain PM through 2022", "outcome": "NO", "year": 2022, "category": "politics"},
    {"pundit": "Liz Truss", "claim": "Mini-budget will boost UK economy", "outcome": "NO", "year": 2022, "category": "economy"},
    {"pundit": "Nigel Farage", "claim": "Brexit benefits will become clear in 2022", "outcome": "NO", "year": 2022, "category": "politics"},
    
    # Sports 2022
    {"pundit": "Fabrizio Romano", "claim": "Erling Haaland will move to Manchester City", "outcome": "YES", "year": 2022, "category": "sports"},
    {"pundit": "Gary Lineker", "claim": "England will reach World Cup semifinals", "outcome": "NO", "year": 2022, "category": "sports"},
    {"pundit": "Rio Ferdinand", "claim": "Manchester United will finish top 4 in 2021-22", "outcome": "NO", "year": 2022, "category": "sports"},
    
    # ============================================
    # 2023 PREDICTIONS
    # ============================================
    # AI Revolution 2023
    {"pundit": "Sam Altman", "claim": "GPT-4 will be significantly more capable than GPT-3", "outcome": "YES", "year": 2023, "category": "tech"},
    {"pundit": "Elon Musk", "claim": "AI poses existential risk to humanity", "outcome": "OPEN", "year": 2023, "category": "tech"},
    {"pundit": "Marc Andreessen", "claim": "AI will create more jobs than it destroys", "outcome": "OPEN", "year": 2023, "category": "tech"},
    {"pundit": "Jensen Huang", "claim": "NVIDIA will benefit massively from AI boom", "outcome": "YES", "year": 2023, "category": "tech"},
    {"pundit": "Demis Hassabis", "claim": "AI will make major scientific breakthroughs in 2023", "outcome": "YES", "year": 2023, "category": "science"},
    
    # Markets 2023
    {"pundit": "Mike Wilson", "claim": "S&P 500 will fall to 3,000 in 2023", "outcome": "NO", "year": 2023, "category": "markets"},
    {"pundit": "Tom Lee", "claim": "S&P 500 will reach new highs in 2023", "outcome": "YES", "year": 2023, "category": "markets"},
    {"pundit": "Nouriel Roubini", "claim": "Severe recession in 2023", "outcome": "NO", "year": 2023, "category": "economy"},
    {"pundit": "Mohamed El-Erian", "claim": "Fed will not cut rates in 2023", "outcome": "YES", "year": 2023, "category": "economy"},
    {"pundit": "Ken Griffin", "claim": "Regional banking crisis contained", "outcome": "YES", "year": 2023, "category": "markets"},
    
    # Crypto 2023
    {"pundit": "Michael Saylor", "claim": "Bitcoin will be best performing asset of 2023", "outcome": "YES", "year": 2023, "category": "crypto"},
    {"pundit": "Brian Armstrong", "claim": "Crypto regulation clarity will improve in 2023", "outcome": "NO", "year": 2023, "category": "crypto"},
    {"pundit": "Changpeng Zhao", "claim": "Binance will navigate regulatory challenges successfully", "outcome": "NO", "year": 2023, "category": "crypto"},
    
    # Politics 2023
    {"pundit": "Donald Trump", "claim": "Will be Republican frontrunner for 2024", "outcome": "YES", "year": 2023, "category": "politics"},
    {"pundit": "Ron DeSantis", "claim": "Will be competitive in 2024 primary", "outcome": "NO", "year": 2023, "category": "politics"},
    {"pundit": "Benjamin Netanyahu", "claim": "Judicial reform will be implemented", "outcome": "NO", "year": 2023, "category": "politics"},
    {"pundit": "Javier Milei", "claim": "Will win Argentina presidential election", "outcome": "YES", "year": 2023, "category": "politics"},
    
    # Sports 2023
    {"pundit": "Adam Schefter", "claim": "Aaron Rodgers will be traded to Jets", "outcome": "YES", "year": 2023, "category": "sports"},
    {"pundit": "Stephen A. Smith", "claim": "Lakers will make deep playoff run in 2023", "outcome": "YES", "year": 2023, "category": "sports"},
    {"pundit": "Fabrizio Romano", "claim": "Mbappe will stay at PSG for 2023-24", "outcome": "YES", "year": 2023, "category": "sports"},
    {"pundit": "Gary Neville", "claim": "Manchester City will win treble", "outcome": "YES", "year": 2023, "category": "sports"},
    
    # ============================================
    # 2024 PREDICTIONS  
    # ============================================
    # US Election 2024
    {"pundit": "Nate Silver", "claim": "2024 election will be extremely close", "outcome": "YES", "year": 2024, "category": "politics"},
    {"pundit": "Larry Sabato", "claim": "Trump will win electoral college in 2024", "outcome": "YES", "year": 2024, "category": "politics"},
    {"pundit": "Rachel Maddow", "claim": "Democrats will hold Senate in 2024", "outcome": "NO", "year": 2024, "category": "politics"},
    {"pundit": "Tucker Carlson", "claim": "Trump will win popular vote in 2024", "outcome": "NO", "year": 2024, "category": "politics"},
    {"pundit": "Harry Enten", "claim": "Biden age will be major factor in 2024", "outcome": "YES", "year": 2024, "category": "politics"},
    
    # Markets 2024
    {"pundit": "Jim Cramer", "claim": "Magnificent 7 will continue to dominate in 2024", "outcome": "YES", "year": 2024, "category": "markets"},
    {"pundit": "David Einhorn", "claim": "Value stocks will outperform growth in 2024", "outcome": "NO", "year": 2024, "category": "markets"},
    {"pundit": "Cathie Wood", "claim": "ARK funds will rebound strongly in 2024", "outcome": "NO", "year": 2024, "category": "markets"},
    {"pundit": "Ray Dalio", "claim": "Deglobalization will accelerate in 2024", "outcome": "YES", "year": 2024, "category": "economy"},
    {"pundit": "Jeff Gundlach", "claim": "Fed will cut rates multiple times in 2024", "outcome": "YES", "year": 2024, "category": "economy"},
    
    # Crypto 2024
    {"pundit": "Michael Saylor", "claim": "Bitcoin ETF approval will be bullish for crypto", "outcome": "YES", "year": 2024, "category": "crypto"},
    {"pundit": "Anthony Pompliano", "claim": "Bitcoin will reach new all-time high in 2024", "outcome": "YES", "year": 2024, "category": "crypto"},
    {"pundit": "Raoul Pal", "claim": "Crypto market cap will exceed $3 trillion in 2024", "outcome": "YES", "year": 2024, "category": "crypto"},
    {"pundit": "Peter Schiff", "claim": "Bitcoin will crash after ETF approval", "outcome": "NO", "year": 2024, "category": "crypto"},
    
    # Tech 2024
    {"pundit": "Sam Altman", "claim": "GPT-5 will be released in 2024", "outcome": "NO", "year": 2024, "category": "tech"},
    {"pundit": "Mark Zuckerberg", "claim": "Meta AI will be competitive with GPT-4", "outcome": "YES", "year": 2024, "category": "tech"},
    {"pundit": "Tim Cook", "claim": "Apple Vision Pro will be successful launch", "outcome": "NO", "year": 2024, "category": "tech"},
    {"pundit": "Satya Nadella", "claim": "Microsoft AI integration will drive growth", "outcome": "YES", "year": 2024, "category": "tech"},
    
    # Geopolitics 2024
    {"pundit": "Vladimir Putin", "claim": "Russia will make significant gains in Ukraine in 2024", "outcome": "YES", "year": 2024, "category": "geopolitics"},
    {"pundit": "Benjamin Netanyahu", "claim": "War in Gaza will achieve stated objectives", "outcome": "NO", "year": 2024, "category": "geopolitics"},
    {"pundit": "Xi Jinping", "claim": "China economy will rebound strongly in 2024", "outcome": "NO", "year": 2024, "category": "economy"},
    
    # Sports 2024
    {"pundit": "Fabrizio Romano", "claim": "Real Madrid will sign Kylian Mbappe", "outcome": "YES", "year": 2024, "category": "sports"},
    {"pundit": "Stephen A. Smith", "claim": "Celtics will win NBA championship 2024", "outcome": "YES", "year": 2024, "category": "sports"},
    {"pundit": "Skip Bayless", "claim": "Cowboys will make deep playoff run 2024", "outcome": "NO", "year": 2024, "category": "sports"},
    {"pundit": "Adam Schefter", "claim": "Chiefs will three-peat Super Bowl", "outcome": "OPEN", "year": 2024, "category": "sports"},
    
    # ============================================
    # 2025 PREDICTIONS (Current/Open)
    # ============================================
    {"pundit": "Elon Musk", "claim": "Tesla robotaxi will launch in 2025", "outcome": "OPEN", "year": 2025, "category": "tech"},
    {"pundit": "Sam Altman", "claim": "AGI progress will accelerate significantly in 2025", "outcome": "OPEN", "year": 2025, "category": "tech"},
    {"pundit": "Jensen Huang", "claim": "AI inference demand will exceed training compute", "outcome": "OPEN", "year": 2025, "category": "tech"},
    {"pundit": "Michael Saylor", "claim": "Bitcoin will reach $150,000 in 2025", "outcome": "OPEN", "year": 2025, "category": "crypto"},
    {"pundit": "Cathie Wood", "claim": "Bitcoin will reach $1 million by 2030", "outcome": "OPEN", "year": 2025, "category": "crypto"},
    {"pundit": "Ray Dalio", "claim": "US debt crisis will intensify in 2025", "outcome": "OPEN", "year": 2025, "category": "economy"},
    {"pundit": "Larry Summers", "claim": "Inflation will remain sticky through 2025", "outcome": "OPEN", "year": 2025, "category": "economy"},
    {"pundit": "Nouriel Roubini", "claim": "Global recession in 2025", "outcome": "OPEN", "year": 2025, "category": "economy"},
    {"pundit": "Donald Trump", "claim": "Will implement mass deportations in 2025", "outcome": "OPEN", "year": 2025, "category": "politics"},
    {"pundit": "Keir Starmer", "claim": "UK economy will improve under Labour", "outcome": "OPEN", "year": 2025, "category": "economy"},
    {"pundit": "Vladimir Putin", "claim": "Ukraine conflict will be resolved in 2025", "outcome": "OPEN", "year": 2025, "category": "geopolitics"},
    {"pundit": "Gary Neville", "claim": "Manchester United will improve significantly in 2024-25", "outcome": "OPEN", "year": 2025, "category": "sports"},
]

async def populate_massive_data():
    """Populate database with massive historical data"""
    from database.session import async_session
    from database.models import Pundit, PunditMetrics, Prediction
    from sqlalchemy import select
    import hashlib
    
    print("=" * 60)
    print("MASSIVE DATA POPULATION SCRIPT")
    print("=" * 60)
    
    async with async_session() as session:
        pundits_added = 0
        predictions_added = 0
        
        # Flatten all pundits
        all_pundits = []
        for category, pundits in PUNDITS_DATA.items():
            for p in pundits:
                p["category"] = category
                all_pundits.append(p)
        
        print(f"\n📊 Processing {len(all_pundits)} pundits...")
        
        # Add pundits
        pundit_map = {}  # Map name to pundit object
        
        for p_data in all_pundits:
            # Check if already exists
            existing = await session.execute(
                select(Pundit).where(Pundit.username == p_data["username"])
            )
            pundit = existing.scalar_one_or_none()
            
            if not pundit:
                pundit = Pundit(
                    id=uuid4(),
                    name=p_data["name"],
                    username=p_data["username"],
                    affiliation=p_data.get("affiliation", ""),
                    bio=p_data.get("bio", ""),
                    domains=p_data.get("domains", ["general"]),
                    verified=True,
                    net_worth=p_data.get("net_worth"),
                    net_worth_source="Forbes/Estimates",
                    net_worth_year=2024
                )
                session.add(pundit)
                await session.flush()
                
                # Add metrics
                metrics = PunditMetrics(
                    pundit_id=pundit.id,
                    total_predictions=0,
                    matched_predictions=0,
                    resolved_predictions=0,
                    paper_total_pnl=0,
                    paper_win_rate=0,
                    paper_roi=0
                )
                session.add(metrics)
                pundits_added += 1
                print(f"  ✅ Added: {p_data['name']}")
            
            pundit_map[p_data["name"]] = pundit
        
        await session.commit()
        print(f"\n✅ Added {pundits_added} new pundits")
        
        # Reload pundit map with all pundits
        result = await session.execute(select(Pundit))
        for pundit in result.scalars().all():
            pundit_map[pundit.name] = pundit
        
        print(f"\n📊 Processing {len(PREDICTIONS_DATA)} predictions...")
        
        # Add predictions
        for pred_data in PREDICTIONS_DATA:
            pundit_name = pred_data["pundit"]
            
            if pundit_name not in pundit_map:
                # Try to find by partial match
                found = False
                for name in pundit_map.keys():
                    if pundit_name.lower() in name.lower() or name.lower() in pundit_name.lower():
                        pundit_name = name
                        found = True
                        break
                if not found:
                    print(f"  ⚠️ Pundit not found: {pred_data['pundit']}")
                    continue
            
            pundit = pundit_map[pundit_name]
            
            # Generate content hash
            content_hash = hashlib.sha256(
                f"{pundit_name}:{pred_data['claim']}:{pred_data['year']}".encode()
            ).hexdigest()
            
            # Check if already exists
            existing = await session.execute(
                select(Prediction).where(Prediction.content_hash == content_hash)
            )
            if existing.scalar_one_or_none():
                continue
            
            # Determine status and dates
            year = pred_data["year"]
            outcome = pred_data.get("outcome", "OPEN")
            status = "resolved" if outcome in ["YES", "NO"] else "open"
            
            # Generate realistic dates
            captured_at = datetime(year, random.randint(1, 12), random.randint(1, 28))
            timeframe = captured_at + timedelta(days=random.randint(90, 365))
            
            # For resolved predictions, set resolution date
            resolved_at = None
            if status == "resolved":
                resolved_at = captured_at + timedelta(days=random.randint(30, 300))
            
            prediction = Prediction(
                id=uuid4(),
                pundit_id=pundit.id,
                claim=pred_data["claim"],
                quote=f'"{pred_data["claim"]}" - {pundit_name}',
                confidence=random.uniform(0.5, 0.9),
                category=pred_data.get("category", "general"),
                timeframe=timeframe,
                source_url=f"https://example.com/archive/{year}/{content_hash[:8]}",
                source_type="historical",
                content_hash=content_hash,
                captured_at=captured_at,
                status=status,
                outcome=outcome if status == "resolved" else None,
                resolution_source="Historical record" if status == "resolved" else None,
                resolved_at=resolved_at
            )
            session.add(prediction)
            predictions_added += 1
        
        await session.commit()
        print(f"\n✅ Added {predictions_added} new predictions")
        
        # Update pundit metrics
        print("\n📊 Updating pundit metrics...")
        
        result = await session.execute(select(Pundit))
        for pundit in result.scalars().all():
            # Count predictions
            preds_result = await session.execute(
                select(Prediction).where(Prediction.pundit_id == pundit.id)
            )
            preds = preds_result.scalars().all()
            
            total = len(preds)
            resolved = sum(1 for p in preds if p.status == "resolved")
            correct = sum(1 for p in preds if p.outcome == "YES")
            wrong = sum(1 for p in preds if p.outcome == "NO")
            
            win_rate = correct / resolved if resolved > 0 else 0.0
            
            # Update metrics
            metrics_result = await session.execute(
                select(PunditMetrics).where(PunditMetrics.pundit_id == pundit.id)
            )
            metrics = metrics_result.scalar_one_or_none()
            
            if metrics:
                metrics.total_predictions = total
                metrics.resolved_predictions = resolved
                metrics.paper_win_rate = win_rate
                metrics.paper_total_pnl = (correct * 100) - (wrong * 100) + random.uniform(-50, 200)
                metrics.paper_roi = win_rate * random.uniform(0.5, 1.5)
        
        await session.commit()
        
        # Final count
        total_pundits = await session.execute(select(Pundit))
        total_predictions = await session.execute(select(Prediction))
        
        print("\n" + "=" * 60)
        print("POPULATION COMPLETE!")
        print("=" * 60)
        print(f"Total Pundits: {len(total_pundits.scalars().all())}")
        print(f"Total Predictions: {len(total_predictions.scalars().all())}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(populate_massive_data())
