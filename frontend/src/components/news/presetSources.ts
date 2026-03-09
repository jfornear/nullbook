export interface PresetSource {
  name: string;
  url: string;
  feed_url: string;
  description: string;
}

export const PRESET_SOURCES: PresetSource[] = [
  {
    name: "Reuters Business",
    url: "https://www.reuters.com/business",
    feed_url: "https://www.reuters.com/business/rss",
    description: "Global business and financial news",
  },
  {
    name: "CNBC",
    url: "https://www.cnbc.com",
    feed_url: "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    description: "Markets, investing, and business news",
  },
  {
    name: "MarketWatch",
    url: "https://www.marketwatch.com",
    feed_url: "https://feeds.marketwatch.com/marketwatch/topstories",
    description: "Stock market data and analysis",
  },
  {
    name: "Yahoo Finance",
    url: "https://finance.yahoo.com",
    feed_url: "https://finance.yahoo.com/news/rssindex",
    description: "Financial news, quotes, and analysis",
  },
  {
    name: "Bloomberg",
    url: "https://www.bloomberg.com",
    feed_url: "https://www.bloomberg.com/feed/podcast/etf-report.xml",
    description: "Business, financial, and market news",
  },
  {
    name: "The Wall Street Journal",
    url: "https://www.wsj.com",
    feed_url: "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    description: "Business and financial journalism",
  },
  {
    name: "Financial Times",
    url: "https://www.ft.com",
    feed_url: "https://www.ft.com/rss/home",
    description: "International business news",
  },
  {
    name: "Seeking Alpha",
    url: "https://seekingalpha.com",
    feed_url: "https://seekingalpha.com/feed.xml",
    description: "Stock market analysis and opinion",
  },
  {
    name: "The Motley Fool",
    url: "https://www.fool.com",
    feed_url: "https://www.fool.com/feeds/index.aspx",
    description: "Investing insights and stock picks",
  },
  {
    name: "Investopedia",
    url: "https://www.investopedia.com",
    feed_url: "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
    description: "Financial education and market news",
  },
  {
    name: "SEC EDGAR Filings",
    url: "https://www.sec.gov/cgi-bin/browse-edgar",
    feed_url:
      "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=40&search_text=&start=0&output=atom",
    description: "SEC filing alerts and regulatory updates",
  },
  {
    name: "Federal Reserve",
    url: "https://www.federalreserve.gov",
    feed_url: "https://www.federalreserve.gov/feeds/press_all.xml",
    description: "Fed announcements and economic data",
  },
];
