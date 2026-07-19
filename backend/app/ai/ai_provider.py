import re
import json
import logging
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Regular expressions for data scrubbing
PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "jwt": re.compile(r"eyJ[a-zA-Z0-9-_=]+\.eyJ[a-zA-Z0-9-_=]+\.[a-zA-Z0-9-_=]*"),
    "api_key": re.compile(r"(?i)(key|secret|token|password|passwd|auth|credential|auth_token|api_key|client_secret)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.\/+=@]{8,128})['\"]?"),
}

def redact_text(text: str) -> str:
    """
    Masks PII, passwords, API keys, and JWT tokens in requests or file content.
    """
    if not text:
        return text

    # Redact JWTs
    text = PATTERNS["jwt"].sub("[REDACTED_JWT]", text)
    
    # Redact Credit Cards
    text = PATTERNS["credit_card"].sub("[REDACTED_CARD]", text)

    # Redact Emails
    text = PATTERNS["email"].sub("[REDACTED_EMAIL]", text)

    # Redact keys/passwords/secrets
    def key_replacer(match):
        key_group = match.group(1)
        val_group = match.group(2)
        # Keep the key identifier but replace the sensitive value
        return match.group(0).replace(val_group, "[REDACTED_SECRET]")

    text = PATTERNS["api_key"].sub(key_replacer, text)
    return text


class AIProvider:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        # Fallback to mock mode if key is missing or is the default baseline placeholder key
        self.is_mocked = not bool(self.api_key) or self.api_key.startswith("AQ.Ab8RN")

        if not self.is_mocked:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"AIProvider initialized with model {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}. Falling back to Mock mode.")
                self.is_mocked = True
        else:
            logger.warning("Gemini API key is empty or placeholder. AIProvider is running in MOCK mode.")

    def analyze_waf_request(self, method: str, path: str, headers: str, query: str, body: str, matched_rules: list) -> dict:
        """
        Asks Gemini to evaluate if a request blocked or flagged by signatures is indeed an attack.
        """
        sanitized_headers = redact_text(headers)
        sanitized_query = redact_text(query)
        sanitized_body = redact_text(body)

        prompt = f"""
You are the AI threat detection module for Web Security Suite Web Application Firewall (WAF).
Analyze the following HTTP request details and classify if this is a malicious attack.

Request Method: {method}
Path: {path}
Headers: {sanitized_headers}
Query Params: {sanitized_query}
Request Body: {sanitized_body}
Matched Signatures: {json.dumps(matched_rules)}

Respond ONLY with a JSON object in this exact format:
{{
  "is_attack": true/false,
  "confidence": 0 to 100,
  "attack_type": "SQL Injection" | "XSS" | "RCE" | "CSRF" | "Path Traversal" | "None",
  "reasoning": "Plain English explanation of why this request is or is not malicious."
}}
"""
        if self.is_mocked:
            # Mock reasoning for tests/demo
            is_attack = len(matched_rules) > 0
            return {
                "is_attack": is_attack,
                "confidence": 85 if is_attack else 10,
                "attack_type": matched_rules[0] if is_attack else "None",
                "reasoning": f"Mock check. Signatures matched: {matched_rules}. Verified request context safely."
            }

        try:
            # Set response MIME type to json to ensure structured response
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            return {
                "is_attack": data.get("is_attack", False),
                "confidence": int(data.get("confidence", 0)),
                "attack_type": data.get("attack_type", "None"),
                "reasoning": data.get("reasoning", "No details provided by Gemini.")
            }
        except Exception as e:
            logger.error(f"Gemini API WAF classification error: {e}")
            return {
                "is_attack": len(matched_rules) > 0,  # Fallback to rules count
                "confidence": 50,
                "attack_type": matched_rules[0] if matched_rules else "None",
                "reasoning": f"Failed to contact Gemini API. Fallback validation: {e}"
            }

    def analyze_vulnerability(self, file_path: str, code_snippet: str, context_before: str, context_after: str, detected_type: str, language: str) -> dict:
        """
        Asks Gemini to analyze a suspicious static code snippet, confirm the vulnerability, and generate remediation fixes.
        """
        prompt = f"""
You are the AI Static Code Vulnerability Scanner for Web Security Suite.
Analyze the following code snippet from file '{file_path}' (written in {language}) that was flagged for containing '{detected_type}'.

Context Before:
{context_before}

Flagged Code:
{code_snippet}

Context After:
{context_after}

Determine if this code actually contains a vulnerability. If yes, generate a remediation fix.
Respond ONLY with a JSON object in this exact format:
{{
  "confirmed": true/false,
  "severity": "Critical" | "High" | "Medium" | "Low",
  "plain_explanation": "A simple, non-jargon, plain-English explanation for a freelance developer or startup owner showing how an attacker could exploit this code.",
  "technical_explanation": "Root cause, OWASP/CWE references, and deep technical details of why this happens.",
  "suggested_fix_before": "Exact snippet of the bad code (matching the flagged code or including necessary lines for the fix)",
  "suggested_fix_after": "The secure, rewritten version of the code that resolves the vulnerability."
}}
"""
        if self.is_mocked:
            # Basic fallback response
            return {
                "confirmed": True,
                "severity": "High",
                "plain_explanation": f"This code uses input in a manner that might allow a {detected_type} attack. This lets an attacker run commands or view files on your server.",
                "technical_explanation": f"Static pattern match for {detected_type} at {file_path}. Input is directly processed without parameterized sanitization.",
                "suggested_fix_before": code_snippet.strip(),
                "suggested_fix_after": f"// Securing code:\n# Sanitize inputs or use parameterized functions instead.\n{code_snippet.strip()}"
            }

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            return {
                "confirmed": data.get("confirmed", False),
                "severity": data.get("severity", "Medium"),
                "plain_explanation": data.get("plain_explanation", ""),
                "technical_explanation": data.get("technical_explanation", ""),
                "suggested_fix_before": data.get("suggested_fix_before", code_snippet),
                "suggested_fix_after": data.get("suggested_fix_after", "")
            }
        except Exception as e:
            logger.error(f"Gemini API static scanner analysis error: {e}")
            return {
                "confirmed": True,
                "severity": "Medium",
                "plain_explanation": f"Could not confirm vulnerability due to AI connection timeout. Please verify manually.",
                "technical_explanation": f"API error: {e}",
                "suggested_fix_before": code_snippet,
                "suggested_fix_after": code_snippet
            }

# Singleton instance
ai_provider = AIProvider()
