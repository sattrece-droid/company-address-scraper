"""
Validation utilities for zip code matching and status code assignment.
Determines the final status of address scraping results.
"""
from typing import List, Dict, Any, Optional
import re


class Validator:
    """Validate scraping results and assign status codes."""
    
    @staticmethod
    def validate_zip_match(
        input_zip: Optional[str],
        scraped_addresses: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Validate if input zip code matches any of the scraped addresses.
        
        Args:
            input_zip: Zip code provided in input (optional)
            scraped_addresses: List of address dicts with zip field
        
        Returns:
            Dict with validation results:
            - matches: bool
            - matching_addresses: List of addresses with matching zip
            - message: str
        """
        if not input_zip:
            return {
                "matches": True,  # No validation needed if no input zip
                "matching_addresses": scraped_addresses,
                "message": "No input zip provided - validation skipped"
            }
        
        if not scraped_addresses:
            return {
                "matches": False,
                "matching_addresses": [],
                "message": "No addresses found to validate"
            }
        
        # Normalize input zip (remove spaces, hyphens, take first 5 digits)
        normalized_input_zip = Validator._normalize_zip(input_zip)
        
        # Find matching addresses
        matching_addresses = []
        for address in scraped_addresses:
            address_zip = address.get("zip", "")
            normalized_address_zip = Validator._normalize_zip(address_zip)
            
            if normalized_address_zip.startswith(normalized_input_zip[:5]):
                matching_addresses.append(address)
        
        matches = len(matching_addresses) > 0
        
        return {
            "matches": matches,
            "matching_addresses": matching_addresses,
            "message": f"Found {len(matching_addresses)} addresses matching zip {input_zip}" if matches 
                      else f"No addresses found matching zip {input_zip}"
        }
    
    @staticmethod
    def _normalize_zip(zip_code: str) -> str:
        """
        Normalize zip code for comparison.
        
        Examples:
            "90210-1234" -> "90210"
            "K1A 0B1" -> "K1A0B1"
            "12345" -> "12345"
        """
        if not zip_code:
            return ""
        
        # Remove spaces and hyphens
        normalized = zip_code.replace(" ", "").replace("-", "")
        
        # For US zips, take first 5 digits
        if normalized.isdigit():
            return normalized[:5]
        
        # For Canadian postal codes, keep format
        return normalized.upper()
    
    @staticmethod
    def assign_status(
        scraped_addresses: List[Dict[str, str]],
        input_zip: Optional[str] = None,
        website_found: bool = True,
        locations_page_found: bool = True,
        is_interactive: bool = False,
        is_blocked: bool = False,
        is_hq_only: bool = False,
        is_cached: bool = False
    ) -> Dict[str, Any]:
        """
        Assign final status code based on scraping results.
        
        Status codes (from README):
        - complete: All locations found and parsed (5+ locations, zip match if provided)
        - partial: Some locations found, possible pagination gaps (1-4 locations)
        - hq_only: No locations page - HQ from Contact/About page
        - manual_required: Interactive locator, no zip provided or extraction failed
        - blocked: Anti-scraping protection prevented access
        - not_found: No website found or wrong company match
        - zip_mismatch: Input zip not found among scraped locations
        
        Returns:
            Dict with status and confidence score
        """
        # Priority 1: Blocking or not found
        if is_blocked:
            return {
                "status": "blocked",
                "confidence": "low",
                "reason": "Anti-scraping protection prevented access"
            }
        
        if not website_found:
            return {
                "status": "not_found",
                "confidence": "low",
                "reason": "No website found for company"
            }
        
        # Priority 2: HQ only
        if is_hq_only:
            return {
                "status": "hq_only",
                "confidence": "medium",
                "reason": "Only headquarters address found (no locations page)"
            }
        
        # Priority 3: Interactive locator without zip
        if is_interactive and not input_zip:
            return {
                "status": "manual_required",
                "confidence": "low",
                "reason": "Interactive store locator detected, but no zip code provided"
            }
        
        # Priority 4: No locations found
        if not scraped_addresses or len(scraped_addresses) == 0:
            if locations_page_found:
                return {
                    "status": "manual_required",
                    "confidence": "low",
                    "reason": "Locations page found but no addresses extracted"
                }
            else:
                return {
                    "status": "not_found",
                    "confidence": "low",
                    "reason": "No locations page found"
                }
        
        # Priority 5: Zip mismatch validation
        if input_zip:
            zip_validation = Validator.validate_zip_match(input_zip, scraped_addresses)
            if not zip_validation["matches"]:
                return {
                    "status": "zip_mismatch",
                    "confidence": "medium",
                    "reason": f"Input zip {input_zip} not found among {len(scraped_addresses)} scraped locations"
                }
        
        # Priority 6: Success cases
        address_count = len(scraped_addresses)
        
        if address_count >= 5:
            return {
                "status": "complete",
                "confidence": "high",
                "reason": f"Successfully scraped {address_count} locations"
            }
        elif address_count >= 1:
            return {
                "status": "partial",
                "confidence": "medium",
                "reason": f"Scraped {address_count} location(s) - may have pagination gaps"
            }
        
        # Fallback
        return {
            "status": "manual_required",
            "confidence": "low",
            "reason": "Unknown status"
        }
    
    @staticmethod
    def validate_address(address: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate individual address completeness.
        
        Returns validation result with completeness score.
        """
        required_fields = ["address", "city"]
        recommended_fields = ["state", "zip", "country"]
        
        # Check required fields
        has_required = all(address.get(field, "").strip() for field in required_fields)
        
        if not has_required:
            return {
                "valid": False,
                "completeness": 0.0,
                "missing_fields": [f for f in required_fields if not address.get(f, "").strip()]
            }
        
        # Calculate completeness score
        all_fields = required_fields + recommended_fields
        filled_fields = sum(1 for f in all_fields if address.get(f, "").strip())
        completeness = filled_fields / len(all_fields)
        
        return {
            "valid": True,
            "completeness": completeness,
            "missing_fields": [f for f in recommended_fields if not address.get(f, "").strip()]
        }
    
    @staticmethod
    def calculate_confidence(
        status: str,
        address_count: int,
        zip_match: bool,
        is_cached: bool
    ) -> str:
        """
        Calculate overall confidence score for results.
        
        Returns: "high", "medium", or "low"
        """
        if status == "complete" and address_count >= 5 and zip_match:
            return "high"
        elif status == "complete" and address_count >= 5:
            return "high"
        elif status == "partial" and address_count >= 2:
            return "medium"
        elif status == "hq_only":
            return "medium"
        else:
            return "low"


# Global validator instance
validator = Validator()