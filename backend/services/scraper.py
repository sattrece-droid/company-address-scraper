"""
Firecrawl integration for web scraping with JavaScript rendering support.
Handles homepage crawling and locations page scraping.
"""
from firecrawl import FirecrawlApp
from typing import Optional, Dict, Any, List
from config import settings
import re


class WebScraper:
    """Web scraper using Firecrawl for JavaScript-rendered pages."""
    
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
    
    def scrape_page(
        self,
        url: str,
        formats: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape a single page using Firecrawl.
        
        Args:
            url: URL to scrape
            formats: List of output formats (default: ["markdown", "html"])
        
        Returns:
            Dict with keys:
            - success: bool
            - markdown: str (if requested)
            - html: str (if requested)
            - metadata: dict
            - error: str (if failed)
        """
        try:
            if formats is None:
                formats = ["markdown", "html"]
            
            # Scrape page with Firecrawl
            result = self.firecrawl.scrape_url(
                url,
                params={
                    "formats": formats,
                    "waitFor": 2000,  # Wait 2 seconds for JS to load
                    "timeout": 15000   # 15 second timeout
                }
            )
            
            if not result or not result.get("success"):
                return {
                    "success": False,
                    "error": "Firecrawl scraping failed"
                }
            
            return {
                "success": True,
                "markdown": result.get("markdown", ""),
                "html": result.get("html", ""),
                "metadata": result.get("metadata", {}),
                "url": url
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Firecrawl error: {str(e)}"
            }
    
    def find_locations_page_url(
        self,
        homepage_content: str,
        base_url: str
    ) -> Optional[str]:
        """
        Extract locations page URL from homepage content.
        Looks for common patterns in links.
        
        Args:
            homepage_content: HTML or markdown content from homepage
            base_url: Base URL of the website (for relative links)
        
        Returns:
            URL of locations page if found, None otherwise
        """
        # Common location page patterns
        location_patterns = [
            r'href=["\']([^"\']*(?:location|store|office|branch|find|near)[^"\']*)["\']',
            r'\[([^\]]*)\]\(([^)]*(?:location|store|office|branch|find|near)[^)]*)\)',  # Markdown links
        ]
        
        potential_urls = []
        
        for pattern in location_patterns:
            matches = re.findall(pattern, homepage_content, re.IGNORECASE)
            for match in matches:
                # Handle both HTML and markdown link formats
                url = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                if url:
                    potential_urls.append(url)
        
        if not potential_urls:
            return None
        
        # Filter and score URLs
        scored_urls = []
        for url in potential_urls:
            score = 0
            url_lower = url.lower()
            
            # Prioritize exact matches
            if "locations" in url_lower or "stores" in url_lower:
                score += 10
            if "find" in url_lower or "near" in url_lower:
                score += 5
            if "office" in url_lower or "branch" in url_lower:
                score += 5
            
            # Penalize non-relevant URLs
            if any(x in url_lower for x in ["careers", "news", "blog", "about-us", "contact"]):
                score -= 5
            
            scored_urls.append((score, url))
        
        # Sort by score and return highest
        scored_urls.sort(reverse=True, key=lambda x: x[0])
        
        if scored_urls and scored_urls[0][0] > 0:
            best_url = scored_urls[0][1]
            
            # Make absolute URL if relative
            if best_url.startswith("/"):
                best_url = base_url.rstrip("/") + best_url
            elif not best_url.startswith("http"):
                best_url = base_url.rstrip("/") + "/" + best_url
            
            return best_url
        
        return None
    
    def scrape_multiple_pages(
        self,
        base_url: str,
        path_pattern: str = "/locations/",
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages following a URL pattern.
        Useful for paginated location listings.
        
        Args:
            base_url: Base website URL
            path_pattern: URL path pattern to follow
            max_pages: Maximum number of pages to scrape
        
        Returns:
            List of scraped page results
        """
        results = []
        
        # Common pagination patterns
        pagination_urls = [
            f"{base_url.rstrip('/')}{path_pattern}",
            f"{base_url.rstrip('/')}{path_pattern}page/1",
            f"{base_url.rstrip('/')}{path_pattern}?page=1",
        ]
        
        for i, url in enumerate(pagination_urls[:max_pages]):
            result = self.scrape_page(url)
            if result.get("success"):
                results.append(result)
            else:
                break  # Stop if page fails
        
        return results
    
    def detect_ajax_locator(self, html: str) -> Dict[str, Any]:
        """
        Detect if page uses AJAX/API-based store locator.
        Looks for common patterns like Yext, Bullseye, etc.
        
        Args:
            html: HTML content of the page
        
        Returns:
            Dict with detection results and API endpoints if found
        """
        ajax_indicators = {
            "yext": r'yext\.com|yextcdn\.com',
            "bullseye": r'bullseyelocations\.com',
            "storepoint": r'storepoint\.co',
            "woosmap": r'woosmap\.com',
        }
        
        detected = {}
        
        for provider, pattern in ajax_indicators.items():
            if re.search(pattern, html, re.IGNORECASE):
                detected[provider] = True
        
        # Look for API endpoints
        api_patterns = [
            r'api[^"\']*location[^"\']*',
            r'location[^"\']*api[^"\']*',
            r'store[^"\']*search[^"\']*'
        ]
        
        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            api_endpoints.extend(matches[:5])  # Limit to first 5 matches
        
        return {
            "has_ajax_locator": len(detected) > 0,
            "providers": list(detected.keys()),
            "potential_api_endpoints": api_endpoints[:5]
        }
    
    def extract_contact_page_address(self, content: str) -> Optional[str]:
        """
        Extract headquarters address from Contact/About page.
        Fallback when no dedicated locations page exists.
        
        Args:
            content: Page content (markdown or HTML)
        
        Returns:
            Address string if found
        """
        # Look for address patterns
        # This is a simplified version - the parser service will do more sophisticated extraction
        address_patterns = [
            r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)[,\s]+[\w\s]+,\s*[A-Z]{2}\s+\d{5}',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None


# Global scraper instance
scraper = WebScraper()