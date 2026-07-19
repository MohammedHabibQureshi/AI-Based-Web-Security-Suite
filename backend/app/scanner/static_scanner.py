import os
import re
import hashlib
import logging
from sqlalchemy.orm import Session
from app.ai.ai_provider import ai_provider
from app.models.scan import ScanFinding, Scan

logger = logging.getLogger(__name__)

# Basic Regex Rules for static source code auditing
SCAN_RULES = [
    {
        "id": "SEC_HARDCODED_KEY",
        "type": "Hardcoded Secret Key",
        "pattern": re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key|jwt_secret|secret_key|api_key|password|private_key)\s*=\s*['\"]([a-zA-Z0-9_\-\.\/+=@]{12,80})['\"]"),
        "languages": [".py", ".js", ".ts", ".php", ".java", ".json", ".env"],
    },
    {
        "id": "SEC_SQL_CONCAT",
        "type": "SQL Injection Risk",
        "pattern": re.compile(r"(?i)(select\s+.*\s+from\s+.*\s+where\s+.*\s*[\+%=]\s*|\.execute\(\s*f['\"].*?\{.*?\}|\.execute\(\s*['\"].*?\%s.*?['\"]\s*%)"),
        "languages": [".py", ".js", ".ts"],
    },
    {
        "id": "SEC_PHP_SQL_CONCAT",
        "type": "SQL Injection Risk (PHP)",
        "pattern": re.compile(r"(?i)(query\s*\(\s*['\"].*?WHERE\s+.*?=\s*['\"]\s*\.\s*\$)"),
        "languages": [".php"],
    },
    {
        "id": "SEC_XSS_DANGEROUS_HTML",
        "type": "Cross-Site Scripting (XSS) Risk",
        "pattern": re.compile(r"(dangerouslySetInnerHTML|innerHtml\s*=|\.send\(\s*['\"].*?<script>|\.write\(\s*['\"].*?<script>|echo\s+\$_GET|echo\s+\$_POST)"),
        "languages": [".js", ".ts", ".php"],
    },
    {
        "id": "SEC_RCE_EVAL",
        "type": "Remote Code Execution (RCE) Risk",
        "pattern": re.compile(r"(eval\s*\(|exec\s*\(|system\s*\(|shell_exec\s*\(|subprocess\.Popen\(\s*.*,\s*shell\s*=\s*True)"),
        "languages": [".py", ".js", ".ts", ".php", ".java"],
    },
    {
        "id": "SEC_PATH_TRAVERSAL",
        "type": "Path Traversal Risk",
        "pattern": re.compile(r"(fs\.readFile\(\s*\w+|open\(\s*\w+|file_get_contents\(\s*\$)"),
        "languages": [".py", ".js", ".ts", ".php"],
    }
]

class CodeScanner:
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def detect_languages_and_frameworks(self, directory: str) -> dict:
        """
        Scans project files to guess the languages and frameworks in use.
        """
        results = {
            "languages": set(),
            "frameworks": set()
        }

        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext == ".py":
                    results["languages"].add("Python")
                elif ext in (".js", ".ts", ".jsx", ".tsx"):
                    results["languages"].add("JavaScript/TypeScript")
                elif ext == ".php":
                    results["languages"].add("PHP")
                elif ext == ".java":
                    results["languages"].add("Java")

                # Framework detection
                if file == "requirements.txt":
                    results["frameworks"].add("Python Dependecy Manifest")
                elif file == "package.json":
                    results["frameworks"].add("Node.js/Express Project")
                elif file == "composer.json":
                    results["frameworks"].add("PHP Project")
                elif file == "pom.xml":
                    results["frameworks"].add("Java Maven Project")

        # Convert sets to list for JSON response
        results["languages"] = list(results["languages"])
        results["frameworks"] = list(results["frameworks"])
        return results

    def get_file_snippet(self, file_path: str, target_line_idx: int, window: int = 10) -> tuple:
        """
        Extracts the target line, context before, and context after.
        Line numbers are 1-indexed.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return "", "", ""

        total_lines = len(lines)
        target_idx = target_line_idx - 1 # Convert to 0-indexed

        if target_idx < 0 or target_idx >= total_lines:
            return "", "", ""

        start_before = max(0, target_idx - window)
        context_before = "".join(lines[start_before:target_idx])
        
        flagged_line = lines[target_idx]

        start_after = target_idx + 1
        end_after = min(total_lines, start_after + window)
        context_after = "".join(lines[start_after:end_after])

        return flagged_line, context_before, context_after

    def scan_directory(self, scan_id: str, directory: str):
        """
        Performs static analysis on all files inside directory.
        Checks for previous findings to skip redundant AI calls (caching).
        """
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan record {scan_id} not found in database.")
            return

        scan.status = "Running"
        self.db.commit()

        # Step 1: Detect Languages
        meta = self.detect_languages_and_frameworks(directory)
        logger.info(f"Scanning directory {directory}. Metadata: {meta}")

        findings_count = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        # Step 2: Traverse files and match patterns
        for root, _, files in os.walk(directory):
            # Skip common build / package dirs
            if any(folder in root for folder in ("node_modules", ".git", "venv", "__pycache__", "build", "dist")):
                continue

            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                full_path = os.path.join(root, file)
                
                # Check rules
                applicable_rules = [r for r in SCAN_RULES if file_ext in r["languages"]]
                if not applicable_rules:
                    continue

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception as e:
                    logger.error(f"Could not read file {full_path}: {e}")
                    continue

                for line_idx, line_content in enumerate(lines, start=1):
                    for rule in applicable_rules:
                        if rule["pattern"].search(line_content):
                            # Hit! Compute code line hash
                            relative_path = os.path.relpath(full_path, directory)
                            hasher = hashlib.md5()
                            hasher.update(f"{relative_path}:{line_content.strip()}".encode("utf-8"))
                            finding_hash = hasher.hexdigest()

                            # Step 3: Check cache (look for this hash in previous findings for this tenant)
                            prev_finding = self.db.query(ScanFinding).filter(
                                ScanFinding.tenant_id == self.tenant_id,
                                ScanFinding.hash == finding_hash
                            ).first()

                            if (prev_finding and 
                                "API error" not in (prev_finding.technical_explanation or "") and 
                                "AI connection timeout" not in (prev_finding.plain_explanation or "")):
                                logger.info(f"Cache Hit for {relative_path}:{line_idx}. Reusing previous AI response.")
                                new_finding = ScanFinding(
                                    tenant_id=self.tenant_id,
                                    scan_id=scan.id,
                                    file_path=relative_path,
                                    line_number=line_idx,
                                    vulnerability_type=prev_finding.vulnerability_type,
                                    severity=prev_finding.severity,
                                    plain_explanation=prev_finding.plain_explanation,
                                    technical_explanation=prev_finding.technical_explanation,
                                    suggested_fix_before=prev_finding.suggested_fix_before,
                                    suggested_fix_after=prev_finding.suggested_fix_after,
                                    hash=finding_hash
                                )
                                self.db.add(new_finding)
                                findings_count += 1
                                if prev_finding.severity == "Critical": critical_count += 1
                                elif prev_finding.severity == "High": high_count += 1
                                elif prev_finding.severity == "Medium": medium_count += 1
                                else: low_count += 1
                                break # Skip further rule check on this line

                            # Step 4: Cache Miss - Run AI validation
                            flagged, before, after = self.get_file_snippet(full_path, line_idx)
                            if not flagged:
                                continue

                            logger.info(f"AI Check: Requesting analysis for {relative_path}:{line_idx} ({rule['type']})")
                            ai_analysis = ai_provider.analyze_vulnerability(
                                file_path=relative_path,
                                code_snippet=flagged,
                                context_before=before,
                                context_after=after,
                                detected_type=rule["type"],
                                language=meta["languages"][0] if meta["languages"] else "Unknown"
                            )

                            if ai_analysis["confirmed"]:
                                # Store confirmed vulnerability
                                severity = ai_analysis["severity"]
                                new_finding = ScanFinding(
                                    tenant_id=self.tenant_id,
                                    scan_id=scan.id,
                                    file_path=relative_path,
                                    line_number=line_idx,
                                    vulnerability_type=rule["type"],
                                    severity=severity,
                                    plain_explanation=ai_analysis["plain_explanation"],
                                    technical_explanation=ai_analysis["technical_explanation"],
                                    suggested_fix_before=ai_analysis["suggested_fix_before"],
                                    suggested_fix_after=ai_analysis["suggested_fix_after"],
                                    hash=finding_hash
                                )
                                self.db.add(new_finding)
                                findings_count += 1
                                if severity == "Critical": critical_count += 1
                                elif severity == "High": high_count += 1
                                elif severity == "Medium": medium_count += 1
                                else: low_count += 1
                            else:
                                logger.info(f"AI rejected vulnerability for {relative_path}:{line_idx} (False Positive)")
                            
                            # Break to rule check loop (only report one rule per line to avoid duplicates)
                            break

        # Calculate final grade / score
        # A: 0 issues
        # B: 1-3 issues (none High/Critical)
        # C: 4-7 issues (none Critical, max 2 High)
        # D: 8+ issues or 1-2 Critical
        # F: 3+ Critical or 15+ issues
        score = "A"
        if critical_count >= 3 or findings_count >= 15:
            score = "F"
        elif critical_count > 0 or high_count >= 3 or findings_count >= 8:
            score = "D"
        elif high_count > 0 or medium_count >= 3 or findings_count >= 4:
            score = "C"
        elif findings_count > 0:
            score = "B"

        # Update Scan Status
        import datetime
        scan.status = "Completed"
        scan.score = score
        scan.total_findings = findings_count
        scan.completed_at = datetime.datetime.utcnow()
        self.db.commit()
        logger.info(f"Scan {scan_id} finished successfully. Findings: {findings_count}, Grade: {score}")
