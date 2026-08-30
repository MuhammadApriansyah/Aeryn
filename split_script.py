#!/usr/bin/env python3
"""One-shot script to extract router sections from aeryn_api.py."""
import re, os

with open('apps/api/aeryn_api.py', 'r') as f:
    lines = f.readlines()

# Define header for all router files
HEADER = '''"""V61.0 — Modular router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time, json, uuid, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

'''

# Define sections with their line ranges (1-indexed)
# Each section extracts raw code and replaces @app. with @router.
sections = {
    'chat.py': """
from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import os, sys, json, time, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.reasoning.dream_synthesis import get_dream_synthesizer
from aeryn_core.memory.enhanced_memory import get_entity_extractor, get_preference_learner, get_cross_session_recall
from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails
from aeryn_core.safety.enhanced_sandbox import get_enhanced_sandbox, SandboxLimits
from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator, AgentRole, TaskPriority as AgentTaskPriority
from aeryn_core.memory.memory_decay import get_memory_decay_engine
from aeryn_core.memory.entity_resolution import get_entity_resolver
from aeryn_core.safety.owasp_security import get_owasp_security
from aeryn_core.utils.llm_client import get_mode_router, AerynLLMClient
from aeryn_core.utils.error_recovery import get_error_recovery, with_retry, with_fallback, with_circuit_breaker
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.logger import info, warn, error, log_exception

router = APIRouter()

class CompileRequest(BaseModel):
    session_id: str = "default"
    base_prompt: str = ""
    user_prompt: str = ""
    history: list = []
    tasks: list = []

class DigestRequest(BaseModel):
    session_id: str = "default"
    user_prompt: str = ""
    response: str = ""

class RunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])

""",
    'dashboard.py': HEADER + '''from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse
import os, sys, time, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.realtime import get_emitter
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.safety.safety_engine import get_safety_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.auth.api_keys import get_api_key_manager
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.memory.vault import AerynVault
from aeryn_core.memory.social_memory import SocialMemory

router = APIRouter()

''',
    'shared.py': HEADER + '''from fastapi import APIRouter
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.memory.vault import AerynVault
from aeryn_core.utils.logger import info, warn, error

router = APIRouter()
db = get_shared_db()

''',
    'notifications.py': HEADER + '''from fastapi import APIRouter
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.utils.error_recovery import get_error_recovery

router = APIRouter()

''',
    'tools.py': HEADER + '''from fastapi import APIRouter
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.tool_runtime import get_tool_runtime
from aeryn_core.platform.background_queue import get_task_queue
from aeryn_core.reasoning.proactive_engine import get_proactive_engine
from aeryn_core.reasoning.long_horizon import get_long_horizon_planner, TaskPriority
from aeryn_core.platform.auto_task import get_auto_task
from aeryn_core.reasoning.context_manager import get_context_manager
from aeryn_core.memory.memory_decay import get_memory_decay_engine
from aeryn_core.memory.entity_resolution import get_entity_resolver
from aeryn_core.safety.owasp_security import get_owasp_security
from aeryn_core.database.semantic_indexer import get_semantic_indexer

router = APIRouter()

''',
    'auth.py': HEADER + '''from fastapi import APIRouter
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.auth.api_keys import get_api_key_manager
from pydantic import BaseModel

router = APIRouter()

''',
    'plugins.py': HEADER + '''from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.plugin_system import get_plugin_manager
from aeryn_core.safety.secrets_runtime import get_plugin_runtime
from pydantic import BaseModel

router = APIRouter()

''',
    'workspaces.py': HEADER + '''from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.workspace_manager import get_workspace_manager
from pydantic import BaseModel

router = APIRouter()

''',
    'admin.py': HEADER + '''from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.auth.auth import get_auth
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.soc2_compliance import get_soc2_compliance
from pydantic import BaseModel

router = APIRouter()

''',
    'phase4.py': HEADER + '''from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.memory.temporal_memory import get_temporal_memory
from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.platform.cloud_sync import get_cloud_sync
from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
from aeryn_core.adaptive import get_adaptive_system
from aeryn_core.platform.webhook_system import get_webhook_system
from aeryn_core.platform.telegram_bot import get_telegram_bot
from aeryn_core.platform.email_agent import get_email_agent
from aeryn_core.platform.calendar_integration import get_calendar
from aeryn_core.platform.github_integration import get_github
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.utils.performance import get_optimizer, get_uptime
from aeryn_core.utils.logger import info, warn, error

router = APIRouter()

''',
}

# Get section line ranges
section_ranges = {
    'chat.py': (343, 580),       # Health, Compile, Digest, Run, Chat, Search, Dashboard, Chat routes
    'dashboard.py': (581, 867),  # SSE, WebSocket + helpers
    'shared.py': (2639, 2749),   # dashboard_stats + shared DB endpoints
    'notifications.py': (2749, 2818),  # Notifications, Search, Error Recovery
    'tools.py': (2818, 2869),    # Tool Runtime + Proactive
    'auth.py': (2958, 3097),     # Auth
    'plugins.py': (3151, 3221),  # Plugin Marketplace
    'workspaces.py': (3221, 3439), # Workspaces
    'admin.py': (3502, 3717),    # Admin + SSO + Admin Dashboard + SOC2 + Email + Secrets
    'phase4.py': (3717, 4308),   # Phase 4 + Browser + Vector + Monitoring
}

for filename, (start, end) in section_ranges.items():
    header = HEADER[filename] if filename in HEADER else HEADER
    code = header
    for i in range(start - 1, min(end, len(lines))):
        line = lines[i]
        line = line.replace('@app.', '@router.').replace('app = ', '# app = ')
        # Remove duplicate import lines
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            if stripped in [h.strip() for h in header.split('\n')]:
                continue
        code += line
    write_path = os.path.join('apps/api/routers', filename)
    with open(write_path, 'w') as f:
        f.write(code)
    print(f"✅ {filename}: lines {start}-{end} = {len(code)} chars")

# Fix chat.py - need BaseModel definitions
print("\nAll router files created!")
os.system('python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in [\"apps/api/routers/\" + f for f in [\"chat.py\",\"dashboard.py\",\"shared.py\",\"notifications.py\",\"tools.py\",\"auth.py\",\"plugins.py\",\"workspaces.py\",\"admin.py\",\"phase4.py\"]]]]" 2>&1 | head -20')
