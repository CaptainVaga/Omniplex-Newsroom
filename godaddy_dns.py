#!/usr/bin/env python3
"""
WE333 GODADDY DNS MANAGER
Connect domains to GitHub Pages automatically
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GoDaddyDNS:
    """GoDaddy DNS Management for WE333 domains"""

    def __init__(self):
        self.api_key = os.getenv('GODADDY_API_KEY')
        self.api_secret = os.getenv('GODADDY_API_SECRET')
        self.base_url = "https://api.godaddy.com/v1"

        if self.api_key and self.api_secret:
            self.headers = {
                "Authorization": f"sso-key {self.api_key}:{self.api_secret}",
                "Content-Type": "application/json"
            }
            print("✓ GoDaddy API: Ready")
        else:
            self.headers = None
            print("✗ GoDaddy API: No credentials")

    def list_domains(self):
        """List all domains in account"""
        if not self.headers:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/domains",
                headers=self.headers
            )
            response.raise_for_status()
            domains = response.json()
            return domains
        except Exception as e:
            print(f"Error listing domains: {e}")
            return []

    def get_dns_records(self, domain: str):
        """Get DNS records for a domain"""
        if not self.headers:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/domains/{domain}/records",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting DNS records: {e}")
            return []

    def setup_github_pages(self, domain: str, github_username: str = "CaptainVaga"):
        """Configure domain for GitHub Pages"""
        if not self.headers:
            print("No GoDaddy credentials")
            return False

        # GitHub Pages IPs
        github_ips = [
            "185.199.108.153",
            "185.199.109.153",
            "185.199.110.153",
            "185.199.111.153"
        ]

        print(f"\n🔧 Setting up {domain} for GitHub Pages...")

        # Create A records for apex domain
        a_records = [{"data": ip, "name": "@", "ttl": 600, "type": "A"} for ip in github_ips]

        # Create CNAME for www
        cname_record = [{
            "data": f"{github_username}.github.io",
            "name": "www",
            "ttl": 600,
            "type": "CNAME"
        }]

        try:
            # Set A records
            response = requests.put(
                f"{self.base_url}/domains/{domain}/records/A/@",
                headers=self.headers,
                json=a_records
            )
            response.raise_for_status()
            print(f"   ✓ A records set (4 GitHub IPs)")

            # Set CNAME for www
            response = requests.put(
                f"{self.base_url}/domains/{domain}/records/CNAME/www",
                headers=self.headers,
                json=cname_record
            )
            response.raise_for_status()
            print(f"   ✓ CNAME www → {github_username}.github.io")

            print(f"\n✅ {domain} configured for GitHub Pages!")
            print(f"   Next: Add '{domain}' in GitHub repo Settings → Pages → Custom domain")
            return True

        except Exception as e:
            print(f"Error setting DNS: {e}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text}")
            return False

    def add_subdomain(self, domain: str, subdomain: str, target: str):
        """Add a subdomain CNAME record"""
        if not self.headers:
            return False

        record = [{
            "data": target,
            "name": subdomain,
            "ttl": 600,
            "type": "CNAME"
        }]

        try:
            response = requests.put(
                f"{self.base_url}/domains/{domain}/records/CNAME/{subdomain}",
                headers=self.headers,
                json=record
            )
            response.raise_for_status()
            print(f"✓ {subdomain}.{domain} → {target}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


def main():
    print("\n" + "="*60)
    print("🌐 WE333 GODADDY DNS MANAGER")
    print("="*60)

    dns = GoDaddyDNS()

    # List all domains
    print("\n📋 Your Domains:")
    print("-"*40)
    domains = dns.list_domains()

    if domains:
        for d in domains:
            status = d.get('status', 'unknown')
            name = d.get('domain', 'unknown')
            expires = d.get('expires', 'N/A')[:10] if d.get('expires') else 'N/A'
            print(f"   • {name} [{status}] (expires: {expires})")
    else:
        print("   No domains found or API error")

    # Show DNS for each domain
    if domains:
        print("\n📊 DNS Records:")
        print("-"*40)
        for d in domains[:3]:  # First 3 domains
            domain = d.get('domain')
            if domain:
                records = dns.get_dns_records(domain)
                print(f"\n   {domain}:")
                for r in records[:5]:  # First 5 records
                    print(f"      {r.get('type'):6} {r.get('name'):15} → {r.get('data')[:40]}")

    print("\n" + "="*60)
    print("💡 To connect a domain to GitHub Pages, run:")
    print("   dns.setup_github_pages('bba.news')")
    print("="*60)


if __name__ == "__main__":
    main()
