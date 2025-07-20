# memory_compressor_daemon.py
import logging
import asyncio
import time
from typing import Dict, Any, List


# Assuming MemoryCompressor and TelemetryService are available
# from memory_compressor import MemoryCompressor
# from telemetry_service import TelemetryService


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryCompressorDaemon:
    """
    A background daemon responsible for periodically triggering Baldur's
    MemoryCompressor to distill raw telemetry logs and other memory fragments
    into compressed, semantically rich representations.
    This helps manage memory bloat and extract higher-level insights.
    """
    def __init__(self, memory_compressor: Any, telemetry_service: Any, compression_interval_seconds: int = 600): # Run every 10 minutes
        self.memory_compressor = memory_compressor
        self.telemetry = telemetry_service
        self.compression_interval_seconds = compression_interval_seconds
        self._running = False
        self._compression_task = None
        self.health_status: Dict[str, Any] = {"status": "initializing", "last_compression_cycle": "N/A", "fragments_generated_this_cycle": 0, "error_count": 0}
        logger.info("MemoryCompressorDaemon initialized.")


    async def start(self):
        """Starts the continuous memory compression loop."""
        if self._running:
            logger.warning("MemoryCompressorDaemon is already running.")
            return


        self._running = True
        self.health_status["status"] = "running"
        self.telemetry.add_diary_entry(
            "MemoryCompressorDaemon_Started",
            "Memory Compressor Daemon started.",
            {},
            contributor="MemoryCompressorDaemon"
        )
        logger.info("MemoryCompressorDaemon: Starting main loop.")
        while self._running:
            try:
                logger.info("MemoryCompressorDaemon: Initiating memory compression cycle.")
                
                # Trigger the memory compressor's cycle
                distilled_fragments = self.memory_compressor.perform_compression_cycle()
                
                self.health_status["last_compression_cycle"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                self.health_status["fragments_generated_this_cycle"] = len(distilled_fragments)
                self.health_status["status"] = "running_ok"


                self.telemetry.add_diary_entry(
                    "MemoryCompressorDaemon_Cycle_Complete",
                    f"Memory compression cycle completed. Generated {len(distilled_fragments)} fragments.",
                    self.health_status,
                    contributor="MemoryCompressorDaemon"
                )
                logger.info("MemoryCompressorDaemon: Compression cycle completed.")


            except Exception as e:
                self.health_status["status"] = "error"
                self.health_status["error_count"] += 1
                self.telemetry.add_diary_entry(
                    "MemoryCompressorDaemon_Error",
                    f"Error during memory compression cycle: {e}",
                    {"error": str(e), "health_status": self.health_status},
                    contributor="MemoryCompressorDaemon",
                    severity="error"
                )
                logger.error(f"MemoryCompressorDaemon: Error during compression cycle: {e}")


            await asyncio.sleep(self.compression_interval_seconds)


    async def stop(self):
        """Stops the memory compressor daemon."""
        self._running = False
        self.health_status["status"] = "stopped"
        self.telemetry.add_diary_entry(
            "MemoryCompressorDaemon_Stopped",
            "Memory Compressor Daemon stopped.",
            {},
            contributor="MemoryCompressorDaemon"
        )
        logger.info("MemoryCompressorDaemon: Stopped.")


    def get_health_status(self) -> Dict[str, Any]:
        """Returns the current health status of the daemon."""
        return self.health_status