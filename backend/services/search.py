"""
Serper integration for finding company websites.
Supports geotargeted search when zip code is provided.
"""
import requests
from typing import Optional, Dict, Any
from config import settings


class WebsiteSearcher:
    """Search for company websites using Serper."""

    def __init__(self):
        self.api_key = settings.serper_api_key
        self.base_url = "https://google.serper.dev/search"
    
    def find_company_website(
        self,
        company_name: str,
        zip_code: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find the official website for a company using Google Search via Serper.

        Args:
            company_name: Name of the company to search for
            zip_code: Optional zip code for geotargeting (improves accuracy for chains)
            country: Optional country code for international companies

        Returns:
            Dict with keys:
            - success: bool
            - website: str (if found)
            - title: str (if found)
            - snippet: str (if found)
            - error: str (if failed)
        """
        try:
            # Always search for the official website, not local results
            query = f'"{company_name}" official website'

            # Serper request payload
            payload = {
                "q": query,
                "num": 3  # Get top 3 results
            }

            # Serper headers
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            # Execute search
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()

            # Extract organic results
            organic_results = results.get("organic", [])

            if not organic_results:
                return {
                    "success": False,
                    "error": "No search results found"
                }

            # First result is usually the official website
            first_result = organic_results[0]

            return {
                "success": True,
                "website": first_result.get("link", ""),
                "title": first_result.get("title", ""),
                "snippet": first_result.get("snippet", ""),
                "displayed_link": first_result.get("link", "").replace("https://", "").replace("http://", "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Serper error: {str(e)}"
            }
    
    def find_locations_page(
        self,
        website: str,
        search_terms: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find the locations/offices page on a specific website.
        Uses site-scoped Google search.

        Args:
            website: Base website URL (e.g., "example.com")
            search_terms: Optional custom search terms

        Returns:
            Dict with success status and URL if found
        """
        try:
            # Clean website URL (remove https://, www., trailing slash)
            clean_website = website.replace("https://", "").replace("http://", "")
            clean_website = clean_website.replace("www.", "").rstrip("/")

            # Build site-scoped search query
            if search_terms:
                query = f"site:{clean_website} {search_terms}"
            else:
                query = f'site:{clean_website} "store locator" OR "find a store" OR locations OR stores OR offices OR "find a location"'

            # Serper request payload
            payload = {
                "q": query,
                "num": 5
            }

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()

            organic_results = results.get("organic", [])

            if not organic_results:
                return {
                    "success": False,
                    "error": "No locations page found via search"
                }

            # Filter for pages likely to be location listings
            location_keywords = ["location", "store", "office", "branch", "find", "near", "locator", "finder"]

            for result in organic_results:
                link = result.get("link", "").lower()
                title = result.get("title", "").lower()

                # Check if URL or title contains location keywords
                if any(keyword in link or keyword in title for keyword in location_keywords):
                    return {
                        "success": True,
                        "url": result.get("link"),
                        "title": result.get("title"),
                        "snippet": result.get("snippet", "")
                    }

            # If no keyword match, return first result
            return {
                "success": True,
                "url": organic_results[0].get("link"),
                "title": organic_results[0].get("title"),
                "snippet": organic_results[0].get("snippet", ""),
                "note": "No exact location page keyword match - using first result"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Serper error: {str(e)}"
            }
    
    def search_local_addresses(
        self,
        company_name: str,
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for company locations using Serper's local results (Google local pack).
        Returns structured address data without needing to scrape any website.

        Args:
            company_name: Company to search for
            zip_code: Optional zip code to geo-target the search

        Returns:
            Dict with success, addresses list, and count
        """
        try:
            if zip_code:
                query = f'{company_name} near {zip_code}'
            else:
                query = f'{company_name} store locations'

            # Use /maps endpoint for structured local results
            maps_url = "https://google.serper.dev/maps"
            payload = {"q": query, "num": 10}
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

            response = requests.post(maps_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            addresses = []

            def parse_address_string(raw: str, name: str) -> dict:
                """Parse '123 Main St, City, ST 12345' into fields."""
                parts = [p.strip() for p in raw.split(",")]
                street = parts[0] if len(parts) > 0 else ""
                city = parts[1] if len(parts) > 1 else ""
                state_zip = parts[2] if len(parts) > 2 else ""
                state, zip_out = "", ""
                if state_zip:
                    tokens = state_zip.strip().split()
                    state = tokens[0] if tokens else ""
                    zip_out = tokens[1] if len(tokens) > 1 else ""
                return {"name": name, "address": street, "city": city, "state": state, "zip": zip_out, "country": "US"}

            # /maps endpoint returns a "places" array
            for item in data.get("places", []):
                title = item.get("title", "").strip()
                raw_address = item.get("address", "").strip()
                if raw_address and any(c.isdigit() for c in raw_address):
                    parsed = parse_address_string(raw_address, title)
                    if parsed["address"] and parsed["city"]:
                        addresses.append(parsed)

            # Fallback: localResults from regular search endpoint
            for item in data.get("localResults", []):
                title = item.get("title", "").strip()
                raw_address = item.get("address", "").strip()
                if raw_address and any(c.isdigit() for c in raw_address):
                    parsed = parse_address_string(raw_address, title)
                    if parsed["address"] and parsed["city"]:
                        addresses.append(parsed)

            return {
                "success": True,
                "addresses": addresses,
                "count": len(addresses)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Local search error: {str(e)}",
                "addresses": [],
                "count": 0
            }

    def find_headquarters(self, company_name: str) -> Dict[str, Any]:
        """
        Find a company's corporate headquarters address.
        Strategy: query Serper Maps for "{company} headquarters" — the top
        result for known companies is the corporate office.
        """
        try:
            payload = {"q": f"{company_name} corporate headquarters", "num": 5}
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
            response = requests.post("https://google.serper.dev/maps", json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get("places", []):
                title = item.get("title", "").strip()
                raw = item.get("address", "").strip()
                if not raw or not any(c.isdigit() for c in raw):
                    continue
                parts = [p.strip() for p in raw.split(",")]
                street = parts[0] if len(parts) > 0 else ""
                city = parts[1] if len(parts) > 1 else ""
                state_zip = parts[2] if len(parts) > 2 else ""
                tokens = state_zip.split() if state_zip else []
                state = tokens[0] if tokens else ""
                zip_out = tokens[1] if len(tokens) > 1 else ""
                return {
                    "success": True,
                    "addresses": [{
                        "name": title or f"{company_name} Headquarters",
                        "address": street, "city": city, "state": state,
                        "zip": zip_out, "country": "US"
                    }],
                    "count": 1,
                    "hq_city": city
                }
            return {"success": False, "addresses": [], "count": 0, "error": "No HQ found"}
        except Exception as e:
            return {"success": False, "addresses": [], "count": 0, "error": str(e)}

    def extract_domain(self, url: str) -> str:
        """
        Extract clean domain from URL.
        
        Examples:
            https://www.example.com/page -> example.com
            http://subdomain.example.com -> subdomain.example.com
        """
        # Remove protocol
        clean = url.replace("https://", "").replace("http://", "")
        
        # Remove www.
        clean = clean.replace("www.", "")
        
        # Take only domain part (before first /)
        clean = clean.split("/")[0]
        
        return clean


# Global searcher instance
searcher = WebsiteSearcher()