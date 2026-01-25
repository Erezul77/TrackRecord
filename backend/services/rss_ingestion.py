# services/rss_ingestion.py
"""
RSS Feed Ingestion Service
Pulls articles from news sources and extracts predictions using AI
"""
import feedparser
import httpx
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NewsArticle:
    title: str
    url: str
    summary: str
    published: datetime
    source: str
    author: Optional[str] = None

# News RSS feeds that often contain predictions
RSS_FEEDS = {
    # ===== FINANCIAL NEWS =====
    "cnbc_markets": {
        "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "source": "CNBC Markets",
        "categories": ["markets", "economy"]
    },
    "cnbc_economy": {
        "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "source": "CNBC Economy",
        "categories": ["economy"]
    },
    "bloomberg_markets": {
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "source": "Bloomberg Markets",
        "categories": ["markets"]
    },
    "reuters_business": {
        "url": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "source": "Reuters Business",
        "categories": ["markets", "economy"]
    },
    
    # ===== CRYPTO NEWS =====
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "source": "CoinDesk",
        "categories": ["crypto"]
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/rss",
        "source": "Cointelegraph",
        "categories": ["crypto"]
    },
    
    # ===== POLITICS NEWS =====
    "politico": {
        "url": "https://www.politico.com/rss/politicopicks.xml",
        "source": "Politico",
        "categories": ["politics"]
    },
    "hill": {
        "url": "https://thehill.com/feed/",
        "source": "The Hill",
        "categories": ["politics"]
    },
    "axios": {
        "url": "https://api.axios.com/feed/",
        "source": "Axios",
        "categories": ["politics", "tech"]
    },
    "npr_politics": {
        "url": "https://feeds.npr.org/1014/rss.xml",
        "source": "NPR Politics",
        "categories": ["politics"]
    },
    "bbc_world": {
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "source": "BBC World",
        "categories": ["politics", "geopolitics"]
    },
    
    # ===== TECH NEWS =====
    "techcrunch": {
        "url": "https://techcrunch.com/feed/",
        "source": "TechCrunch",
        "categories": ["tech"]
    },
    "verge": {
        "url": "https://www.theverge.com/rss/index.xml",
        "source": "The Verge",
        "categories": ["tech", "entertainment"]
    },
    "wired": {
        "url": "https://www.wired.com/feed/rss",
        "source": "Wired",
        "categories": ["tech", "science"]
    },
    
    # ===== SPORTS NEWS =====
    "espn": {
        "url": "https://www.espn.com/espn/rss/news",
        "source": "ESPN",
        "categories": ["sports"]
    },
    "espn_nfl": {
        "url": "https://www.espn.com/espn/rss/nfl/news",
        "source": "ESPN NFL",
        "categories": ["sports"]
    },
    "espn_nba": {
        "url": "https://www.espn.com/espn/rss/nba/news",
        "source": "ESPN NBA",
        "categories": ["sports"]
    },
    "bleacher_report": {
        "url": "https://bleacherreport.com/articles/feed",
        "source": "Bleacher Report",
        "categories": ["sports"]
    },
    "athletic": {
        "url": "https://theathletic.com/feeds/rss/news/",
        "source": "The Athletic",
        "categories": ["sports"]
    },
    
    # ===== ENTERTAINMENT NEWS =====
    "variety": {
        "url": "https://variety.com/feed/",
        "source": "Variety",
        "categories": ["entertainment", "media"]
    },
    "hollywood_reporter": {
        "url": "https://www.hollywoodreporter.com/feed/",
        "source": "Hollywood Reporter",
        "categories": ["entertainment", "media"]
    },
    "deadline": {
        "url": "https://deadline.com/feed/",
        "source": "Deadline",
        "categories": ["entertainment", "media"]
    },
    "billboard": {
        "url": "https://www.billboard.com/feed/",
        "source": "Billboard",
        "categories": ["entertainment"]
    },
    
    # ===== SCIENCE & HEALTH NEWS =====
    "science_daily": {
        "url": "https://www.sciencedaily.com/rss/all.xml",
        "source": "Science Daily",
        "categories": ["science"]
    },
    "nature": {
        "url": "http://feeds.nature.com/nature/rss/current",
        "source": "Nature",
        "categories": ["science"]
    },
    "stat_news": {
        "url": "https://www.statnews.com/feed/",
        "source": "STAT News",
        "categories": ["health", "science"]
    },
    "medical_news": {
        "url": "https://www.medicalnewstoday.com/rss",
        "source": "Medical News Today",
        "categories": ["health"]
    },
    
    # ===== CLIMATE & ENVIRONMENT =====
    "climate_home": {
        "url": "https://www.climatechangenews.com/feed/",
        "source": "Climate Home News",
        "categories": ["climate", "science"]
    },
    "carbon_brief": {
        "url": "https://www.carbonbrief.org/feed/",
        "source": "Carbon Brief",
        "categories": ["climate", "science"]
    },
    
    # ===== GEOPOLITICS =====
    "foreign_policy": {
        "url": "https://foreignpolicy.com/feed/",
        "source": "Foreign Policy",
        "categories": ["geopolitics", "politics"]
    },
    "al_jazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "source": "Al Jazeera",
        "categories": ["geopolitics", "politics", "middle-east"]
    },
    
    # ===== UK & EUROPE =====
    "bbc_uk": {
        "url": "http://feeds.bbci.co.uk/news/uk/rss.xml",
        "source": "BBC UK",
        "categories": ["uk", "uk-politics"]
    },
    "guardian_uk": {
        "url": "https://www.theguardian.com/uk-news/rss",
        "source": "The Guardian UK",
        "categories": ["uk", "uk-politics"]
    },
    "telegraph": {
        "url": "https://www.telegraph.co.uk/rss.xml",
        "source": "The Telegraph",
        "categories": ["uk", "uk-politics"]
    },
    "sky_news": {
        "url": "https://feeds.skynews.com/feeds/rss/home.xml",
        "source": "Sky News",
        "categories": ["uk"]
    },
    "euronews": {
        "url": "https://www.euronews.com/rss",
        "source": "Euronews",
        "categories": ["eu", "europe"]
    },
    "politico_eu": {
        "url": "https://www.politico.eu/feed/",
        "source": "Politico EU",
        "categories": ["eu", "europe", "politics"]
    },
    "dw_europe": {
        "url": "https://rss.dw.com/xml/rss-en-eu",
        "source": "Deutsche Welle Europe",
        "categories": ["eu", "germany", "europe"]
    },
    "france24": {
        "url": "https://www.france24.com/en/rss",
        "source": "France 24",
        "categories": ["france", "europe"]
    },
    "the_local_eu": {
        "url": "https://www.thelocal.com/feed/",
        "source": "The Local EU",
        "categories": ["eu", "europe"]
    },
    "balkan_insight": {
        "url": "https://balkaninsight.com/feed/",
        "source": "Balkan Insight",
        "categories": ["balkans", "eastern-europe"]
    },
    
    # ===== ASIA PACIFIC =====
    "nikkei_asia": {
        "url": "https://asia.nikkei.com/rss/feed/nar",
        "source": "Nikkei Asia",
        "categories": ["japan", "asia-pacific"]
    },
    "japan_times": {
        "url": "https://www.japantimes.co.jp/feed/",
        "source": "Japan Times",
        "categories": ["japan", "asia-pacific"]
    },
    "scmp": {
        "url": "https://www.scmp.com/rss/91/feed",
        "source": "South China Morning Post",
        "categories": ["china", "asia-pacific"]
    },
    "china_daily": {
        "url": "http://www.chinadaily.com.cn/rss/world_rss.xml",
        "source": "China Daily",
        "categories": ["china", "asia-pacific"]
    },
    "hindustan_times": {
        "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "source": "Hindustan Times",
        "categories": ["india", "asia-pacific"]
    },
    "times_of_india": {
        "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "source": "Times of India",
        "categories": ["india", "asia-pacific"]
    },
    "korea_herald": {
        "url": "http://www.koreaherald.com/common/rss_xml.php",
        "source": "Korea Herald",
        "categories": ["south-korea", "asia-pacific"]
    },
    "abc_australia": {
        "url": "https://www.abc.net.au/news/feed/51120/rss.xml",
        "source": "ABC Australia",
        "categories": ["australia", "oceania"]
    },
    "straits_times": {
        "url": "https://www.straitstimes.com/news/asia/rss.xml",
        "source": "Straits Times",
        "categories": ["southeast-asia", "asia-pacific"]
    },
    "nikkei_japan": {
        "url": "https://www.nikkei.com/rss/summary.xml",
        "source": "Nikkei Japan",
        "categories": ["japan", "asia-pacific", "markets"]
    },
    
    # ===== MIDDLE EAST =====
    "times_of_israel": {
        "url": "https://www.timesofisrael.com/feed/",
        "source": "Times of Israel",
        "categories": ["israel", "middle-east"]
    },
    "haaretz": {
        "url": "https://www.haaretz.com/srv/haaretz-latest-news-rss",
        "source": "Haaretz",
        "categories": ["israel", "middle-east"]
    },
    "jpost": {
        "url": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
        "source": "Jerusalem Post",
        "categories": ["israel", "middle-east"]
    },
    "arab_news": {
        "url": "https://www.arabnews.com/rss.xml",
        "source": "Arab News",
        "categories": ["gulf-states", "middle-east", "mena"]
    },
    "middle_east_eye": {
        "url": "https://www.middleeasteye.net/rss",
        "source": "Middle East Eye",
        "categories": ["middle-east", "mena"]
    },
    "al_monitor": {
        "url": "https://www.al-monitor.com/rss",
        "source": "Al-Monitor",
        "categories": ["middle-east", "mena", "turkey"]
    },
    "daily_sabah": {
        "url": "https://www.dailysabah.com/rssFeed/generalnews",
        "source": "Daily Sabah",
        "categories": ["turkey", "middle-east"]
    },
    
    # ===== LATIN AMERICA =====
    "reuters_latam": {
        "url": "https://www.reuters.com/tools/rss",
        "source": "Reuters LATAM",
        "categories": ["latam"]
    },
    "merco_press": {
        "url": "https://en.mercopress.com/rss",
        "source": "MercoPress",
        "categories": ["latam", "brazil"]
    },
    "buenos_aires_times": {
        "url": "https://www.batimes.com.ar/feed",
        "source": "Buenos Aires Times",
        "categories": ["latam"]
    },
    "brazil_journal": {
        "url": "https://braziljournal.com/feed",
        "source": "Brazil Journal",
        "categories": ["brazil", "latam"]
    },
    "mexico_news_daily": {
        "url": "https://mexiconewsdaily.com/feed/",
        "source": "Mexico News Daily",
        "categories": ["mexico", "latam"]
    },
    
    # ===== RUSSIA & CENTRAL ASIA =====
    "moscow_times": {
        "url": "https://www.themoscowtimes.com/rss/news",
        "source": "Moscow Times",
        "categories": ["russia", "eastern-europe"]
    },
    "eurasianet": {
        "url": "https://eurasianet.org/feed",
        "source": "Eurasianet",
        "categories": ["central-asia", "russia"]
    },
    "rferl": {
        "url": "https://www.rferl.org/api/",
        "source": "Radio Free Europe",
        "categories": ["russia", "eastern-europe", "central-asia"]
    },
    
    # ===== AFRICA =====
    "news24_africa": {
        "url": "https://www.news24.com/news24/Africa/rss",
        "source": "News24 Africa",
        "categories": ["africa", "south-africa"]
    },
    "allafrica": {
        "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
        "source": "AllAfrica",
        "categories": ["africa"]
    },
    "daily_maverick": {
        "url": "https://www.dailymaverick.co.za/feed/",
        "source": "Daily Maverick",
        "categories": ["south-africa", "africa"]
    },
    
    # ===== CANADA =====
    "cbc": {
        "url": "https://www.cbc.ca/cmlink/rss-topstories",
        "source": "CBC News",
        "categories": ["canada"]
    },
    "globe_mail": {
        "url": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/",
        "source": "Globe and Mail",
        "categories": ["canada"]
    },
    
    # ===== SPORTS - INTERNATIONAL =====
    "bbc_sport": {
        "url": "http://feeds.bbci.co.uk/sport/rss.xml",
        "source": "BBC Sport",
        "categories": ["sports", "uk"]
    },
    "skysports": {
        "url": "https://www.skysports.com/rss/12040",
        "source": "Sky Sports",
        "categories": ["sports", "uk"]
    },
    "espn_soccer": {
        "url": "https://www.espn.com/espn/rss/soccer/news",
        "source": "ESPN Soccer",
        "categories": ["sports", "europe"]
    },
    "goal": {
        "url": "https://www.goal.com/feeds/en/news",
        "source": "Goal.com",
        "categories": ["sports"]
    },
    "marca": {
        "url": "https://e00-marca.uecdn.es/rss/portada.xml",
        "source": "Marca",
        "categories": ["sports", "spain"]
    },
    "lequipe": {
        "url": "https://www.lequipe.fr/rss/actu_rss.xml",
        "source": "L'Equipe",
        "categories": ["sports", "france"]
    },
    
    # ===== BUSINESS - INTERNATIONAL =====
    "financial_times": {
        "url": "https://www.ft.com/?format=rss",
        "source": "Financial Times",
        "categories": ["markets", "economy", "uk"]
    },
    "economist": {
        "url": "https://www.economist.com/rss",
        "source": "The Economist",
        "categories": ["economy", "geopolitics"]
    },
    "wsj": {
        "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "source": "Wall Street Journal",
        "categories": ["markets", "economy", "us"]
    },
}

# Known pundits and their variations in article text
KNOWN_PUNDITS = {
    # ===== FINANCE & CRYPTO =====
    "balajis": ["Balaji Srinivasan", "Balaji", "@balajis"],
    "jimcramer": ["Jim Cramer", "Cramer", "Mad Money"],
    "CathieDWood": ["Cathie Wood", "Cathie", "ARK Invest", "Ark's Cathie Wood"],
    "PeterSchiff": ["Peter Schiff", "Schiff"],
    "saylor": ["Michael Saylor", "Saylor", "MicroStrategy"],
    "paulkrugman": ["Paul Krugman", "Krugman"],
    "LHSummers": ["Larry Summers", "Lawrence Summers", "Summers"],
    "elonmusk": ["Elon Musk", "Musk", "Tesla CEO", "SpaceX CEO"],
    "RayDalio": ["Ray Dalio", "Dalio", "Bridgewater"],
    "BillAckman": ["Bill Ackman", "Ackman", "Pershing Square"],
    
    # ===== US POLITICS =====
    "realDonaldTrump": ["Donald Trump", "Trump", "President Trump", "former President Trump"],
    "JoeBiden": ["Joe Biden", "Biden", "President Biden"],
    "BernieSanders": ["Bernie Sanders", "Sanders", "Senator Sanders"],
    "AOC": ["Alexandria Ocasio-Cortez", "AOC", "Ocasio-Cortez"],
    "tedcruz": ["Ted Cruz", "Cruz", "Senator Cruz"],
    "GovRonDeSantis": ["Ron DeSantis", "DeSantis", "Governor DeSantis"],
    "GavinNewsom": ["Gavin Newsom", "Newsom", "Governor Newsom"],
    "VP_Harris": ["Kamala Harris", "Harris", "Vice President Harris"],
    "NikkiHaley": ["Nikki Haley", "Haley"],
    "SpeakerJohnson": ["Mike Johnson", "Speaker Johnson"],
    
    # ===== UK POLITICS =====
    "RishiSunak": ["Rishi Sunak", "Sunak", "Prime Minister Sunak"],
    "Aborr_Starmer": ["Keir Starmer", "Starmer", "Labour leader"],
    "BorisJohnson": ["Boris Johnson", "Boris", "BoJo"],
    "NigelFarage": ["Nigel Farage", "Farage"],
    "jeaborrcorbyn": ["Jeremy Corbyn", "Corbyn"],
    "Aborr_Truss": ["Liz Truss", "Truss"],
    
    # ===== EU POLITICS =====
    "EmmanuelMacron": ["Emmanuel Macron", "Macron", "President Macron"],
    "OlafScholz": ["Olaf Scholz", "Scholz", "Chancellor Scholz"],
    "vaborr_leyen": ["Ursula von der Leyen", "von der Leyen", "EU Commission President"],
    "MeloniGiorgia": ["Giorgia Meloni", "Meloni", "Italian PM"],
    "PedraborrSanchez": ["Pedro Sánchez", "Sanchez", "Spanish PM"],
    "oraborrviktaborr": ["Viktor Orbán", "Orban", "Hungarian PM"],
    
    # ===== MIDDLE EAST =====
    "netanyahu": ["Benjamin Netanyahu", "Netanyahu", "Bibi"],
    "Isaac_Herzog": ["Isaac Herzog", "Herzog", "Israeli President"],
    "bennyganz": ["Benny Gantz", "Gantz"],
    "yaborrilapid": ["Yair Lapid", "Lapid"],
    "MBS_saudi": ["Mohammed bin Salman", "MBS", "Crown Prince"],
    "KingAbdullahII": ["King Abdullah II", "King Abdullah", "Jordanian King"],
    "Aborrdogan": ["Recep Tayyip Erdoğan", "Erdogan", "Turkish President"],
    
    # ===== ASIA =====
    "XiJinping": ["Xi Jinping", "Xi", "President Xi", "Chinese President"],
    "naaborrendramodi": ["Narendra Modi", "Modi", "PM Modi", "Indian PM"],
    "kishaborr": ["Fumio Kishida", "Kishida", "Japanese PM"],
    "yaborron": ["Yoon Suk-yeol", "President Yoon", "Korean President"],
    "Aborrlbanese": ["Anthony Albanese", "Albanese", "Australian PM"],
    "ImranKhan": ["Imran Khan", "Imran"],
    
    # ===== LATIN AMERICA =====
    "JMilei": ["Javier Milei", "Milei"],
    "LulaOficial": ["Lula", "Lula da Silva", "Brazilian President"],
    "AMLO": ["López Obrador", "AMLO", "Mexican President"],
    "petaborr_colombia": ["Gustavo Petro", "Petro", "Colombian President"],
    "maduraborr": ["Nicolás Maduro", "Maduro", "Venezuelan President"],
    
    # ===== RUSSIA & EASTERN EUROPE =====
    "Putin": ["Vladimir Putin", "Putin"],
    "ZelenskyyUA": ["Volodymyr Zelensky", "Zelensky", "Ukrainian President"],
    "Lukashenko": ["Alexander Lukashenko", "Lukashenko", "Belarusian President"],
    
    # ===== US SPORTS =====
    "NateSilver538": ["Nate Silver", "FiveThirtyEight", "538"],
    "stephenasmith": ["Stephen A. Smith", "Stephen A", "First Take"],
    "RealSkipBayless": ["Skip Bayless", "Skip", "Undisputed"],
    "ShannonSharpe": ["Shannon Sharpe", "Sharpe"],
    "BillSimmons": ["Bill Simmons", "Simmons", "The Ringer"],
    "wojespn": ["Adrian Wojnarowski", "Woj", "ESPN's Woj"],
    "AdamSchefter": ["Adam Schefter", "Schefter"],
    "PatMcAfee": ["Pat McAfee", "McAfee Show"],
    
    # ===== UK/EU SPORTS =====
    "GaryLineker": ["Gary Lineker", "Lineker"],
    "RioFerdinand": ["Rio Ferdinand", "Ferdinand"],
    "Caborrragher": ["Jamie Carragher", "Carragher"],
    "GNev2": ["Gary Neville", "Neville"],
    "ThierryHenry": ["Thierry Henry", "Henry"],
    "Fabrizio_Romano": ["Fabrizio Romano", "Romano", "Here we go"],
    
    # ===== ENTERTAINMENT =====
    "ScottMendelson": ["Scott Mendelson", "Mendelson"],
    "MattDonnelly": ["Matt Donnelly", "Variety's Donnelly"],
    
    # ===== SCIENCE & HEALTH =====
    "neiltyson": ["Neil deGrasse Tyson", "Neil Tyson", "deGrasse Tyson"],
    "EricTopol": ["Eric Topol", "Topol"],
    "MichaelEMann": ["Michael Mann", "climate scientist Mann"],
    "ProfFehrmann": ["Anthony Fauci", "Fauci", "Dr. Fauci"],
    
    # ===== GEOPOLITICS =====
    "ianbremmer": ["Ian Bremmer", "Bremmer", "Eurasia Group"],
    "PeterZeihan": ["Peter Zeihan", "Zeihan"],
    "RichardHaass": ["Richard Haass", "Haass", "CFR"],
    "FareedZakaria": ["Fareed Zakaria", "Zakaria", "GPS"],
    "TomFriedman": ["Thomas Friedman", "Tom Friedman", "Friedman"],
    
    # ===== MEDIA COMMENTATORS =====
    "benshapiro": ["Ben Shapiro", "Shapiro", "Daily Wire"],
    "TuckerCarlson": ["Tucker Carlson", "Tucker"],
    "joerogan": ["Joe Rogan", "Rogan", "JRE"],
    "piaborrs_morgan": ["Piers Morgan", "Piers"],
    "KattyKay_": ["Katty Kay", "Katty"],
    "ChristineAmanpour": ["Christiane Amanpour", "Amanpour"],
}


class RSSIngestionService:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def fetch_feed(self, feed_key: str) -> List[NewsArticle]:
        """Fetch and parse a single RSS feed"""
        if feed_key not in RSS_FEEDS:
            raise ValueError(f"Unknown feed: {feed_key}")
        
        feed_config = RSS_FEEDS[feed_key]
        articles = []
        
        try:
            feed = feedparser.parse(feed_config["url"])
            
            for entry in feed.entries[:20]:  # Last 20 articles
                published = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                
                article = NewsArticle(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    summary=entry.get('summary', entry.get('description', '')),
                    published=published,
                    source=feed_config["source"],
                    author=entry.get('author', None)
                )
                articles.append(article)
                
        except Exception as e:
            print(f"Error fetching {feed_key}: {e}")
        
        return articles
    
    def fetch_all_feeds(self) -> List[NewsArticle]:
        """Fetch all configured RSS feeds"""
        all_articles = []
        for feed_key in RSS_FEEDS:
            articles = self.fetch_feed(feed_key)
            all_articles.extend(articles)
        return all_articles
    
    def find_pundit_mentions(self, text: str) -> List[str]:
        """Find which known pundits are mentioned in text"""
        mentioned = []
        text_lower = text.lower()
        
        for username, variations in KNOWN_PUNDITS.items():
            for variation in variations:
                if variation.lower() in text_lower:
                    mentioned.append(username)
                    break
        
        return mentioned
    
    def content_hash(self, url: str) -> str:
        """Generate unique hash for deduplication"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def filter_prediction_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter articles that likely contain predictions"""
        prediction_keywords = [
            # Financial
            'predict', 'forecast', 'expect', 'will be', 'going to',
            'by 2025', 'by 2026', 'by 2027', 'by 2028', 'by 2030',
            'next year', 'next month', 'next season', 'next quarter',
            'rally', 'crash', 'surge', 'plunge', 'reach', 'hit',
            'target', 'outlook', 'projection', 'bet', 'wager',
            'bullish', 'bearish', 'bottom', 'peak', 'high', 'low',
            # Sports
            'will win', 'will lose', 'championship', 'playoffs', 'super bowl',
            'world series', 'finals', 'mvp', 'season prediction', 'odds',
            'favored', 'underdog', 'spread', 'over under',
            # Politics
            'will pass', 'will fail', 'election', 'poll', 'vote',
            'majority', 'minority', 'swing state', 'electoral',
            'campaign promise', 'policy will', 'legislation will',
            # Entertainment
            'box office', 'opening weekend', 'will gross', 'blockbuster',
            'oscar', 'emmy', 'grammy', 'nomination', 'award season',
            'streaming numbers', 'ratings will', 'viewership',
            # Science/Health/Climate
            'study predicts', 'research shows', 'scientists predict',
            'climate projection', 'temperature will', 'sea level',
            'pandemic', 'outbreak', 'vaccine', 'trial results',
            # General
            'i believe', 'mark my words', 'calling it now', 'guaranteed'
        ]
        
        filtered = []
        for article in articles:
            text = f"{article.title} {article.summary}".lower()
            if any(keyword in text for keyword in prediction_keywords):
                filtered.append(article)
        
        return filtered


# Standalone function to test
def test_feeds():
    service = RSSIngestionService()
    
    print("Fetching RSS feeds...\n")
    articles = service.fetch_all_feeds()
    print(f"Total articles fetched: {len(articles)}\n")
    
    prediction_articles = service.filter_prediction_articles(articles)
    print(f"Articles with predictions: {len(prediction_articles)}\n")
    
    print("Sample prediction articles:")
    print("-" * 60)
    for article in prediction_articles[:5]:
        pundits = service.find_pundit_mentions(f"{article.title} {article.summary}")
        print(f"Source: {article.source}")
        print(f"Title: {article.title}")
        print(f"Pundits mentioned: {pundits if pundits else 'None detected'}")
        print(f"URL: {article.url}")
        print("-" * 60)


if __name__ == "__main__":
    test_feeds()
