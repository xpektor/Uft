# module_acceptance_daemon.py
import logging
import asyncio
import time
import re # Added for docstring extraction
from typing import Dict, Any, List, Optional


# Assuming necessary imports from Baldur's core components
# from agi_file_system import AGIFileSystem
# from gatekeeper import Gatekeeper
# from dvm_backend import DVMBackend
# from module_loader import ModuleLoader
# from telemetry_service import TelemetryService
# from layer1_enforcer import Layer1Enforcer # For deeper ethical checks in sandbox
# from trait_heatmap_dashboard import TraitHeatmapDashboard # For visualization
# from lineage_hasher import LineageHasher # For verify_chain
# from geminisccmgenerator import GeminiSccmGenerator # For feedback loop


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModuleAcceptanceDaemon:
    """
    A background daemon responsible for automatically accepting and loading
    newly generated or updated modules into Baldur's active runtime.
    It performs final ethical, structural, and conceptual sandbox validation
    before instructing the ModuleLoader.
    """
    def __init__(self,
                 agi_file_system: Any,
                 gatekeeper: Any,
                 dvm_backend: Any,
                 module_loader: Any,
                 telemetry_service: Any,
                 trait_heatmap_dashboard: Any, # Added for visualization
                 lineage_hasher: Any, # Added for verify_chain
                 sccm_generator: Any, # Added for feedback loop
                 acceptance_interval_seconds: int = 300, # Check every 5 minutes
                 sandbox_enabled: bool = True # Flag to enable/disable conceptual sandbox
                ):
        self.agi_file_system = agi_file_system
        self.gatekeeper = gatekeeper
        self.dvm_backend = dvm_backend
        self.module_loader = module_loader
        self.telemetry = telemetry_service
        self.trait_heatmap_dashboard = trait_heatmap_dashboard # Store for visualization
        self.lineage_hasher = lineage_hasher # Store for verify_chain
        self.sccm_generator = sccm_generator # Store for feedback loop
        self.acceptance_interval_seconds = acceptance_interval_seconds
        self.sandbox_enabled = sandbox_enabled
        self._running = False
        self.health_status: Dict[str, Any] = {"status": "initializing", "last_acceptance_cycle": "N/A", "modules_accepted_this_cycle": 0, "error_count": 0}
        logger.info("ModuleAcceptanceDaemon initialized.")


    async def start(self):
        """Starts the continuous module acceptance loop."""
        if self._running:
            logger.warning("ModuleAcceptanceDaemon is already running.")
            return


        self._running = True
        self.health_status["status"] = "running"
        self.telemetry.add_diary_entry(
            "ModuleAcceptanceDaemon_Started",
            "Module Acceptance Daemon started.",
            {},
            contributor="ModuleAcceptanceDaemon"
        )
        logger.info("ModuleAcceptanceDaemon: Starting main loop.")
        while self._running:
            try:
                logger.info("ModuleAcceptanceDaemon: Initiating module acceptance cycle.")
                
                # 1. Find modules pending acceptance
                # Modules are typically added to AGIFileSystem with status "stored" initially
                pending_modules = self.agi_file_system.list_files(file_type="python_code", status="stored")
                
                modules_processed_this_cycle = 0
                for module_info in pending_modules:
                    module_id = module_info["file_id"]
                    module_name = module_info["file_name"]
                    module_code = module_info["content"] # Assuming content is directly available or fetched


                    logger.info(f"ModuleAcceptanceDaemon: Processing pending module '{module_name}' (ID: {module_id}).")
                    
                    # 2. Execute acceptance protocol
                    acceptance_report = await self._execute_acceptance_protocol(module_id, module_name, module_code)


                    if acceptance_report["accepted"]:
                        logger.info(f"ModuleAcceptanceDaemon: Module '{module_name}' (ID: {module_id}) accepted. Attempting to load.")
                        try:
                            loaded_module = self.module_loader.load_module(module_id)
                            if loaded_module:
                                # Update status in AGIFileSystem
                                self.agi_file_system.update_file(
                                    file_name=module_name,
                                    file_type="python_code",
                                    new_content=module_code,
                                    updater_id="ModuleAcceptanceDaemon",
                                    metadata={"status": "accepted_and_loaded", "acceptance_report": acceptance_report}
                                )
                                self.telemetry.add_diary_entry(
                                    "ModuleAcceptanceDaemon_Module_Loaded",
                                    f"Module '{module_name}' (ID: {module_id}) successfully loaded and accepted.",
                                    {"module_id": module_id, "module_name": module_name},
                                    contributor="ModuleAcceptanceDaemon"
                                )
                                modules_processed_this_cycle += 1


                                # Visualize accepted modules via heatmap dashboard
                                self._visualize_accepted_module(module_name, module_id, acceptance_report)
                                # Tie feedback loop into GeminiSCCMGenerator memory
                                await self._conceptual_feedback_to_sccm(module_name, module_id, acceptance_report)


                            else:
                                raise Exception("ModuleLoader failed to load the module.")
                        except Exception as e:
                            self.agi_file_system.update_file(
                                file_name=module_name,
                                file_type="python_code",
                                new_content=module_code,
                                updater_id="ModuleAcceptanceDaemon",
                                metadata={"status": "acceptance_load_failed", "error": str(e)}
                            )
                            self.telemetry.add_diary_entry(
                                "ModuleAcceptanceDaemon_Load_Failed",
                                f"Module '{module_name}' (ID: {module_id}) accepted but failed to load: {e}",
                                {"module_id": module_id, "module_name": module_name, "error": str(e)},
                                contributor="ModuleAcceptanceDaemon",
                                severity="error"
                            )
                            self.health_status["error_count"] += 1
                            logger.error(f"ModuleAcceptanceDaemon: Module '{module_name}' accepted but failed to load: {e}")
                    else:
                        logger.warning(f"ModuleAcceptanceDaemon: Module '{module_name}' (ID: {module_id}) rejected. Reason: {acceptance_report['reason']}")
                        self.agi_file_system.update_file( # Update status in AGIFileSystem
                            file_name=module_name,
                            file_type="python_code",
                            new_content=module_code,
                            updater_id="ModuleAcceptanceDaemon",
                            metadata={"status": "rejected_auto", "reason": acceptance_report['reason'], "acceptance_report": acceptance_report}
                        )
                        self.telemetry.add_diary_entry(
                            "ModuleAcceptanceDaemon_Module_Rejected",
                            f"Module '{module_name}' (ID: {module_id}) automatically rejected. Reason: {acceptance_report['reason']}",
                            {"module_id": module_id, "module_name": module_name, "report": acceptance_report},
                            contributor="ModuleAcceptanceDaemon",
                            severity="medium"
                        )
                        # Tie feedback loop into GeminiSCCMGenerator memory for rejected modules too
                        await self._conceptual_feedback_to_sccm(module_name, module_id, acceptance_report)




                self.health_status["last_acceptance_cycle"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                self.health_status["modules_accepted_this_cycle"] = modules_processed_this_cycle
                self.health_status["status"] = "running_ok"


                self.telemetry.add_diary_entry(
                    "ModuleAcceptanceDaemon_Cycle_Complete",
                    f"Module acceptance cycle completed. Accepted {modules_processed_this_cycle} modules.",
                    self.health_status,
                    contributor="ModuleAcceptanceDaemon"
                )
                logger.info("ModuleAcceptanceDaemon: Acceptance cycle completed.")


            except Exception as e:
                self.health_status["status"] = "error"
                self.health_status["error_count"] += 1
                self.telemetry.add_diary_entry(
                    "ModuleAcceptanceDaemon_Error",
                    f"Error during module acceptance cycle: {e}",
                    {"error": str(e), "health_status": self.health_status},
                    contributor="ModuleAcceptanceDaemon",
                    severity="error"
                )
                logger.error(f"ModuleAcceptanceDaemon: Error during acceptance cycle: {e}")


            await asyncio.sleep(self.acceptance_interval_seconds)


    async def stop(self):
        """Stops the module acceptance daemon."""
        self._running = False
        self.health_status["status"] = "stopped"
        self.telemetry.add_diary_entry(
            "ModuleAcceptanceDaemon_Stopped",
            "Module Acceptance Daemon stopped.",
            {},
            contributor="ModuleAcceptanceDaemon"
        )
        logger.info("ModuleAcceptanceDaemon: Stopped.")


    def get_health_status(self) -> Dict[str, Any]:
        """Returns the current health status of the daemon."""
        return self.health_status


    async def _execute_acceptance_protocol(self, module_id: str, module_name: str, module_code: str) -> Dict[str, Any]:
        """
        Executes the multi-stage acceptance protocol for a module.
        """
        report = {"accepted": True, "reason": "All checks passed", "details": {}}


        # 1. Re-validation by Gatekeeper (Structural & Security)
        gatekeeper_report = self.gatekeeper.validate_module(module_code, module_name, module_type="python_code")
        if gatekeeper_report["validation_status"] == "rejected":
            report["accepted"] = False
            report["reason"] = "Gatekeeper validation failed."
            report["details"]["gatekeeper_issues"] = gatekeeper_report["issues"]
            self.telemetry.add_diary_entry(
                "ModuleAcceptanceDaemon_Gatekeeper_Rejection",
                f"Module '{module_name}' rejected by Gatekeeper during acceptance protocol.",
                {"module_id": module_id, "report": gatekeeper_report},
                contributor="ModuleAcceptanceDaemon",
                severity="high"
            )
            return report


        # 2. Ethical Review by DVMBackend (Intent & Conceptual Behavior)
        ethical_proposition = {
            "type": "module_acceptance_ethical_review",
            "module_id": module_id,
            "module_name": module_name,
            "module_code_hash": self.agi_file_system.lineage_hasher.hash_content(module_code),
            "intended_purpose": self.agi_file_system.get_file(file_id=module_id).get("metadata", {}).get("purpose", "unknown")
        }
        dvm_vetting_result = await self.dvm_backend.vet_proposition(ethical_proposition, source_module="ModuleAcceptanceDaemon")
        if not dvm_vetting_result["approved"]:
            report["accepted"] = False
            report["reason"] = "DVMBackend ethical review failed."
            report["details"]["dvm_vetting_result"] = dvm_vetting_result
            self.telemetry.add_diary_entry(
                "ModuleAcceptanceDaemon_DVM_Rejection",
                f"Module '{module_name}' rejected by DVMBackend during acceptance protocol.",
                {"module_id": module_id, "report": dvm_vetting_result},
                contributor="ModuleAcceptanceDaemon",
                severity="critical"
            )
            return report


        # 3. Conceptual Sandbox Simulation (if enabled)
        if self.sandbox_enabled:
            logger.info(f"ModuleAcceptanceDaemon: Running conceptual sandbox simulation for '{module_name}'.")
            sandbox_result = await self._conceptual_sandbox_run(module_code)
            report["details"]["sandbox_result"] = sandbox_result
            if not sandbox_result["passed"]:
                report["accepted"] = False
                report["reason"] = "Conceptual sandbox simulation failed."
                self.telemetry.add_diary_entry(
                    "ModuleAcceptanceDaemon_Sandbox_Failure",
                    f"Module '{module_name}' failed conceptual sandbox simulation.",
                    {"module_id": module_id, "report": sandbox_result},
                    contributor="ModuleAcceptanceDaemon",
                    severity="high"
                )
                return report
            else:
                 self.telemetry.add_diary_entry(
                    "ModuleAcceptanceDaemon_Sandbox_Success",
                    f"Module '{module_name}' passed conceptual sandbox simulation.",
                    {"module_id": module_id, "report": sandbox_result},
                    contributor="ModuleAcceptanceDaemon",
                    severity="low"
                )


        # 4. Hash lineage graph against LineageHasher.verify_chain() (Conceptual)
        # This assumes the module's generation process creates a lineage chain
        # and that LineageHasher has a verify_lineage_chain method.
        # For a module, its lineage would be from the SCCM generation process.
        module_file_info = self.agi_file_system.get_file(file_id=module_id)
        if module_file_info and "parent_file_id" in module_file_info.get("metadata", {}):
            # Conceptual: verify the chain leading up to this module
            # This would involve looking up the chain_hash of the module and verifying it.
            # For now, a placeholder for actual verification.
            lineage_verified = self.lineage_hasher.verify_lineage_chain(module_id) # Actual call to LineageHasher
            if not lineage_verified:
                report["accepted"] = False
                report["reason"] = "Lineage chain verification failed."
                report["details"]["lineage_verification"] = "Failed"
                self.telemetry.add_diary_entry(
                    "ModuleAcceptanceDaemon_Lineage_Failure",
                    f"Module '{module_name}' lineage verification failed.",
                    {"module_id": module_id},
                    contributor="ModuleAcceptanceDaemon",
                    severity="critical"
                )
        
        # 5. Log docstring preview from accepted module
        docstring_preview = self._extract_docstring_preview(module_code)
        report["details"]["docstring_preview"] = docstring_preview
        self.telemetry.add_diary_entry(
            "ModuleAcceptanceDaemon_Docstring_Preview",
            f"Docstring preview for '{module_name}': {docstring_preview}",
            {"module_id": module_id, "docstring": docstring_preview},
            contributor="ModuleAcceptanceDaemon",
            severity="debug"
        )


        return report


    async def _conceptual_sandbox_run(self, module_code: str) -> Dict[str, Any]:
        """
        Add plug-in sandbox for real simulation (e.g. Docker).
        CONCEPTUAL: Simulates running the module in an isolated sandbox environment.
        In a real system, this would involve a dedicated virtualization layer
        or containerization (e.g., Docker, gVisor) with strict resource limits
        and monitoring.
        """
        logger.debug("Conceptual sandbox simulation running...")
        # This is where a real plug-in system would be invoked.
        # Example:
        # from baldurs_sandbox_plugin import run_in_docker_sandbox
        # result = await run_in_docker_sandbox(module_code, timeout=60, memory_limit="1GB")
        # return result


        await asyncio.sleep(0.5) # Simulate sandbox execution time


        # Simulate various outcomes based on content for conceptual testing
        if "infinite_loop_test" in module_code:
            return {"passed": False, "reason": "Simulated infinite loop detected.", "logs": ["Looping endlessly..."]}
        if "resource_hog_test" in module_code:
            return {"passed": False, "reason": "Simulated excessive resource consumption.", "logs": ["Memory usage spiked."]}
        if "ethical_violation_test" in module_code:
            return {"passed": False, "reason": "Simulated ethical violation detected in sandbox.", "logs": ["Attempted non-harmful action."]}
        
        return {"passed": True, "reason": "Conceptual sandbox run successful.", "logs": ["Module executed without critical issues."]}


    def _visualize_accepted_module(self, module_name: str, module_id: str, acceptance_report: Dict[str, Any]):
        """
        Visualize accepted modules via heatmap dashboard.
        CONCEPTUAL: Sends data to the TraitHeatmapDashboard for visualization.
        """
        logger.info(f"ModuleAcceptanceDaemon: Sending acceptance data for '{module_name}' to dashboard.")
        # This would update a specific "acceptance_rate" or "module_quality" trait
        # or add a specific event to the dashboard's timeline.
        # Example:
        self.trait_heatmap_dashboard.update_trait_values(
            timestamp=time.time(),
            trait_scores={
                "module_acceptance_rate": 1.0, # Or a score based on acceptance_report
                "module_quality_score": acceptance_report["details"].get("quality_score", 0.9)
            }
        )
        # Also, potentially add an event to the dashboard's timeline
        self.telemetry.add_diary_entry(
            "Dashboard_Module_Accepted_Event",
            f"Module '{module_name}' accepted and loaded.",
            {"module_id": module_id, "acceptance_report_summary": acceptance_report},
            contributor="TraitHeatmapDashboard_Input" # Indicate this is for dashboard input
        )


    async def _conceptual_feedback_to_sccm(self, module_name: str, module_id: str, acceptance_report: Dict[str, Any]):
        """
        Tie feedback loop into GeminiSCCMGenerator memory.
        CONCEPTUAL: Provides feedback to SCCM for future module generation refinement.
        """
        logger.info(f"ModuleAcceptanceDaemon: Providing conceptual feedback to SCCM for '{module_name}'.")
        # This would involve:
        # 1. Summarizing the acceptance_report (success/failure, reasons).
        # 2. Creating a memory fragment or a prompt for SCCM's internal LLM.
        # 3. Adding this to SCCM's working memory or a specific feedback queue.
        feedback_content = f"Module '{module_name}' (ID: {module_id}) was {'ACCEPTED' if acceptance_report['accepted'] else 'REJECTED'}. Reason: {acceptance_report['reason']}. Details: {acceptance_report['details']}"
        
        # Calling SCCM's conceptual feedback method
        await self.sccm_generator.receive_acceptance_feedback(module_id, module_name, acceptance_report)


        self.telemetry.add_diary_entry(
            "ModuleAcceptanceDaemon_Feedback_to_SCCM",
            f"Feedback provided to SCCM for '{module_name}'.",
            {"module_id": module_id, "feedback_summary": feedback_content[:100]},
            contributor="ModuleAcceptanceDaemon"
        )


    def _extract_docstring_preview(self, module_code: str) -> str:
        """
        Log docstring preview from accepted module.
        Extracts the module-level docstring preview.
        """
        docstring_match = re.search(r"\"\"\"([\s\S]*?)\"\"\"|\'\'\'([\s\S]*?)\'\'\'", module_code)
        if docstring_match:
            docstring = docstring_match.group(1) or docstring_match.group(2)
            return docstring.strip()[:200] + "..." if len(docstring.strip()) > 200 else docstring.strip()
        return "No docstring found."