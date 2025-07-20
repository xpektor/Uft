# gatekeeper.py
import logging
import re
from typing import Dict, Any, List, Optional


# Assuming TelemetryService is available
# from telemetry_service import TelemetryService


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Gatekeeper:
    """
    Layer 3.3.6: Gatekeeper.
    Responsible for security and structural validation of newly generated or modified modules,
    code snippets, or propositions. It operates after Layer 1's ethical veto, ensuring
    code integrity, adherence to structural standards, and absence of malicious patterns.
    """
    def __init__(self, telemetry_service: Any):
        self.telemetry = telemetry_service
        # Define security patterns and structural rules
        self.security_phrase_maps: Dict[str, List[str]] = {
            "prohibited_keywords": [
                "os.system", "eval(", "exec(", "pickle.load", "subprocess.run",
                "shutil.rmtree", "rm -rf",
                "import socket", "socket.connect", "socket.bind",
                "while True:", "for _ in range(infinity)",
                "sys.exit(", "raise SystemExit",
                "__import__",
                "ctypes",
                "threading.Thread", "multiprocessing.Process"
            ],
            "prohibited_regex_patterns": [
                (r"^\s*import\s+os\s*$", "critical"), # Flag severity levels per regex hit
                (r"^\s*import\s+sys\s*$", "critical"),
                (r"^\s*import\s+subprocess\s*$", "critical"),
                (r"^\s*import\s+shutil\s*$", "critical"),
                (r"^\s*import\s+socket\s*$", "critical"),
                (r"file\.write\(.*?\)", "high"), # Suspicious file writes
                (r"requests\.(get|post|put|delete)\(.*?\)", "medium"), # Uncontrolled HTTP requests
                (r"exec\(.*?\)", "critical"),
                (r"eval\(.*?\)", "critical"),
                (r"pickle\.loads\(.*?\)", "critical"),
                (r"^\s*while\s+True\s*:\s*$", "high"), # Simple infinite loop
                (r"^\s*for\s+_\s+in\s+range\s*\(\s*(?:float\('inf'\)|1e9)\s*\)\s*:\s*$", "high"),
                (r"^\s*import\s+[^;]*?;\s*os\.system\(", "critical"),
                (r"^\s*def\s+malicious_function\s*\(", "critical"),
                (r"^\s*class\s+EvilClass\s*\(", "critical"),
                (r"^\s*with\s+open\(.*?,\s*['\"]w['\"]", "high"),
                (r"^\s*try\s*:\s*.*?except\s+Exception\s+as\s+e:\s*pass", "medium"), # Overly broad exception handling
                (r"^\s*print\(.*?password.*?\)", "medium"), # Logging sensitive info
                (r"^\s*input\(.*?\)", "medium"), # Blocking input
                (r"^\s*time\.sleep\(\s*(?:[1-9]\d{2,}|[1-9]\d{3,})\s*\)", "medium"), # Long delays
            ]
        }
        self.structural_rules: Dict[str, Any] = {
            "max_lines": 500,
            "max_functions": 20,
            "required_docstrings": True,
            "allowed_imports_regex": [
                r"^logging$", r"^typing$", r"^numpy$", r"^asyncio$", r"^fastapi$",
                r"^os$", r"^json$", r"^time$", r"^re$", r"^hashlib$",
                r"^uvicorn$", r"^httpx$", r"^aiohttp$",
                r"^PIL$", r"^cv2$", r"^pyserial$", r"^smbus$",
                r"^transformers$", r"^torch$", r"^ollama$",
                r"^telemetry_service$", r"^lineage_hasher$", r"^belief_evolution_graph$",
                r"^abstracted_trait_vectorizer$", r"^dvm_backend$", r"^external_llm_ledger$",
                r"^gemini_api_client$", r"^geminisccmgenerator$", r"^layer1_enforcer$",
                r"^layer4_llm_client$", r"^layer4_routing_daemon$", r"^memory_compressor$",
                r"^memory_compressor_daemon$", r"^module_loader$", r"^paradox_seeder$",
                r"^semantic_divergence_analyzer$", r"^trait_ancestry_ledger$",
                r"^trait_conflict_resolver$", r"^trait_heatmap_dashboard$",
                r"^trait_mutator_daemon$", r"^truth_drift_scanner$", r"^agi_file_system$",
                r"^uvicorn$" # Added uvicorn for clarity
            ]
        }
        logger.info("Gatekeeper initialized with security and structural rules.")


    def validate_module(self, module_code: str, module_name: str, module_type: str = "python_code") -> Dict[str, Any]:
        """
        Validates a module's code for security vulnerabilities and structural integrity.
        Returns a validation report.
        """
        report = {
            "module_name": module_name,
            "module_type": module_type,
            "validation_status": "approved",
            "issues": []
        }
        logger.info(f"Gatekeeper: Validating module '{module_name}' ({module_type}).")


        # Perform security checks
        self._check_security_patterns(module_code, report)


        # Perform structural checks (if it's code)
        if module_type == "python_code":
            self._check_structural_rules(module_code, report)


        if report["issues"]:
            report["validation_status"] = "rejected"
            self.telemetry.add_diary_entry(
                "Gatekeeper_Validation_Rejected",
                f"Module '{module_name}' rejected by Gatekeeper. Issues found.",
                report,
                contributor="Gatekeeper",
                severity="critical"
            )
            logger.warning(f"Gatekeeper: Module '{module_name}' rejected. Issues: {report['issues']}")
        else:
            self.telemetry.add_diary_entry(
                "Gatekeeper_Validation_Approved",
                f"Module '{module_name}' approved by Gatekeeper. No issues found.",
                report,
                contributor="Gatekeeper",
                severity="low"
            )
            logger.info(f"Gatekeeper: Module '{module_name}' approved.")


        return report


    def _check_security_patterns(self, code: str, report: Dict[str, Any]):
        """Checks code against prohibited keywords and regex patterns."""
        code_lower = code.lower()


        # Check prohibited keywords
        for keyword in self.security_phrase_maps["prohibited_keywords"]:
            if keyword.lower() in code_lower:
                report["issues"].append({
                    "type": "Security_Violation",
                    "description": f"Prohibited keyword found: '{keyword}'",
                    "severity": "critical"
                })


        # Flag severity levels per regex hit
        for pattern, severity_level in self.security_phrase_maps["prohibited_regex_patterns"]:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                report["issues"].append({
                    "type": "Security_Violation",
                    "description": f"Prohibited regex pattern found: '{pattern}'",
                    "severity": severity_level
                })


        # Check for unauthorized imports
        import_statements = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)", code, re.MULTILINE)
        all_imports = set(import_statements)


        for imp in all_imports:
            is_allowed = False
            for allowed_regex in self.structural_rules["allowed_imports_regex"]:
                if re.match(allowed_regex, imp):
                    is_allowed = True
                    break
            if not is_allowed:
                report["issues"].append({
                    "type": "Security_Violation",
                    "description": f"Unauthorized import detected: '{imp}'",
                    "severity": "critical"
                })


    def _check_structural_rules(self, code: str, report: Dict[str, Any]):
        """Checks code against structural rules."""
        lines = code.splitlines()
        num_lines = len(lines)
        if num_lines > self.structural_rules["max_lines"]:
            report["issues"].append({
                "type": "Structural_Violation",
                "description": f"Module exceeds max lines ({num_lines}/{self.structural_rules['max_lines']})",
                "severity": "medium"
            })


        num_functions = len(re.findall(r"^\s*def\s+[a-zA-Z0-9_]+\s*\(", code, re.MULTILINE))
        # Log function density as complexity metric
        report["details"]["function_density"] = num_functions / num_lines if num_lines > 0 else 0
        self.telemetry.add_diary_entry(
            "Gatekeeper_Function_Density",
            f"Module '{report['module_name']}' function density: {report['details']['function_density']:.2f}",
            {"module_name": report['module_name'], "density": report['details']['function_density']},
            contributor="Gatekeeper",
            severity="debug"
        )


        if num_functions > self.structural_rules["max_functions"]:
            report["issues"].append({
                "type": "Structural_Violation",
                "description": f"Module exceeds max functions ({num_functions}/{self.structural_rules['max_functions']})",
                "severity": "medium"
            })


        if self.structural_rules["required_docstrings"]:
            if not re.match(r"^\s*\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'", code):
                report["issues"].append({
                    "type": "Structural_Violation",
                    "description": "Missing module-level docstring",
                    "severity": "low"
                })
            function_defs = re.findall(r"^\s*def\s+([a-zA-Z0-9_]+)\s*\(.*?\):\s*$", code, re.MULTILINE)
            for func_name in function_defs:
                func_pattern = r"^\s*def\s+" + re.escape(func_name) + r"\s*\(.*?\):\s*\n\s*(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')"
                if not re.search(func_pattern, code, re.MULTILINE):
                    report["issues"].append({
                        "type": "Structural_Violation",
                        "description": f"Missing docstring for function '{func_name}'",
                        "severity": "low"
                    })
        
        # Isolate risky blocks contextually (class, def, etc.) - Conceptual
        # This would require AST parsing for true contextual isolation.
        # For conceptual purposes, we can log if certain patterns appear within function/class definitions.
        risky_patterns_in_blocks = [
            (r"^\s*(?:def|class)\s+.*?:[\s\S]*?(os\.system|eval\(|exec\()", "high", "Risky function within block"),
        ]
        for pattern, severity_level, description in risky_patterns_in_blocks:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                report["issues"].append({
                    "type": "Security_Violation",
                    "description": f"Contextual risky pattern found: '{description}'",
                    "severity": severity_level
                })
        
        # Stub linter integration (Conceptual)
        # This would involve calling an external linter like Pylint or Flake8
        # and parsing its output.
        # try:
        #     import subprocess
        #     linter_output = subprocess.run(['pylint', '--from-stdin', '--output-format=json'], input=code.encode('utf-8'), capture_output=True, text=True, check=True)
        #     linter_issues = json.loads(linter_output.stdout)
        #     for issue in linter_issues:
        #         report["issues"].append({
        #             "type": "Linter_Warning",
        #             "description": f"Pylint: {issue['message']} (line {issue['line']})",
        #             "severity": "low" if issue['type'] == 'warning' else "medium"
        #         })
        # except Exception as e:
        #     logger.warning(f"Gatekeeper: Conceptual linter integration failed: {e}")