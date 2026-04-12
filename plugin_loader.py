import os
import importlib

PLUGIN_FOLDER = "plugins"
plugins = {}


def load_plugins():
    global plugins
    plugins = {}

    for file in os.listdir(PLUGIN_FOLDER):
        if file.endswith(".py") and file != "__init__.py":
            module_name = f"{PLUGIN_FOLDER}.{file[:-3]}"
            module = importlib.import_module(module_name)

            plugins[file[:-3]] = module  # store as dict

    return plugins


def handle_plugin(user_input):
    for name, plugin in plugins.items():
        if hasattr(plugin, "can_handle") and plugin.can_handle(user_input):
            return plugin.run(user_input)
    return None