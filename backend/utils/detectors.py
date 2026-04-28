"""
Form and interactive element detection for locations pages.
Determines if Playwright automation is needed.
"""
import re
from typing import Dict, Any


class FormDetector:
    """Detect interactive forms and store locators."""
    
    @staticmethod
    def is_interactive_locator(html: str) -> bool:
        """
        Detect if page has an interactive store locator form.
        
        Args:
            html: HTML content of the locations page
        
        Returns:
            True if interactive form detected, False otherwise
        """
        keywords = [
            "enter your zip", "enter zip code", "find nearby",
            "search by location", "enter your address", "select your state",
            r'<input.*type="text".*zip', r'<input.*placeholder=".*zip.*code',
            "store locator", "find a store", "location search",
            r'<input.*name=".*zip', r'<input.*id=".*zip',
            "search for locations", "enter location"
        ]
        
        html_lower = html.lower()
        
        # Check for keyword matches
        for keyword in keywords:
            if re.search(keyword, html_lower):
                return True
        
        return False
    
    @staticmethod
    def detect_form_fields(html: str) -> Dict[str, Any]:
        """
        Detect specific form fields on the page.
        
        Args:
            html: HTML content
        
        Returns:
            Dict with detected form fields and their attributes
        """
        detected_fields = {
            "zip_input": False,
            "address_input": False,
            "city_input": False,
            "state_select": False,
            "search_button": False,
            "submit_button": False
        }
        
        # Detect zip code input
        zip_patterns = [
            r'<input[^>]*(?:name|id|placeholder)[^>]*zip[^>]*>',
            r'<input[^>]*type="text"[^>]*(?:postal|zip)[^>]*>'
        ]
        for pattern in zip_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["zip_input"] = True
                break
        
        # Detect address input
        address_patterns = [
            r'<input[^>]*(?:name|id|placeholder)[^>]*address[^>]*>',
        ]
        for pattern in address_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["address_input"] = True
                break
        
        # Detect city input
        city_patterns = [
            r'<input[^>]*(?:name|id|placeholder)[^>]*city[^>]*>',
        ]
        for pattern in city_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["city_input"] = True
                break
        
        # Detect state select
        state_patterns = [
            r'<select[^>]*(?:name|id)[^>]*state[^>]*>',
        ]
        for pattern in state_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["state_select"] = True
                break
        
        # Detect search button
        search_patterns = [
            r'<button[^>]*(?:search|find)[^>]*>',
            r'<input[^>]*type="submit"[^>]*(?:search|find)[^>]*>'
        ]
        for pattern in search_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["search_button"] = True
                break
        
        # Detect submit button
        submit_patterns = [
            r'<button[^>]*type="submit"[^>]*>',
            r'<input[^>]*type="submit"[^>]*>'
        ]
        for pattern in submit_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected_fields["submit_button"] = True
                break
        
        return detected_fields
    
    @staticmethod
    def get_interaction_strategy(
        html: str,
        has_zip_code: bool = False
    ) -> Dict[str, Any]:
        """
        Determine the best strategy for handling a locations page.
        
        Args:
            html: HTML content of the page
            has_zip_code: Whether user provided a zip code
        
        Returns:
            Dict with strategy recommendation:
            - strategy: "static" | "interactive" | "manual_required"
            - reason: str
            - needs_playwright: bool
        """
        is_interactive = FormDetector.is_interactive_locator(html)
        form_fields = FormDetector.detect_form_fields(html)
        
        # If not interactive, use static scraping
        if not is_interactive:
            return {
                "strategy": "static",
                "reason": "No interactive form detected - use static scraping",
                "needs_playwright": False
            }
        
        # Interactive but no zip provided
        if is_interactive and not has_zip_code:
            return {
                "strategy": "manual_required",
                "reason": "Interactive locator detected but no zip code provided",
                "needs_playwright": False
            }
        
        # Interactive with zip - use Playwright
        if is_interactive and has_zip_code:
            return {
                "strategy": "interactive",
                "reason": "Interactive locator detected with zip code - use Playwright automation",
                "needs_playwright": True,
                "form_fields": form_fields
            }
        
        # Fallback
        return {
            "strategy": "static",
            "reason": "Default to static scraping",
            "needs_playwright": False
        }
    
    @staticmethod
    def detect_pagination(html: str) -> Dict[str, Any]:
        """
        Detect if page has pagination for location listings.
        
        Args:
            html: HTML content
        
        Returns:
            Dict with pagination detection results
        """
        pagination_indicators = {
            "has_pagination": False,
            "pagination_type": None,
            "indicators": []
        }
        
        # Common pagination patterns
        patterns = {
            "next_button": r'(?:next|>|»|›).*page',
            "page_numbers": r'page\s*\d+',
            "load_more": r'load\s*more|show\s*more',
            "pagination_div": r'<(?:div|nav)[^>]*pagination[^>]*>',
        }
        
        html_lower = html.lower()
        
        for indicator_name, pattern in patterns.items():
            if re.search(pattern, html_lower):
                pagination_indicators["has_pagination"] = True
                pagination_indicators["indicators"].append(indicator_name)
                
                if indicator_name == "load_more":
                    pagination_indicators["pagination_type"] = "infinite_scroll"
                elif indicator_name in ["next_button", "page_numbers", "pagination_div"]:
                    pagination_indicators["pagination_type"] = "traditional"
        
        return pagination_indicators
    
    @staticmethod
    def detect_map_embed(html: str) -> Dict[str, Any]:
        """
        Detect if page uses embedded maps (Google Maps, etc.).
        
        Args:
            html: HTML content
        
        Returns:
            Dict with map detection results
        """
        map_providers = {
            "google_maps": r'maps\.google(?:apis)?\.com|google\.com/maps',
            "mapbox": r'mapbox\.com',
            "leaflet": r'leaflet',
            "openstreetmap": r'openstreetmap'
        }
        
        detected = {
            "has_map": False,
            "providers": []
        }
        
        html_lower = html.lower()
        
        for provider, pattern in map_providers.items():
            if re.search(pattern, html_lower):
                detected["has_map"] = True
                detected["providers"].append(provider)
        
        return detected


# Global detector instance
detector = FormDetector()