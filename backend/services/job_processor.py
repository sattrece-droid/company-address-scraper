"""
Main job orchestrator for processing company address scraping requests.
Chains together all services: cache → search → scrape → parse → validate.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.cache import cache
from services.search import searcher
from services.scraper import scraper
from services.parser import parser
from services.browser import browser
from utils.validators import validator
from utils.detectors import detector
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobProcessor:
    """Process company address scraping jobs."""
    
    def __init__(self):
        self.cost_tracker = {
            "serpapi_calls": 0,
            "firecrawl_calls": 0,
            "playwright_calls": 0,
            "bedrock_input_tokens": 0,
            "bedrock_output_tokens": 0
        }
    
    async def process_company(
        self,
        company_name: str,
        zip_code: Optional[str] = None,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single company through the full pipeline.
        
        Args:
            company_name: Name of the company
            zip_code: Optional zip code for geotargeting and validation
            website: Optional website URL (skips search if provided)
        
        Returns:
            Dict with processing results including addresses and status
        """
        logger.info(f"Processing: {company_name} (zip: {zip_code or 'N/A'})")
        
        result = {
            "company_name": company_name,
            "input_zip_code": zip_code,
            "addresses": [],
            "status": "unknown",
            "confidence": "low",
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Step 1: Check cache
            cached_result = cache.get(company_name, zip_code)
            if cached_result:
                logger.info(f"Cache hit for {company_name}")
                result.update(cached_result.get("result", {}))
                result["cached"] = True
                return result
            
            # Step 2: Find website (if not provided)
            if website:
                logger.info(f"Using provided website: {website}")
                company_website = website
            else:
                logger.info(f"Searching for website: {company_name}")
                search_result = searcher.find_company_website(company_name, zip_code)
                self.cost_tracker["serpapi_calls"] += 1
                
                if not search_result.get("success"):
                    result.update(validator.assign_status(
                        [], website_found=False
                    ))
                    cache.set(company_name, result, result["status"], zip_code, None)
                    return result
                
                company_website = search_result.get("website")
            
            result["website"] = company_website
            
            # Step 3: Scrape homepage
            logger.info(f"Scraping homepage: {company_website}")
            homepage_result = scraper.scrape_page(company_website)
            self.cost_tracker["firecrawl_calls"] += 1
            
            if not homepage_result.get("success"):
                result.update(validator.assign_status(
                    [], website_found=True, locations_page_found=False
                ))
                cache.set(company_name, result, result["status"], zip_code, company_website)
                return result
            
            # Step 4: Find locations page URL
            logger.info(f"Finding locations page for: {company_name}")
            
            # Try scraper's pattern matching first
            locations_url = scraper.find_locations_page_url(
                homepage_result.get("html", ""),
                company_website
            )
            
            # Fallback to AI extraction if pattern matching fails
            if not locations_url:
                locations_url = parser.extract_locations_page_url(
                    homepage_result.get("html", "")[:10000],
                    company_website
                )
            
            # Fallback to SerpAPI site search
            if not locations_url:
                logger.info(f"Trying SerpAPI site search for locations page")
                search_result = searcher.find_locations_page(company_website)
                self.cost_tracker["serpapi_calls"] += 1
                
                if search_result.get("success"):
                    locations_url = search_result.get("url")
            
            # If still no locations page, try contact/about page
            if not locations_url:
                logger.warning(f"No locations page found for {company_name}")
                # Try to extract HQ from homepage or contact page
                hq_address = scraper.extract_contact_page_address(
                    homepage_result.get("markdown", "")
                )
                
                if hq_address:
                    result["addresses"] = [{"address": hq_address, "city": "", "state": "", "zip": "", "country": "", "name": "Headquarters"}]
                    result.update(validator.assign_status(
                        result["addresses"], input_zip=zip_code, is_hq_only=True
                    ))
                else:
                    result.update(validator.assign_status(
                        [], website_found=True, locations_page_found=False
                    ))
                
                cache.set(company_name, result, result["status"], zip_code, company_website)
                return result
            
            logger.info(f"Found locations page: {locations_url}")
            
            # Step 5: Scrape locations page
            logger.info(f"Scraping locations page: {locations_url}")
            locations_result = scraper.scrape_page(locations_url)
            self.cost_tracker["firecrawl_calls"] += 1
            
            if not locations_result.get("success"):
                result.update(validator.assign_status(
                    [], website_found=True, locations_page_found=True
                ))
                cache.set(company_name, result, result["status"], zip_code, company_website)
                return result
            
            locations_html = locations_result.get("html", "")
            
            # Step 6: Detect if interactive form
            strategy = detector.get_interaction_strategy(
                locations_html,
                has_zip_code=bool(zip_code)
            )
            
            logger.info(f"Interaction strategy: {strategy.get('strategy')}")
            
            # Step 7: Handle interactive vs static scraping
            if strategy.get("needs_playwright") and zip_code:
                # Use Playwright to fill form and get results
                logger.info(f"Using Playwright for interactive locator")
                playwright_result = await browser.scrape_with_playwright(
                    locations_url, zip_code
                )
                self.cost_tracker["playwright_calls"] += 1

                if not playwright_result.get("success"):
                    logger.warning(f"Playwright failed: {playwright_result.get('error')}")
                    result.update(validator.assign_status(
                        [], input_zip=zip_code, is_interactive=True
                    ))
                    cache.set(company_name, result, result["status"], zip_code, company_website)
                    return result

                # Parse addresses from Playwright-extracted HTML
                playwright_html = playwright_result.get("html", "")
                parse_result = parser.parse_addresses(playwright_html)

                if not parse_result.get("success") or parse_result.get("count", 0) == 0:
                    logger.warning(f"Address parsing failed after Playwright, trying fallback")
                    parse_result = parser.parse_addresses(playwright_html, use_fallback=True)

                addresses = parse_result.get("addresses", [])
                result["addresses"] = addresses

                logger.info(f"Parsed {len(addresses)} addresses from Playwright results")

                # Validate and assign status
                status_result = validator.assign_status(
                    addresses,
                    input_zip=zip_code,
                    website_found=True,
                    locations_page_found=True,
                    is_interactive=False,  # Successfully handled the interactive part
                    is_blocked=False,
                    is_hq_only=False
                )

                result.update(status_result)
                cache.set(company_name, result, result["status"], zip_code, company_website)
                return result
            
            elif strategy.get("strategy") == "manual_required":
                result.update(validator.assign_status(
                    [], input_zip=zip_code, is_interactive=True
                ))
                cache.set(company_name, result, result["status"], zip_code, company_website)
                return result
            
            # Step 8: Check for pagination
            pagination_info = detector.detect_pagination(locations_html)

            all_pages_content = locations_result.get("markdown", locations_html)

            if pagination_info.get("has_pagination"):
                logger.info(f"Pagination detected: {pagination_info.get('pagination_type')}")

                # Scrape additional pages
                additional_pages = scraper.scrape_multiple_pages(
                    company_website,
                    path_pattern="/locations/",
                    max_pages=10
                )

                # Combine content from all pages for parsing
                if additional_pages:
                    logger.info(f"Scraped {len(additional_pages)} additional pages")
                    for page_result in additional_pages:
                        if page_result.get("success"):
                            all_pages_content += "\n\n" + page_result.get("markdown", page_result.get("html", ""))
                        self.cost_tracker["firecrawl_calls"] += 1

            # Step 9: Parse addresses from combined content
            logger.info(f"Parsing addresses from locations page(s)")

            parse_result = parser.parse_addresses(all_pages_content)

            if not parse_result.get("success") or parse_result.get("count", 0) == 0:
                # Try with fallback model (Claude Haiku)
                logger.warning(f"Nova Micro failed, trying Claude Haiku fallback")
                parse_result = parser.parse_addresses(all_pages_content, use_fallback=True)

            addresses = parse_result.get("addresses", [])
            result["addresses"] = addresses
            
            logger.info(f"Parsed {len(addresses)} addresses")

            # Step 10: Validate and assign status
            status_result = validator.assign_status(
                addresses,
                input_zip=zip_code,
                website_found=True,
                locations_page_found=True,
                is_interactive=False,
                is_blocked=False,
                is_hq_only=False
            )
            
            result.update(status_result)

            # Step 11: Cache result
            cache.set(company_name, result, result["status"], zip_code, company_website)
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing {company_name}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
            return result
    
    async def process_batch(
        self,
        companies: List[Dict[str, Optional[str]]],
        job_id: str
    ) -> Dict[str, Any]:
        """
        Process a batch of companies.
        
        Args:
            companies: List of dicts with company_name, zip_code, website
            job_id: Unique job identifier
        
        Returns:
            Dict with batch results and statistics
        """
        logger.info(f"Processing batch job {job_id} with {len(companies)} companies")
        
        results = []
        
        # Process companies sequentially (parallel processing in production)
        for company in companies:
            result = await self.process_company(
                company.get("company_name"),
                company.get("zip_code"),
                company.get("website")
            )
            results.append(result)
        
        # Calculate statistics
        stats = self._calculate_statistics(results)
        
        return {
            "job_id": job_id,
            "status": "completed",
            "companies_processed": len(companies),
            "results": results,
            "statistics": stats,
            "cost_tracker": self.cost_tracker,
            "completed_at": datetime.now().isoformat()
        }
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from batch results."""
        total = len(results)
        
        status_counts = {}
        for result in results:
            status = result.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        cached_count = sum(1 for r in results if r.get("cached", False))
        total_addresses = sum(len(r.get("addresses", [])) for r in results)
        
        return {
            "total_companies": total,
            "status_breakdown": status_counts,
            "cached_results": cached_count,
            "total_addresses_found": total_addresses,
            "average_addresses_per_company": total_addresses / total if total > 0 else 0
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get estimated costs for the job."""
        # Estimated costs per call (from README)
        serpapi_cost_per_call = 0.025
        firecrawl_cost_per_call = 0.005
        playwright_cost_per_call = 0  # Self-hosted
        
        return {
            "serpapi_calls": self.cost_tracker["serpapi_calls"],
            "serpapi_cost": self.cost_tracker["serpapi_calls"] * serpapi_cost_per_call,
            "firecrawl_calls": self.cost_tracker["firecrawl_calls"],
            "firecrawl_cost": self.cost_tracker["firecrawl_calls"] * firecrawl_cost_per_call,
            "playwright_calls": self.cost_tracker["playwright_calls"],
            "total_estimated_cost": (
                self.cost_tracker["serpapi_calls"] * serpapi_cost_per_call +
                self.cost_tracker["firecrawl_calls"] * firecrawl_cost_per_call
            )
        }


# Global processor instance
processor = JobProcessor()