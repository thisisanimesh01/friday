import os
import sys
import importlib

_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_FOLDER = os.path.join(_DIR, "plugins")
plugins = {}


from logger import get_logger

logger = get_logger("PluginLoader")

def load_plugins():
    global plugins
    plugins = {}

    # Ensure project root is on sys.path so "plugins.<name>" resolves
    if _DIR not in sys.path:
        sys.path.insert(0, _DIR)

    if not os.path.exists(PLUGIN_FOLDER):
        return plugins

    for file in os.listdir(PLUGIN_FOLDER):
        if file.endswith(".py") and file != "__init__.py":
            module_name = f"plugins.{file[:-3]}"
            try:
                module = importlib.import_module(module_name)
                plugins[file[:-3]] = module  # store as dict
                logger.info(f"Loaded plugin: {file[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load plugin {file}: {e}")

    return plugins


def handle_plugin(user_input):
    for name, plugin in plugins.items():
        if hasattr(plugin, "can_handle") and plugin.can_handle(user_input):
            try:
                return plugin.run(user_input)
            except Exception as e:
                logger.error(f"Plugin '{name}' raised an error while executing '{user_input}': {e}")
                return f"Error executing plugin {name}: {str(e)}"
    return None