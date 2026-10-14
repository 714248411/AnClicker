"""Optional private extension loader; public distribution includes no private API implementation."""
import importlib
import os
import sys
from pathlib import Path

def create_agent_session():
    extension=os.environ.get('ANCLICKER_PRIVATE_AGENT_DIR')
    if extension:
        root=Path(extension).resolve()
        if not (root/'anclicker_private_agent/client.py').is_file():raise RuntimeError('私有 Agent 扩展路径无效')
        if str(root) not in sys.path:sys.path.insert(0,str(root))
        return importlib.import_module('anclicker_private_agent.client').ApiAgentSession()
    from agent_runtime import AgentSession
    return AgentSession()
