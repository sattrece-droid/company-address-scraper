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
            # Build search query
            if zip_code:
                # Geotargeted search - helps disambiguate chains and franchises
                query = f'"{company_name}" {zip_code}'
            else:
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
                query = f'site:{clean_website} locations OR offices OR "find a location" OR stores'

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
            location_keywords = ["location", "store", "office", "branch", "find", "near"]

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