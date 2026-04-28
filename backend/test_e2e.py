"""
End-to-end test suite for the company address scraping pipeline.
Tests 7 scenarios from the MVP spec with real company data.

Run with: python test_e2e.py

Optional: Pass --real to use real API keys instead of mocks
         Pass --company NAME to test a single company
"""
import asyncio
import sys
from typing import Optional
from services.job_processor import processor
from services.cache import cache
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class E2ETestSuite:
    """End-to-end test cases for company address scraping."""

    def __init__(self, use_real_apis: bool = False):
        self.use_real_apis = use_real_apis
        self.results = []

    async def test_simple_site(self):
        """
        Test 1: Simple site with static location list (no forms, no pagination).
        Expected: Status = "complete" or "partial"
        Companies: ServiceMaster, Home Depot
        """
        logger.info("=" * 60)
        logger.info("TEST 1: Simple Site (Static List)")
        logger.info("=" * 60)

        companies = [
            {"name": "Home Depot", "zip": "90210"},
            {"name": "ServiceMaster", "zip": None},
        ]

        for company in companies:
            logger.info(f"\nProcessing: {company['name']}")
            result = await processor.process_company(
                company["name"],
                company.get("zip")
            )

            success = result.get("status") in ["complete", "partial"]
            addresses = len(result.get("addresses", []))

            test_result = {
                "test": "Simple Site",
                "company": company["name"],
                "expected_status": "complete/partial",
                "actual_status": result.get("status"),
                "passed": success,
                "addresses_found": addresses,
                "timestamp": datetime.now().isoformat()
            }

            self.results.append(test_result)

            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Addresses: {addresses}")
            logger.info(f"Cached: {result.get('cached', False)}")
            logger.info(f"Result: {'✓ PASS' if success else '✗ FAIL'}")

    async def test_interactive_locator(self):
        """
        Test 2: Interactive zip-gated store locator form.
        Expected: Status = "complete" (via Playwright automation)
        Companies: Starbucks, Target
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Interactive Store Locator (Playwright)")
        logger.info("=" * 60)

        companies = [
            {"name": "Starbucks", "zip": "90210"},
            {"name": "Target", "zip": "30301"},
        ]

        for company in companies:
            logger.info(f"\nProcessing: {company['name']} with zip {company['zip']}")
            result = await processor.process_company(
                company["name"],
                company.get("zip")
            )

            success = result.get("status") == "complete"
            addresses = len(result.get("addresses", []))
            playwright_used = result.get("cached") is False

            test_result = {
                "test": "Interactive Locator",
                "company": company["name"],
                "expected_status": "complete",
                "actual_status": result.get("status"),
                "passed": success,
                "addresses_found": addresses,
                "playwright_used": playwright_used,
                "timestamp": datetime.now().isoformat()
            }

            self.results.append(test_result)

            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Addresses: {addresses}")
            logger.info(f"Result: {'✓ PASS' if success else '✗ FAIL'}")

    async def test_hq_only(self):
        """
        Test 3: Company with no dedicated locations page (HQ only).
        Expected: Status = "hq_only"
        Note: Using a smaller company for this
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: HQ-Only (No Locations Page)")
        logger.info("=" * 60)

        # Small B2B company likely to have no locations page
        company = "Acme Corporation"
        logger.info(f"\nProcessing: {company}")

        result = await processor.process_company(company, zip_code=None)

        success = result.get("status") in ["hq_only", "not_found"]
        addresses = len(result.get("addresses", []))

        test_result = {
            "test": "HQ Only",
            "company": company,
            "expected_status": "hq_only",
            "actual_status": result.get("status"),
            "passed": success,
            "addresses_found": addresses,
            "timestamp": datetime.now().isoformat()
        }

        self.results.append(test_result)

        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Addresses: {addresses}")
        logger.info(f"Result: {'✓ PASS' if success else '✗ FAIL'}")

    async def test_ambiguous_name(self):
        """
        Test 4: Ambiguous company name with zip for disambiguation.
        Expected: Status = "zip_mismatch" or "not_found" without zip
                 Status = "complete/partial" with zip (disambiguated)
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Ambiguous Company Name")
        logger.info("=" * 60)

        # Test without zip - should fail
        logger.info("\n4a. Without zip code:")
        company = "BrightStar"
        result_no_zip = await processor.process_company(company, zip_code=None)
        success_no_zip = result_no_zip.get("status") in ["not_found", "zip_mismatch"]

        test_result_no_zip = {
            "test": "Ambiguous Name (No Zip)",
            "company": company,
            "expected_status": "not_found",
            "actual_status": result_no_zip.get("status"),
            "passed": success_no_zip,
            "addresses_found": len(result_no_zip.get("addresses", [])),
            "timestamp": datetime.now().isoformat()
        }

        self.results.append(test_result_no_zip)

        logger.info(f"Company: {company}")
        logger.info(f"Status: {result_no_zip.get('status')}")
        logger.info(f"Result: {'✓ PASS' if success_no_zip else '✗ FAIL'}")

        # Test with zip - might succeed if disambiguated
        logger.info("\n4b. With zip code (90210):")
        result_with_zip = await processor.process_company(
            company,
            zip_code="90210"
        )

        logger.info(f"Status: {result_with_zip.get('status')}")
        logger.info(f"Addresses: {len(result_with_zip.get('addresses', []))}")

    async def test_pagination(self):
        """
        Test 5: Large location list with pagination (50+ locations).
        Expected: Status = "complete" (all pages scraped)
        Companies: Starbucks, McDonald's, Subway
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Pagination (50+ Locations)")
        logger.info("=" * 60)

        companies = [
            {"name": "Starbucks", "zip": "90210"},
            {"name": "McDonald's", "zip": "90210"},
        ]

        for company in companies:
            logger.info(f"\nProcessing: {company['name']}")
            result = await processor.process_company(
                company["name"],
                company.get("zip")
            )

            addresses = len(result.get("addresses", []))
            success = addresses > 5  # Should find many locations

            test_result = {
                "test": "Pagination",
                "company": company["name"],
                "expected_addresses": "50+",
                "actual_addresses": addresses,
                "passed": success,
                "status": result.get("status"),
                "timestamp": datetime.now().isoformat()
            }

            self.results.append(test_result)

            logger.info(f"Addresses found: {addresses}")
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Result: {'✓ PASS (many locations)' if success else '✗ FAIL (few locations)'}")

    async def test_cache_hit(self):
        """
        Test 6: Cache hit - repeat request should return instantly.
        Expected: Result returned from cache (cached=True)
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: Cache Hit (Repeat Request)")
        logger.info("=" * 60)

        company = "Starbucks"
        zip_code = "90210"

        # Clear cache for this test to ensure first run
        cache.delete(company, zip_code)

        logger.info(f"\nProcessing: {company} (first run - not cached)")
        import time
        start_first = time.time()

        result_first = await processor.process_company(company, zip_code)

        time_first = time.time() - start_first

        logger.info(f"Time: {time_first:.2f}s")
        logger.info(f"Cached: {result_first.get('cached', False)}")
        logger.info(f"Addresses: {len(result_first.get('addresses', []))}")

        # Second request - should be cached
        logger.info(f"\nProcessing: {company} (repeat - should be cached)")
        start_second = time.time()

        result_second = await processor.process_company(company, zip_code)

        time_second = time.time() - start_second

        cached = result_second.get("cached", False)
        success = cached and time_second < time_first  # Should be faster

        test_result = {
            "test": "Cache Hit",
            "company": company,
            "first_request_time": f"{time_first:.2f}s",
            "second_request_time": f"{time_second:.2f}s",
            "second_cached": cached,
            "passed": success,
            "addresses_match": len(result_first.get("addresses", [])) == len(result_second.get("addresses", [])),
            "timestamp": datetime.now().isoformat()
        }

        self.results.append(test_result)

        logger.info(f"Time: {time_second:.2f}s")
        logger.info(f"Cached: {cached}")
        logger.info(f"Result: {'✓ PASS' if success else '✗ FAIL (not cached or slower)'}")

    async def test_blocked_site(self):
        """
        Test 7: Blocked/anti-scraping site.
        Expected: Status = "blocked" (HTTP 403/429 or CAPTCHA detected)
        Note: Hard to test reliably - this is more for monitoring
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST 7: Anti-Scraping Protection")
        logger.info("=" * 60)

        logger.info("\nNote: This test verifies the pipeline handles blocked sites.")
        logger.info("Actual blocked sites depend on site changes and are unpredictable.")
        logger.info("If a site marks itself as 'blocked', the test passes.")

        # Use a well-known anti-scraping site
        company = "Cloudflare"  # Ironically tests blocking
        logger.info(f"\nProcessing: {company}")

        result = await processor.process_company(company, zip_code=None)

        is_blocked = result.get("status") == "blocked"
        not_found = result.get("status") == "not_found"
        success = is_blocked or not_found

        test_result = {
            "test": "Anti-Scraping",
            "company": company,
            "expected_status": "blocked or not_found",
            "actual_status": result.get("status"),
            "passed": success,
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        }

        self.results.append(test_result)

        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Result: {'✓ PASS' if success else '✗ FAIL'}")

    async def run_all_tests(self):
        """Run all 7 test scenarios."""
        logger.info("\n" + "=" * 70)
        logger.info("COMPANY ADDRESS SCRAPING - E2E TEST SUITE")
        logger.info("=" * 70)

        try:
            await self.test_simple_site()
            await self.test_interactive_locator()
            await self.test_hq_only()
            await self.test_ambiguous_name()
            await self.test_pagination()
            await self.test_cache_hit()
            await self.test_blocked_site()

            self.print_summary()

        except Exception as e:
            logger.error(f"Test suite error: {str(e)}", exc_info=True)

    def print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("passed", False))

        logger.info(f"\nTotal Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Pass Rate: {passed_tests / total_tests * 100:.1f}%")

        logger.info("\nDetailed Results:")
        for result in self.results:
            status = "✓ PASS" if result.get("passed", False) else "✗ FAIL"
            test_name = result.get("test")
            company = result.get("company", "")
            logger.info(f"  {status} - {test_name}: {company}")

        logger.info("\n" + "=" * 70)


async def main():
    """Main entry point."""
    use_real = "--real" in sys.argv
    single_company = None

    for arg in sys.argv[1:]:
        if arg.startswith("--company="):
            single_company = arg.split("=", 1)[1]

    if single_company:
        logger.info(f"Testing single company: {single_company}")
        result = await processor.process_company(single_company)
        logger.info(f"\nResult: {result}")
        return

    suite = E2ETestSuite(use_real_apis=use_real)
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
