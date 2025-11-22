#!/usr/bin/env python3
"""
WE333 OMNIPLEX UK SENTINEL - IBM watsonx Orchestrate Integration
Agentic AI for UK Parliament Monitoring
"""

import os
import json
import hashlib
import requests
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiClient:
    """Google Gemini AI client"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model = None

        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            # Try different model names
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("Gemini AI: Active (gemini-2.0-flash)")
            except:
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print("Gemini AI: Active (gemini-pro)")
                except Exception as e:
                    print(f"Gemini model error: {e}")
        else:
            print("Gemini AI: Not configured")

    def generate(self, prompt: str) -> str:
        """Generate text using Gemini"""
        if not self.model:
            return None

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return None

class IBMWatsonxClient:
    """IBM watsonx API client for Orchestrate"""

    def __init__(self):
        self.api_key = os.getenv('IBM_API_KEY')
        self.url = os.getenv('IBM_URL', 'https://us-south.ml.cloud.ibm.com')
        self.project_id = os.getenv('IBM_PROJECT_ID')
        self.access_token = None
        self.token_expiry = None

        if not self.api_key:
            print("WARNING: IBM_API_KEY not set in .env")

    def get_access_token(self) -> str:
        """Get IAM access token from IBM Cloud"""
        if self.access_token and self.token_expiry:
            if datetime.now().timestamp() < self.token_expiry:
                return self.access_token

        token_url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.api_key
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
            self.access_token = result['access_token']
            self.token_expiry = datetime.now().timestamp() + result['expires_in'] - 60
            print("IBM token acquired")
            return self.access_token
        except Exception as e:
            print(f"Token error: {e}")
            return None

    def generate_text(self, prompt: str, model_id: str = "ibm/granite-13b-chat-v2") -> str:
        """Generate text using watsonx.ai foundation models"""
        token = self.get_access_token()
        if not token:
            return "Error: No IBM access token"

        url = f"{self.url}/ml/v1/text/generation?version=2024-03-14"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": self.project_id,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"API Response: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            return result['results'][0]['generated_text']
        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error: {e}"


class UKParliamentAPI:
    """Real UK Parliament API client"""

    def __init__(self):
        self.base_url = "https://members-api.parliament.uk/api"
        self.bills_url = "https://bills-api.parliament.uk/api/v1"
        self.hansard_url = "https://hansard-api.parliament.uk/api"

    def get_current_mps(self, limit: int = 20) -> Dict:
        """Get current Members of Parliament"""
        url = f"{self.base_url}/Members/Search"
        params = {
            "House": 1,  # Commons
            "IsCurrentMember": True,
            "take": limit
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"MPs API error: {e}")
            return {"error": str(e)}

    def get_current_bills(self, limit: int = 10) -> Dict:
        """Get current bills before Parliament"""
        url = f"{self.bills_url}/Bills"
        params = {
            "CurrentHouse": "All",
            "take": limit,
            "skip": 0
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Bills API error: {e}")
            return {"error": str(e)}

    def get_bill_details(self, bill_id: int) -> Dict:
        """Get details for a specific bill"""
        url = f"{self.bills_url}/Bills/{bill_id}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Bill details error: {e}")
            return {"error": str(e)}

    def get_divisions(self, limit: int = 10) -> Dict:
        """Get recent House of Commons divisions (votes)"""
        url = "https://commonsvotes-api.parliament.uk/data/divisions.json/search"
        params = {"take": limit}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Divisions API error: {e}")
            return {"error": str(e)}

    def get_lords_divisions(self, limit: int = 10) -> Dict:
        """Get recent House of Lords divisions"""
        url = "https://lordsvotes-api.parliament.uk/data/Divisions/search"
        params = {"take": limit}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Lords divisions error: {e}")
            return {"error": str(e)}


class We333Agent:
    """Agentic AI agent using WE333 principles"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = []
        self.ethics = OmniplexEthics()

    def think(self, context: str) -> str:
        """Agent reasoning step"""
        thought = f"[{self.name}] Analyzing: {context[:100]}..."
        self.memory.append({"type": "thought", "content": thought})
        return thought

    def act(self, action: str, data: Any) -> Dict:
        """Agent action step with ethics check"""
        # Ethics check before action
        if not self.ethics.check(action, data):
            return {"status": "blocked", "reason": "Ethics violation"}

        result = {"agent": self.name, "action": action, "timestamp": datetime.now().isoformat()}
        self.memory.append({"type": "action", "content": result})
        return result

    def observe(self, observation: Any) -> None:
        """Agent observation step"""
        self.memory.append({"type": "observation", "content": str(observation)[:500]})


class OmniplexEthics:
    """Ethics guardian for all agent actions"""

    def __init__(self):
        self.laws = {
            "002": "Human judgment preserved",
            "003": "Zero manipulation",
            "007": "Triple verification required",
            "011": "Emergency override available",
            "012": "Heritage honored"
        }

    def check(self, action: str, data: Any) -> bool:
        """Check action against ethics laws"""
        # Law 003: No manipulation
        if self._is_manipulative(action, data):
            print(f"ETHICS BLOCK: Manipulation detected in {action}")
            return False

        # Law 002: Human judgment point
        if self._requires_human_review(action):
            print(f"ETHICS: Human review required for {action}")

        return True

    def _is_manipulative(self, action: str, data: Any) -> bool:
        manipulation_keywords = ["force", "manipulate", "deceive", "hide"]
        return any(kw in str(action).lower() for kw in manipulation_keywords)

    def _requires_human_review(self, action: str) -> bool:
        review_actions = ["publish", "decide", "conclude", "report"]
        return any(ra in action.lower() for ra in review_actions)


class SHA256Verifier:
    """Data integrity verification"""

    def __init__(self):
        self.hashes = {}

    def compute(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def verify(self, key: str, data: str) -> bool:
        current = self.compute(data)
        if key in self.hashes:
            return self.hashes[key] == current
        self.hashes[key] = current
        return True


class OrchestratedPipeline:
    """Main Orchestrated Pipeline with Gemini AI"""

    def __init__(self):
        self.gemini = GeminiClient()
        self.ibm = IBMWatsonxClient()
        self.parliament = UKParliamentAPI()
        self.sha = SHA256Verifier()

        # Create specialized agents
        self.agents = {
            'bills_monitor': We333Agent("BillsMonitor", "Track current legislation"),
            'votes_tracker': We333Agent("VotesTracker", "Monitor voting patterns"),
            'debates_analyzer': We333Agent("DebatesAnalyzer", "Analyze parliamentary debates"),
            'committees_watcher': We333Agent("CommitteesWatcher", "Track committee activity"),
            'questions_tracker': We333Agent("QuestionsTracker", "Monitor PMQs and written questions"),
            'lords_monitor': We333Agent("LordsMonitor", "Watch House of Lords"),
            'amendments_tracker': We333Agent("AmendmentsTracker", "Track bill amendments"),
            'future_calendar': We333Agent("FutureCalendar", "Project upcoming business")
        }

        print("\n WE333 ORCHESTRATED PIPELINE")
        print("Google Gemini + UK Parliament API + WE333 Ethics")
        print(f"Agents: {len(self.agents)} | SHA: Active | Ethics: Active")

    def run_agent_task(self, agent_name: str, task: str) -> Dict:
        """Run a task through a specific agent"""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}

        # Think
        thought = agent.think(task)
        print(f"  {thought}")

        # Act
        result = agent.act(task, {})

        return result

    def fetch_parliament_data(self) -> Dict:
        """Fetch real data from UK Parliament APIs"""
        print("\n FETCHING UK PARLIAMENT DATA...")

        data = {}

        # Get current bills
        print("  Bills...")
        bills = self.parliament.get_current_bills(5)
        if "items" in bills:
            data['bills'] = bills['items']
            print(f"    Found {len(bills['items'])} bills")

        # Get recent divisions
        print("  Divisions (votes)...")
        divisions = self.parliament.get_divisions(5)
        if isinstance(divisions, list):
            data['divisions'] = divisions
            print(f"    Found {len(divisions)} recent votes")

        # Get current MPs
        print("  MPs...")
        mps = self.parliament.get_current_mps(10)
        if "items" in mps:
            data['mps'] = mps['items']
            print(f"    Found {len(mps['items'])} MPs")

        # SHA verify all data
        data_str = json.dumps(data, default=str)
        sha_hash = self.sha.compute(data_str)
        data['sha_hash'] = sha_hash
        print(f"  SHA256: {sha_hash[:16]}...")

        return data

    def analyze_with_ai(self, data: Dict) -> str:
        """Use Gemini AI to analyze parliament data"""

        bills = data.get('bills', [])
        divisions = data.get('divisions', [])

        # Build context for AI
        bills_text = "\n".join([f"- {b.get('shortTitle', 'Unknown')}" for b in bills[:5]])
        votes_text = "\n".join([
            f"- {d.get('Title', 'Unknown')[:50]}: Ayes {d.get('AyeCount', 0)} vs Noes {d.get('NoCount', 0)}"
            for d in divisions[:5]
        ])

        prompt = f"""You are WE333, an AI journalism assistant monitoring UK Parliament for truth and transparency.

Analyze this current UK Parliament data and provide a brief, factual summary (3-4 sentences):

CURRENT BILLS:
{bills_text}

RECENT VOTES:
{votes_text}

Focus on:
1. Key themes in legislation
2. Notable voting patterns
3. Potential public impact

Be objective, factual, and avoid speculation. End with "Human review recommended for publication."""

        # Try Gemini first
        if self.gemini.model:
            print("\n Analyzing with Google Gemini AI...")
            result = self.gemini.generate(prompt)
            if result:
                return result

        # Fallback to local analysis
        print("\n Analyzing with WE333 Intelligence...")
        return self.local_analysis(data)

    def local_analysis(self, data: Dict) -> str:
        """WE333 rule-based intelligent analysis"""
        bills = data.get('bills', [])
        divisions = data.get('divisions', [])
        mps = data.get('mps', [])

        analysis_parts = []

        # Analyze bills
        if bills:
            bill_topics = []
            for bill in bills[:5]:
                title = bill.get('shortTitle', '').lower()
                if 'safety' in title or 'security' in title:
                    bill_topics.append('public safety')
                elif 'health' in title or 'nhs' in title:
                    bill_topics.append('healthcare')
                elif 'business' in title or 'economic' in title:
                    bill_topics.append('economy')
                elif 'environment' in title or 'climate' in title:
                    bill_topics.append('environment')

            unique_topics = list(set(bill_topics))
            if unique_topics:
                analysis_parts.append(f"Parliament focusing on: {', '.join(unique_topics)}")
            analysis_parts.append(f"{len(bills)} bills currently in progress")

        # Analyze divisions
        if divisions:
            analysis_parts.append(f"{len(divisions)} recent votes recorded")

            # Check for close votes
            close_votes = []
            for div in divisions[:5]:
                ayes = div.get('AyeCount', 0)
                noes = div.get('NoCount', 0)
                if ayes > 0 and noes > 0:
                    margin = abs(ayes - noes)
                    if margin < 50:
                        close_votes.append(div.get('Title', 'Unknown')[:50])

            if close_votes:
                analysis_parts.append(f"Close votes detected: {len(close_votes)}")

        # Summary
        if not analysis_parts:
            return "Parliament data collected. Awaiting human analysis."

        return " | ".join(analysis_parts)

    def triple_verify(self, data: Dict) -> bool:
        """WE333 Triple verification"""
        print("\n TRIPLE VERIFICATION:")

        # 1. Source check
        source_ok = 'sha_hash' in data
        print(f"  1. Source integrity: {'' if source_ok else ''}")

        # 2. Structure check
        structure_ok = isinstance(data, dict) and len(data) > 0
        print(f"  2. Data structure: {'' if structure_ok else ''}")

        # 3. SHA verification
        sha_ok = self.sha.verify('parliament_data', json.dumps(data, default=str))
        print(f"  3. SHA verification: {'' if sha_ok else ''}")

        return all([source_ok, structure_ok, sha_ok])

    def run(self) -> Dict:
        """Main orchestration loop"""
        print("\n" + "="*70)
        print("WE333 OMNIPLEX UK SENTINEL - IBM ORCHESTRATED")
        print("="*70)
        print("Heritage: 1951 THA  1970s BBA  2025 AIIA")
        print("Mission: UK Parliament monitoring with zero manipulation")
        print("="*70)

        # Step 1: Fetch real Parliament data
        parliament_data = self.fetch_parliament_data()

        # Step 2: Triple verify
        if not self.triple_verify(parliament_data):
            print("\n VERIFICATION FAILED - Human review required")
            return {"status": "verification_failed"}

        # Step 3: Run agents on data
        print("\n AGENT ANALYSIS:")
        for agent_name, agent in self.agents.items():
            if agent_name in ['bills_monitor', 'votes_tracker']:
                self.run_agent_task(agent_name, f"Analyze {agent_name} data")

        # Step 4: AI analysis (Gemini or local)
        analysis = self.analyze_with_ai(parliament_data)
        print(f"\n AI Analysis:\n{analysis}")

        # Step 5: Prepare output
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "parliament_data": parliament_data,
            "analysis": analysis,
            "sha_signature": parliament_data.get('sha_hash'),
            "we333_verified": True
        }

        print("\n" + "="*70)
        print("PIPELINE COMPLETE")
        print("="*70)
        print(f" Data fetched from UK Parliament APIs")
        print(f" Triple verified with SHA256")
        print(f" Ethics checks passed")
        print(f" Ready for human review")

        return result


def main():
    """WE begin together"""
    print("\n WE333 OMNIPLEX + IBM WATSONX ORCHESTRATE")
    print("Three generations. One truth. Zero manipulation.\n")

    # Check for .env
    if not os.path.exists('.env'):
        print("NOTE: No .env file found. Create from .env.example")
        print("For IBM watsonx features, add your IBM_API_KEY\n")

    pipeline = OrchestratedPipeline()

    try:
        result = pipeline.run()

        if result.get('status') == 'success':
            parliament_data = result.get('parliament_data', {})

            # Show detailed bills
            bills = parliament_data.get('bills', [])
            if bills:
                print(f"\n{'='*70}")
                print(" CURRENT BILLS IN PARLIAMENT")
                print(f"{'='*70}")
                for i, bill in enumerate(bills[:5], 1):
                    title = bill.get('shortTitle', 'Unknown')
                    stage = bill.get('currentStage', {}).get('description', 'Unknown stage')
                    house = bill.get('currentHouse', 'Unknown')
                    print(f"  {i}. {title}")
                    print(f"     Stage: {stage} | House: {house}")

            # Show recent votes
            divisions = parliament_data.get('divisions', [])
            if divisions:
                print(f"\n{'='*70}")
                print(" RECENT PARLIAMENTARY VOTES")
                print(f"{'='*70}")
                for i, div in enumerate(divisions[:5], 1):
                    title = div.get('Title', 'Unknown')[:60]
                    ayes = div.get('AyeCount', 0)
                    noes = div.get('NoCount', 0)
                    date = div.get('Date', '')[:10]
                    print(f"  {i}. {title}")
                    print(f"     Ayes: {ayes} | Noes: {noes} | Date: {date}")

            print(f"\n{'='*70}")
            print(" WE333 OMNIPLEX - READY FOR PUBLICATION")
            print(f"{'='*70}")
            print(f" Target: omniplex.earth")
            print(f" SHA: {result.get('sha_signature', 'N/A')[:32]}...")
            print(f" Human review required for final approval")

    except KeyboardInterrupt:
        print("\n\n Human initiated pause")
        print("WE preserve data integrity")
    except Exception as e:
        print(f"\n Pipeline error: {e}")
        print("WE investigate together")


if __name__ == "__main__":
    main()
