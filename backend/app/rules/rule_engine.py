import os
import re
import yaml
import logging

logger = logging.getLogger(__name__)

class WafRule:
    def __init__(self, rule_id, name, category, severity, base_risk_score, pattern_strings):
        self.id = rule_id
        self.name = name
        self.category = category
        self.severity = severity
        self.base_risk_score = base_risk_score
        self.patterns = [re.compile(p) for p in pattern_strings]

class RuleEngine:
    def __init__(self, rules_path=None):
        if not rules_path:
            # Locate default file relative to this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(current_dir, "owasp_rules.yaml")

        self.rules = []
        self.load_rules(rules_path)

    def load_rules(self, path):
        if not os.path.exists(path):
            logger.error(f"OWASP Rules file not found at {path}. Rule engine will be empty.")
            return

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                
            rules_data = data.get("rules", [])
            for r in rules_data:
                rule = WafRule(
                    rule_id=r["id"],
                    name=r["name"],
                    category=r["category"],
                    severity=r["severity"],
                    base_risk_score=r["base_risk_score"],
                    pattern_strings=r["patterns"]
                )
                self.rules.append(rule)
            logger.info(f"Loaded {len(self.rules)} rules from {path}")
        except Exception as e:
            logger.error(f"Failed to parse rule file {path}: {e}")

    def inspect_request(self, method: str, path: str, headers: dict, query: str, body: str) -> dict:
        """
        Scans HTTP request content against the loaded regex rules.
        """
        import urllib.parse
        matched_rules = []
        max_base_score = 0

        # URL-decode inputs to correctly evaluate rules (e.g. handle %20, %3C, etc.)
        decoded_path = urllib.parse.unquote(path or "")
        decoded_query = urllib.parse.unquote(query or "")
        decoded_body = urllib.parse.unquote(body or "")

        # Create combined text payload to match against for query, body, path
        # Headers are checked individually (values only)
        targets = [
            f"METHOD: {method}",
            f"PATH: {decoded_path}",
            f"QUERY: {decoded_query}",
            f"BODY: {decoded_body}"
        ]

        # Add headers to search list
        for k, v in headers.items():
            # Avoid scanning Auth token values to reduce false positives/disclosure
            if k.lower() in ("authorization", "cookie"):
                continue
            targets.append(f"{k}: {v}")

        # Scan rules
        for rule in self.rules:
            matched = False
            for pattern in rule.patterns:
                for target in targets:
                    if pattern.search(target):
                        matched = True
                        break
                if matched:
                    break
            
            if matched:
                matched_rules.append({
                    "id": rule.id,
                    "name": rule.name,
                    "category": rule.category,
                    "severity": rule.severity
                })
                if rule.base_risk_score > max_base_score:
                    max_base_score = rule.base_risk_score

        # Calculate score: max matched score + 10 points for each additional match
        risk_score = 0
        if matched_rules:
            num_matches = len(matched_rules)
            risk_score = max_base_score + (10 * (num_matches - 1))
            risk_score = min(risk_score, 100) # Cap at 100

        return {
            "matched": len(matched_rules) > 0,
            "risk_score": risk_score,
            "rules": matched_rules
        }

# Singleton instance
rule_engine = RuleEngine()
