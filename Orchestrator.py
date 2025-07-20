# orchestrator.py
import asyncio
import os
import logging
from core.kernel import Kernel


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Environment Variables ---
# Ensure these are set in your environment before running
# os.environ['GEMINI_API_KEY'] = 'YOUR_GEMINI_API_KEY' # Replace with your actual key or set externally


async def main():
    """
    Main function to initialize and start the Baldur Kernel.
    """
    logger.info("Starting Baldur Orchestrator...")


    # Directory for generated modules
    modules_dir = "modules"
    os.makedirs(modules_dir, exist_ok=True)


    # Initialize the Kernel
    kernel = Kernel(modules_dir=modules_dir)


    # Start the Kernel's HTTP server in a non-blocking way
    logger.info("Baldur Kernel initialized. Starting HTTP server...")
    await kernel.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Baldur Orchestrator stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.exception(f"An unhandled error occurred in the Orchestrator: {e}")