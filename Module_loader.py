# module_loader.py
import importlib.util
import sys
import os
import logging


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModuleLoader:
    """
    Baldur's Module Loader (conceptual L3.0.4 - part of Sentience OS Kernel/Core).
    Responsible for dynamically loading and managing cognitive modules.
    """
    def __init__(self, modules_dir: str):
        self.modules_dir = modules_dir
        os.makedirs(self.modules_dir, exist_ok=True) # Ensure modules directory exists
        self.loaded_modules = {}
        logger.info(f"ModuleLoader initialized. Modules directory: {self.modules_dir}")


    def load_module(self, module_name: str, file_path: str):
        """
        Dynamically loads a Python module from a given file path.


        Args:
            module_name (str): The name to assign to the loaded module.
            file_path (str): The absolute path to the module's Python file.


        Returns:
            module: The loaded module object, or None if loading fails.
        """
        if not os.path.exists(file_path):
            logger.error(f"ModuleLoader: File not found at {file_path}")
            return None


        if module_name in self.loaded_modules:
            logger.warning(f"ModuleLoader: Module '{module_name}' already loaded. Reloading...")
            # For simplicity, we'll just remove and re-add if it exists
            # In a real system, more sophisticated reload logic would be needed.
            del self.loaded_modules[module_name]
            if module_name in sys.modules:
                del sys.modules[module_name] # Remove from sys.modules to force a clean reload


        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None:
                logger.error(f"ModuleLoader: Could not get spec for module {module_name} from {file_path}")
                return None


            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module # Add to sys.modules
            spec.loader.exec_module(module) # Execute the module code


            self.loaded_modules[module_name] = module
            logger.info(f"ModuleLoader: Successfully loaded module '{module_name}' from {file_path}")
            return module
        except Exception as e:
            logger.error(f"ModuleLoader: Failed to load module '{module_name}' from {file_path}: {e}")
            return None


    def get_module(self, module_name: str):
        """
        Retrieves a previously loaded module.


        Args:
            module_name (str): The name of the module to retrieve.


        Returns:
            module: The loaded module object, or None if not found.
        """
        return self.loaded_modules.get(module_name)


    def get_all_loaded_modules(self) -> dict:
        """
        Returns a dictionary of all currently loaded modules.
        """
        return self.loaded_modules


    def unload_module(self, module_name: str):
        """
        Unloads a module. Note: Unloading Python modules cleanly can be complex
        due to references. This is a basic attempt.


        Args:
            module_name (str): The name of the module to unload.
        """
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]
            if module_name in sys.modules:
                del sys.modules[module_name]
            logger.info(f"ModuleLoader: Unloaded module '{module_name}'.")
        else:
            logger.warning(f"ModuleLoader: Module '{module_name}' not found for unloading.")