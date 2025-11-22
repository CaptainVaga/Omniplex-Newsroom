#!/usr/bin/env python3
"""
WE333 FULL DATA GENERATOR - JHU-Style UK Democracy Dashboard
All sources: Parliament, Gov.uk, News, Social
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class UKParliamentFullAPI:
    """Complete UK Parliament API integration"""

    def __init__(self):
        self.members_url = "https://members-api.parliament.uk/api"
        self.bills_url = "https://bills-api.parliament.uk/api/v1"
        self.commons_votes_url = "https://commonsvotes-api.parliament.uk/data"
        self.lords_votes_url = "https://lordsvotes-api.parliament.uk/data"
        self.hansard_url = "https://hansard-api.parliament.uk"

    def get_bills(self, limit=20) -> List[Dict]:
        """Get current bills"""
        try:
            response = requests.get(
                f"{self.bills_url}/Bills",
                params={"CurrentHouse": "All", "take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"  Bills error: {e}")
            return []

    def get_commons_divisions(self, limit=20) -> List[Dict]:
        """Get House of Commons votes"""
        try:
            response = requests.get(
                f"{self.commons_votes_url}/divisions.json/search",
                params={"take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Commons divisions error: {e}")
            return []

    def get_lords_divisions(self, limit=10) -> List[Dict]:
        """Get House of Lords votes"""
        try:
            response = requests.get(
                f"{self.lords_votes_url}/Divisions/search",
                params={"take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Lords divisions error: {e}")
            return []

    def get_mps(self, limit=50) -> List[Dict]:
        """Get current MPs"""
        try:
            response = requests.get(
                f"{self.members_url}/Members/Search",
                params={"House": 1, "IsCurrentMember": True, "take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"  MPs error: {e}")
            return []

    def get_lords(self, limit=50) -> List[Dict]:
        """Get current Lords"""
        try:
            response = requests.get(
                f"{self.members_url}/Members/Search",
                params={"House": 2, "IsCurrentMember": True, "take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"  Lords error: {e}")
            return []

    def get_written_questions(self, limit=20) -> List[Dict]:
        """Get recent written questions"""
        try:
            response = requests.get(
                "https://questions-statements-api.parliament.uk/api/writtenquestions/questions",
                params={"take": limit, "answered": "Any"},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"  Written questions error: {e}")
            return []

    def get_oral_questions(self, limit=10) -> List[Dict]:
        """Get upcoming oral questions"""
        try:
            response = requests.get(
                "https://questions-statements-api.parliament.uk/api/oralquestions/list",
                params={"take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"  Oral questions error: {e}")
            return []

    def get_committees(self, limit=20) -> List[Dict]:
        """Get parliamentary committees"""
        try:
            response = requests.get(
                "https://committees-api.parliament.uk/api/Committees",
                params={"take": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"  Committees error: {e}")
            return []


class GovUKAPI:
    """UK Government data sources"""

    def __init__(self):
        self.base_url = "https://www.gov.uk/api"

    def get_announcements(self, limit=10) -> List[Dict]:
        """Get government announcements"""
        try:
            response = requests.get(
                f"{self.base_url}/search.json",
                params={
                    "filter_content_purpose_supergroup": "news_and_communications",
                    "count": limit,
                    "order": "-public_timestamp"
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"  Gov.uk announcements error: {e}")
            return []

    def get_policies(self, limit=10) -> List[Dict]:
        """Get policy papers"""
        try:
            response = requests.get(
                f"{self.base_url}/search.json",
                params={
                    "filter_content_purpose_supergroup": "policy_and_engagement",
                    "count": limit,
                    "order": "-public_timestamp"
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"  Gov.uk policies error: {e}")
            return []

    def get_statistics(self, limit=10) -> List[Dict]:
        """Get government statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/search.json",
                params={
                    "filter_content_purpose_supergroup": "research_and_statistics",
                    "count": limit,
                    "order": "-public_timestamp"
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"  Gov.uk statistics error: {e}")
            return []


class NewsFeeds:
    """News RSS feed aggregator"""

    def __init__(self):
        self.feeds = {
            "bbc_politics": "https://feeds.bbci.co.uk/news/politics/rss.xml",
            "bbc_uk": "https://feeds.bbci.co.uk/news/uk/rss.xml",
            "guardian_politics": "https://www.theguardian.com/politics/rss"
        }

    def parse_rss(self, url: str, limit=10) -> List[Dict]:
        """Parse RSS feed"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Simple XML parsing without external lib
            import re
            items = []
            item_pattern = r'<item>(.*?)</item>'
            title_pattern = r'<title>(.*?)</title>'
            link_pattern = r'<link>(.*?)</link>'
            pubdate_pattern = r'<pubDate>(.*?)</pubDate>'

            matches = re.findall(item_pattern, response.text, re.DOTALL)

            for match in matches[:limit]:
                title = re.search(title_pattern, match)
                link = re.search(link_pattern, match)
                pubdate = re.search(pubdate_pattern, match)

                items.append({
                    "title": title.group(1) if title else "Unknown",
                    "link": link.group(1) if link else "",
                    "date": pubdate.group(1) if pubdate else ""
                })

            return items
        except Exception as e:
            print(f"  RSS error ({url}): {e}")
            return []

    def get_bbc_politics(self, limit=10) -> List[Dict]:
        """Get BBC Politics news"""
        return self.parse_rss(self.feeds["bbc_politics"], limit)

    def get_bbc_uk(self, limit=10) -> List[Dict]:
        """Get BBC UK news"""
        return self.parse_rss(self.feeds["bbc_uk"], limit)

    def get_guardian_politics(self, limit=10) -> List[Dict]:
        """Get Guardian Politics news"""
        return self.parse_rss(self.feeds["guardian_politics"], limit)


class GeminiAnalyzer:
    """Google Gemini AI analyzer"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model = None

        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except:
                self.model = genai.GenerativeModel('gemini-pro')

    def analyze(self, data: Dict) -> str:
        """Generate comprehensive analysis"""
        if not self.model:
            return self.local_analysis(data)

        try:
            # Build summary of data
            bills = data.get('parliament', {}).get('bills', [])
            votes = data.get('parliament', {}).get('commons_divisions', [])
            news = data.get('news', {}).get('bbc_politics', [])
            gov = data.get('government', {}).get('announcements', [])

            prompt = f"""You are WE333, an AI journalism assistant. Analyze this UK democracy data:

PARLIAMENT:
- {len(bills)} active bills
- {len(votes)} recent votes
- Key bills: {', '.join([b.get('shortTitle', '')[:30] for b in bills[:3]])}

NEWS HEADLINES:
{chr(10).join(['- ' + n.get('title', '')[:60] for n in news[:5]])}

GOVERNMENT:
{chr(10).join(['- ' + g.get('title', '')[:60] for g in gov[:3]])}

Provide a brief (4-5 sentences) factual analysis covering:
1. Key parliamentary activity
2. Major news themes
3. Government focus areas
4. Potential public impact

Be objective. End with "Human review recommended." """

            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"  Gemini analysis error: {e}")
            return self.local_analysis(data)

    def local_analysis(self, data: Dict) -> str:
        """Fallback local analysis"""
        parts = []
        parliament = data.get('parliament', {})

        if parliament.get('bills'):
            parts.append(f"{len(parliament['bills'])} bills in Parliament")
        if parliament.get('commons_divisions'):
            parts.append(f"{len(parliament['commons_divisions'])} recent Commons votes")
        if parliament.get('lords_divisions'):
            parts.append(f"{len(parliament['lords_divisions'])} Lords votes")
        if data.get('news', {}).get('bbc_politics'):
            parts.append(f"{len(data['news']['bbc_politics'])} news stories tracked")
        if data.get('government', {}).get('announcements'):
            parts.append(f"{len(data['government']['announcements'])} government announcements")

        parts.append("Human review recommended.")
        return " | ".join(parts)


def generate_full_data():
    """Generate comprehensive UK democracy data"""
    print("\n" + "="*60)
    print(" WE333 FULL DATA GENERATOR")
    print("="*60)

    parliament = UKParliamentFullAPI()
    govuk = GovUKAPI()
    news = NewsFeeds()
    gemini = GeminiAnalyzer()

    data = {
        "timestamp": datetime.now().isoformat(),
        "parliament": {},
        "government": {},
        "news": {},
        "analysis": "",
        "stats": {},
        "sha_hash": ""
    }

    # === PARLIAMENT DATA ===
    print("\n PARLIAMENT DATA:")

    print("  Fetching bills...")
    data['parliament']['bills'] = parliament.get_bills(20)
    print(f"    {len(data['parliament']['bills'])} bills")

    print("  Fetching Commons divisions...")
    data['parliament']['commons_divisions'] = parliament.get_commons_divisions(20)
    print(f"    {len(data['parliament']['commons_divisions'])} votes")

    print("  Fetching Lords divisions...")
    data['parliament']['lords_divisions'] = parliament.get_lords_divisions(10)
    print(f"    {len(data['parliament']['lords_divisions'])} votes")

    print("  Fetching MPs...")
    data['parliament']['mps'] = parliament.get_mps(50)
    print(f"    {len(data['parliament']['mps'])} MPs")

    print("  Fetching Lords...")
    data['parliament']['lords'] = parliament.get_lords(50)
    print(f"    {len(data['parliament']['lords'])} Lords")

    print("  Fetching written questions...")
    data['parliament']['written_questions'] = parliament.get_written_questions(20)
    print(f"    {len(data['parliament']['written_questions'])} questions")

    print("  Fetching committees...")
    data['parliament']['committees'] = parliament.get_committees(20)
    print(f"    {len(data['parliament']['committees'])} committees")

    # === GOVERNMENT DATA ===
    print("\n GOVERNMENT DATA:")

    print("  Fetching announcements...")
    data['government']['announcements'] = govuk.get_announcements(15)
    print(f"    {len(data['government']['announcements'])} announcements")

    print("  Fetching policies...")
    data['government']['policies'] = govuk.get_policies(10)
    print(f"    {len(data['government']['policies'])} policies")

    print("  Fetching statistics...")
    data['government']['statistics'] = govuk.get_statistics(10)
    print(f"    {len(data['government']['statistics'])} statistics")

    # === NEWS DATA ===
    print("\n NEWS DATA:")

    print("  Fetching BBC Politics...")
    data['news']['bbc_politics'] = news.get_bbc_politics(15)
    print(f"    {len(data['news']['bbc_politics'])} stories")

    print("  Fetching BBC UK...")
    data['news']['bbc_uk'] = news.get_bbc_uk(15)
    print(f"    {len(data['news']['bbc_uk'])} stories")

    print("  Fetching Guardian Politics...")
    data['news']['guardian_politics'] = news.get_guardian_politics(15)
    print(f"    {len(data['news']['guardian_politics'])} stories")

    # === STATS ===
    data['stats'] = {
        "total_bills": len(data['parliament'].get('bills', [])),
        "total_votes": len(data['parliament'].get('commons_divisions', [])) + len(data['parliament'].get('lords_divisions', [])),
        "total_mps": len(data['parliament'].get('mps', [])),
        "total_lords": len(data['parliament'].get('lords', [])),
        "total_questions": len(data['parliament'].get('written_questions', [])),
        "total_committees": len(data['parliament'].get('committees', [])),
        "total_news": len(data['news'].get('bbc_politics', [])) + len(data['news'].get('guardian_politics', [])),
        "total_gov_updates": len(data['government'].get('announcements', [])) + len(data['government'].get('policies', []))
    }

    # === AI ANALYSIS ===
    print("\n AI ANALYSIS:")
    print("  Generating with Gemini...")
    data['analysis'] = gemini.analyze(data)
    print("    Done")

    # === SHA HASH ===
    data['sha_hash'] = hashlib.sha256(
        json.dumps(data, default=str).encode()
    ).hexdigest()[:32]

    # === SAVE ===
    output_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print("\n" + "="*60)
    print(" DATA GENERATION COMPLETE")
    print("="*60)
    print(f" Bills: {data['stats']['total_bills']}")
    print(f" Votes: {data['stats']['total_votes']}")
    print(f" MPs: {data['stats']['total_mps']}")
    print(f" Lords: {data['stats']['total_lords']}")
    print(f" Questions: {data['stats']['total_questions']}")
    print(f" News: {data['stats']['total_news']}")
    print(f" Gov Updates: {data['stats']['total_gov_updates']}")
    print(f" SHA: {data['sha_hash']}")
    print("="*60)

    return data


if __name__ == "__main__":
    generate_full_data()
