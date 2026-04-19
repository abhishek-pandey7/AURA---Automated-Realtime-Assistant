import pkgutil
import importlib
from pathlib import Path

ALL_TOOL_DEFS = []
_dispatch_map = {}

def _init_tools():
    global ALL_TOOL_DEFS, _dispatch_map
    ALL_TOOL_DEFS.clear()
    _dispatch_map.clear()

    pkg_dir = Path(__file__).resolve().parent
    for _, module_name, ispkg in pkgutil.iter_modules([str(pkg_dir)]):
        if ispkg: continue
        try:
            module = importlib.import_module(f"aura.tools.{module_name}")
            
            # Find TOOL_DEF or TOOL_DEFS
            defs = []
            if hasattr(module, "TOOL_DEFS"):
                defs = getattr(module, "TOOL_DEFS")
            elif hasattr(module, "TOOL_DEF"):
                defs = [getattr(module, "TOOL_DEF")]
                
            for tdef in defs:
                if isinstance(tdef, dict) and "function" in tdef and "name" in tdef["function"]:
                    ALL_TOOL_DEFS.append(tdef)
                    tool_name = tdef["function"]["name"]
                    
                    # Map to function reference
                    if hasattr(module, tool_name) and callable(getattr(module, tool_name)):
                        _dispatch_map[tool_name] = getattr(module, tool_name)
                    elif module_name == "shell" and tool_name == "bash":
                        _dispatch_map[tool_name] = getattr(module, "run")
        except Exception:
            pass # Ignore broken generated tools on startup

_init_tools()

def dispatch(name: str, inputs: dict) -> str:
    func = _dispatch_map.get(name)
    if func:
        try:
            res = func(**inputs)
            return res if res is not None else f"[ AURA ] Executed: {name}"
        except TypeError as e:
            # Fallback for unexpected missing properties where **inputs fails mapping exactly
            return f"[ AURA ] Tool arguments error '{name}': {e}"
        except Exception as e:
            return f"[ AURA ] Tool execution error '{name}': {e}"
    
    return f"[ AURA ] Unknown tool: {name}"
