"""
Mock test script to verify the JobProcessor orchestration logic.
Mocks external API calls to avoid dependency on real API keys for logic testing.
"""
import asyncio
from unittest.mock import MagicMock, patch
from services.job_processor import processor
import json

async def test_mock_pipeline():
    print("Starting mock pipeline test...")
    
    # Mock data
    mock_company = "Test Company"
    mock_zip = "90210"
    mock_website = "https://testcompany.com"
    mock_locations_url = "https://testcompany.com/locations"
    
    # Mock addresses
    mock_addresses = [
        {"name": "Location 1", "address": "123 Main St", "city": "Beverly Hills", "state": "CA", "zip": "90210", "country": "US"},
        {"name": "Location 2", "address": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90001", "country": "US"}
    ]

    # Patch services
    with patch("services.search.searcher.find_company_website") as mock_search, \
         patch("services.scraper.scraper.scrape_page") as mock_scrape, \
         patch("services.parser.parser.parse_addresses") as mock_parse, \
         patch("services.cache.cache.get", return_value=None), \
         patch("services.cache.cache.set"):
        
        # Configure mocks
        mock_search.return_value = {"success": True, "website": mock_website}
        
        # Mock scrape results
        mock_scrape.side_effect = [
            {"success": True, "html": "<html>Homepage</html>", "markdown": "Homepage", "url": mock_website}, # Homepage
            {"success": True, "html": "<html>Locations</html>", "markdown": "Locations", "url": mock_locations_url} # Locations page
        ]
        
        # Mock parser
        mock_parse.return_value = {"success": True, "addresses": mock_addresses, "count": 2}
        
        # Mock locations URL detection
        with patch("services.scraper.scraper.find_locations_page_url", return_value=mock_locations_url):
            
            # Run processor
            result = await processor.process_company(mock_company, mock_zip)
            
            # Verify results
            print("\nTest Result Summary:")
            print(f"Company: {result['company_name']}")
            print(f"Status: {result['status']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Addresses Found: {len(result['addresses'])}")
            
            assert result["status"] == "partial" # 2 locations < 5
            assert len(result["addresses"]) == 2
            assert result["website"] == mock_website
            
            print("\nPipeline logic verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_mock_pipeline())
