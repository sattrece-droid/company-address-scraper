"""
Amazon Bedrock integration for address parsing using Nova Micro.
Extracts structured address data from unstructured HTML/text.
"""
import boto3
import json
from typing import List, Dict, Any, Optional
from config import settings


class AddressParser:
    """Parse addresses from HTML/text using Amazon Bedrock (Nova Micro)."""
    
    def __init__(self):
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_default_region
        )
        self.model_id = settings.bedrock_model_id
        self.fallback_model_id = settings.bedrock_fallback_model_id
    
    def parse_addresses(
        self,
        content: str,
        use_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Extract structured addresses from content using Bedrock.
        
        Args:
            content: HTML or text content containing addresses
            use_fallback: If True, use Claude Haiku instead of Nova Micro
        
        Returns:
            Dict with keys:
            - success: bool
            - addresses: List[Dict] with fields: name, address, city, state, zip, country
            - count: int
            - error: str (if failed)
        """
        try:
            # Truncate content if too long (to manage token costs)
            max_chars = 50000  # Roughly 12k tokens
            if len(content) > max_chars:
                content = content[:max_chars]
            
            # Build prompt
            prompt = self._build_extraction_prompt(content)
            
            # Choose model
            model_id = self.fallback_model_id if use_fallback else self.model_id
            
            # Call Bedrock
            if "nova" in model_id:
                response = self._invoke_nova(prompt, model_id)
            else:
                response = self._invoke_claude(prompt, model_id)
            
            if not response.get("success"):
                return response
            
            # Parse response
            addresses = self._parse_model_response(response.get("content", ""))
            
            return {
                "success": True,
                "addresses": addresses,
                "count": len(addresses),
                "model_used": model_id
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Bedrock parsing error: {str(e)}",
                "addresses": [],
                "count": 0
            }
    
    def _build_extraction_prompt(self, content: str) -> str:
        """Build prompt for address extraction."""
        return f"""Extract REAL physical location addresses from the following content.

A REAL address must include a street number AND a street name (e.g. "123 Main St", "2875 M.L.K. Jr Blvd").

DO NOT include:
- Zip codes alone as the address (e.g. "90210" is NOT an address)
- City/state-only entries with no street
- Search input placeholders, filter UI labels, or "Find a store"-style text
- The literal value "None" or empty/null entries

For each location, extract:
- name: Location/store/office name (if available)
- address: Full street address (must contain a number + street name)
- city: City name
- state: State or province (2-letter code if US/Canada)
- zip: Zip/postal code
- country: Country (2-letter code if clear, or full name)

Return ONLY a valid JSON array of objects. No explanation, no markdown.

Example output:
[
  {{"name": "Main Office", "address": "123 Main St", "city": "New York", "state": "NY", "zip": "10001", "country": "US"}}
]

If no real addresses are found, return: []

Content to analyze:
{content}"""
    
    def _invoke_nova(self, prompt: str, model_id: str) -> Dict[str, Any]:
        """Invoke Amazon Nova model via Bedrock."""
        try:
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 4000,
                    "temperature": 0.2
                }
            })
            
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text from Nova response
            content = response_body.get("output", {}).get("message", {}).get("content", [])
            text = content[0].get("text", "") if content else ""
            
            return {
                "success": True,
                "content": text
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Nova invocation error: {str(e)}"
            }
    
    def _invoke_claude(self, prompt: str, model_id: str) -> Dict[str, Any]:
        """Invoke Claude model via Bedrock (fallback)."""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.2
            })
            
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text from Claude response
            content = response_body.get("content", [])
            text = content[0].get("text", "") if content else ""
            
            return {
                "success": True,
                "content": text
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Claude invocation error: {str(e)}"
            }
    
    @staticmethod
    def _looks_like_street_address(s: str) -> bool:
        """A real street address has a leading/embedded number + a street-type word."""
        if not s or len(s) < 5:
            return False
        import re as _re
        if not _re.search(r"\d", s):
            return False
        street_words = r"(st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|ln|lane|way|ct|court|pkwy|parkway|hwy|highway|pl|place|ter|terrace|cir|circle|sq|square|trl|trail|loop|sr|route|rte)"
        return bool(_re.search(rf"\b{street_words}\b", s, flags=_re.IGNORECASE)) or bool(_re.search(r"\d+\s+[A-Za-z]", s))

    def _parse_model_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse model response into structured address list.
        Handles various response formats and cleans data.
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove opening ```json or ```
                response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text[3:]
                # Remove closing ```
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            addresses = json.loads(response_text)
            
            if not isinstance(addresses, list):
                return []
            
            # Clean and validate each address
            cleaned_addresses = []
            for addr in addresses:
                if not isinstance(addr, dict):
                    continue
                
                def clean(val):
                    s = str(val).strip() if val is not None else ""
                    return "" if s.lower() in ("none", "null", "n/a", "-") else s

                cleaned_addr = {
                    "name": clean(addr.get("name")),
                    "address": clean(addr.get("address")),
                    "city": clean(addr.get("city")),
                    "state": clean(addr.get("state")),
                    "zip": clean(addr.get("zip")),
                    "country": clean(addr.get("country"))
                }
                
                # Drop the address field if it doesn't actually look like a street address
                if cleaned_addr["address"] and not self._looks_like_street_address(cleaned_addr["address"]):
                    cleaned_addr["address"] = ""

                # Include if at least one meaningful field is present
                if any([cleaned_addr["address"], cleaned_addr["city"], cleaned_addr["zip"]]):
                    cleaned_addresses.append(cleaned_addr)
            
            return cleaned_addresses
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty list
            return []
        except Exception:
            return []
    
    def extract_locations_page_url(
        self,
        homepage_content: str,
        base_url: str
    ) -> Optional[str]:
        """
        Use AI to find the locations page URL from homepage content.
        More sophisticated than regex-based approach.
        
        Args:
            homepage_content: Homepage HTML/markdown
            base_url: Base website URL
        
        Returns:
            URL of locations page if found
        """
        try:
            prompt = f"""Find the store locator or locations page URL from this webpage.

Rules:
- Reply with ONLY the URL, nothing else
- No explanation, no markdown, no extra text
- If not found, reply with exactly: NONE

Base URL: {base_url}

Content:
{homepage_content[:5000]}"""

            # Use Nova Micro for this task
            response = self._invoke_nova(prompt, self.model_id)

            if response.get("success"):
                raw = response.get("content", "").strip()

                # Extract first URL-like token from response (handles verbose replies)
                import re
                url_match = re.search(r'https?://[^\s\'"<>]+|/[a-zA-Z0-9/_-]+', raw)
                if url_match:
                    url = url_match.group(0).rstrip(".,)")
                elif raw and raw != "NONE" and not any(c in raw for c in [" ", "\n"]):
                    url = raw
                else:
                    return None

                # Make absolute URL if needed
                if url.startswith("/"):
                    url = base_url.rstrip("/") + url
                elif not url.startswith("http"):
                    url = base_url.rstrip("/") + "/" + url

                return url

            return None
        
        except Exception:
            return None


# Global parser instance
parser = AddressParser()