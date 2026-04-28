"""
Playwright-based browser automation for interactive store locators.
Fills forms, clicks buttons, and extracts resulting HTML.
Uses a semaphore to limit concurrent browsers to 1 (Lightsail 2GB constraint).
"""
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Async Playwright automation for interactive locators."""

    def __init__(self, max_concurrent: int = 1):
        """
        Initialize browser automation with concurrency limit.

        Args:
            max_concurrent: Max concurrent browser instances (1 for Lightsail 2GB)
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def scrape_with_playwright(
        self,
        url: str,
        zip_code: str,
        timeout_ms: int = 20000
    ) -> Dict[str, Any]:
        """
        Automate store locator form filling and scraping.

        Args:
            url: URL of the locations page with interactive form
            zip_code: Zip code to fill in the form
            timeout_ms: Total timeout in milliseconds

        Returns:
            Dict with:
            - success: bool
            - html: str (resulting page HTML)
            - error: str (if failed)
        """
        async with self.semaphore:
            return await self._scrape_internal(url, zip_code, timeout_ms)

    async def _scrape_internal(
        self,
        url: str,
        zip_code: str,
        timeout_ms: int
    ) -> Dict[str, Any]:
        """Internal scraping logic (called within semaphore)."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    logger.info(f"Opening page: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms // 2)

                    # Step 1: Find and fill zip code input
                    zip_filled = await self._fill_zip_input(page, zip_code, timeout_ms // 4)

                    if not zip_filled:
                        logger.warning(f"Could not fill zip code on {url}")
                        return {
                            "success": False,
                            "error": "Could not find or fill zip code input field"
                        }

                    logger.info(f"Filled zip code: {zip_code}")

                    # Step 2: Find and click submit button
                    submit_clicked = await self._click_submit_button(page, timeout_ms // 4)

                    if not submit_clicked:
                        logger.warning(f"Could not click submit button on {url}")
                        return {
                            "success": False,
                            "error": "Could not find or click submit button"
                        }

                    logger.info(f"Clicked submit button")

                    # Step 3: Wait for results to load
                    results_found = await self._wait_for_results(page, timeout_ms // 4)

                    if not results_found:
                        logger.warning(f"Results did not load on {url}")
                        return {
                            "success": False,
                            "error": "Results did not load within timeout"
                        }

                    logger.info(f"Results loaded successfully")

                    # Step 4: Extract HTML
                    html_content = await page.content()

                    return {
                        "success": True,
                        "html": html_content,
                        "url": url
                    }

                finally:
                    await browser.close()

        except PlaywrightTimeoutError as e:
            logger.error(f"Playwright timeout for {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Timeout: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Playwright error for {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Browser error: {str(e)}"
            }

    async def _fill_zip_input(
        self,
        page,
        zip_code: str,
        timeout_ms: int
    ) -> bool:
        """
        Find and fill zip code input field.
        Tries multiple selector strategies.

        Args:
            page: Playwright page object
            zip_code: Zip code to fill
            timeout_ms: Timeout for each attempt

        Returns:
            True if successful, False otherwise
        """
        zip_selectors = [
            # Specific attribute matches
            'input[name*="zip"]',
            'input[id*="zip"]',
            'input[placeholder*="zip"]',
            'input[aria-label*="zip"]',

            # Postal code variants
            'input[name*="postal"]',
            'input[id*="postal"]',
            'input[placeholder*="postal"]',

            # Generic text input (last resort)
            'input[type="text"]',
            'input:not([type])',
        ]

        for selector in zip_selectors:
            try:
                element = page.locator(selector).first

                # Check if element is visible and enabled
                if await element.is_visible(timeout=timeout_ms // len(zip_selectors)):
                    await element.fill(zip_code, timeout=timeout_ms // len(zip_selectors))
                    logger.info(f"Filled zip with selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
                continue

        return False

    async def _click_submit_button(
        self,
        page,
        timeout_ms: int
    ) -> bool:
        """
        Find and click submit/search button.
        Tries multiple selector strategies.

        Args:
            page: Playwright page object
            timeout_ms: Timeout for each attempt

        Returns:
            True if successful, False otherwise
        """
        submit_selectors = [
            # Specific action buttons
            'button:has-text("Search")',
            'button:has-text("Find")',
            'button:has-text("Submit")',
            'button:has-text("Go")',
            'input[type="submit"][value*="Search"]',
            'input[type="submit"][value*="Find"]',

            # Attribute-based
            'button[type="submit"]',
            'input[type="submit"]',
            'button[name*="search"]',
            'button[id*="search"]',
            'button[class*="search"]',
            'button[class*="submit"]',

            # Generic buttons
            'button',
        ]

        for selector in submit_selectors:
            try:
                element = page.locator(selector).first

                # Check if element is visible
                if await element.is_visible(timeout=timeout_ms // len(submit_selectors)):
                    await element.click(timeout=timeout_ms // len(submit_selectors))
                    logger.info(f"Clicked button with selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
                continue

        return False

    async def _wait_for_results(
        self,
        page,
        timeout_ms: int
    ) -> bool:
        """
        Wait for location results to appear on page.
        Tries multiple result indicators.

        Args:
            page: Playwright page object
            timeout_ms: Timeout to wait

        Returns:
            True if results detected, False otherwise
        """
        result_selectors = [
            # Common result container classes
            ".location-result",
            ".store-result",
            ".location-item",
            ".store-item",
            "[class*='result']",
            "[class*='location']",

            # Common markers for location data
            ".address",
            "[class*='address']",
            ".store-address",

            # Table rows or list items
            "tr[class*='location']",
            "li[class*='location']",
            "li[class*='store']",
        ]

        for selector in result_selectors:
            try:
                # Wait for at least one result to appear
                await page.wait_for_selector(selector, timeout=timeout_ms)
                logger.info(f"Results detected with selector: {selector}")
                return True
            except PlaywrightTimeoutError:
                logger.debug(f"No results with selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Wait for selector {selector} failed: {str(e)}")
                continue

        # Fallback: just wait a bit and check for content change
        try:
            await asyncio.sleep(1)
            # Check if page has substantial content
            body_html = await page.locator("body").inner_html()
            if len(body_html) > 500:
                logger.info("Results assumed loaded by content length")
                return True
        except Exception as e:
            logger.debug(f"Content length check failed: {str(e)}")

        return False


# Global browser automation instance
browser = BrowserAutomation(max_concurrent=1)
