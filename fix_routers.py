#!/usr/bin/env python3
"""Fix all router files by prepending correct headers."""
import os

HEADER = {
    'chat.py': '''"""V61.0 — Chat router for Aeryn API."""
from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import os, sys, json, time, uuid, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.utils.llm_client import get_mode_router, AerynLLMClient
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.error_recovery import get_error_recovery
from aeryn_core.utils.logger import info, warn, error, log_exception

router = APIRouter()

''',
    'dashboard.py': '''"""V61.0 — Dashboard router for Aeryn API."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse, HTMLResponse
import os, sys, time, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from sse_starlette.sse import EventSourceResponse
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
from aeryn_core.utils.performance import get_uptime

router = APIRouter()

''',
    'shared.py': '''"""V61.0 — Shared endpoints router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.memory.vault import AerynVault
from aeryn_core.utils.logger import info, warn, error, log_exception

router = APIRouter()
_start_time = time.time()
_request_count = 0
_error_count = 0

''',
    'notifications.py': '''"""V61.0 — Notifications router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.utils.error_recovery import get_error_recovery

router = APIRouter()

''',
    'tools.py': '''"""V61.0 — Tools & Proactive router for Aeryn API."""
from fastapi import APIRouter
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
    'auth.py': '''"""V61.0 — Auth router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time, json, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.auth.api_keys import get_api_key_manager
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.auth.sso_manager import get_sso_manager
from aeryn_core.auth.rate_limiter import get_rate_limiter

router = APIRouter()

''',
    'plugins.py': '''"""V61.0 — Plugins router for Aeryn API."""
from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.platform.plugin_system import get_plugin_manager
from aeryn_core.safety.secrets_runtime import get_plugin_runtime
from aeryn_core.platform.plugin_marketplace import get_plugin_marketplace

router = APIRouter()

''',
    'workspaces.py': '''"""V61.0 — Workspaces router for Aeryn API."""
from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.platform.workspace_manager import get_workspace_manager

router = APIRouter()

''',
    'admin.py': '''"""V61.0 — Admin router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.soc2_compliance import get_soc2_compliance
from aeryn_core.safety.secrets_runtime import get_secrets_manager, get_plugin_runtime
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.platform.telegram_bot import get_telegram_bot

router = APIRouter()

''',
    'phase4.py': '''"""V61.0 — Phase 4 endpoints router for Aeryn API."""
from fastapi import APIRouter
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.platform.cloud_sync import get_cloud_sync
from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
from aeryn_core.adaptive import get_adaptive_system
from aeryn_core.platform.webhook_system import get_webhook_system
from aeryn_core.platform.email_agent import get_email_agent
from aeryn_core.platform.calendar_integration import get_calendar
from aeryn_core.platform.github_integration import get_github
from aeryn_core.utils.logger import info, warn, error, log_exception
from aeryn_core.utils.performance import get_optimizer, get_uptime

router = APIRouter()

''',
    'web_routes.py': '''"""V61.0 — Web routes router for Aeryn API."""
from fastapi import APIRouter, RedirectResponse
from fastapi.responses import FileResponse, HTMLResponse
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

router = APIRouter()

''',
}

# Section ranges to extract body code
body_ranges = {
    'chat.py': [(343, 580)],  # Health, Compile, Digest, Run, Chat, Search
    'dashboard.py': [(581, 867)],  # SSE, WebSocket, helpers
    'shared.py': [(2512, 2749)],  # Dashboard stats, shared tasks/reminders/vault
    'notifications.py': [(2749, 2818)],  # Notifications, Search, Error recovery
    'tools.py': [(2818, 2953)],  # Tools + Proactive
    'auth.py': [(2954, 3097)],  # Auth
    'plugins.py': [(3151, 3221)],  # Plugin marketplace
    'workspaces.py': [(3221, 3439)],  # Workspaces
    'admin.py': [(3498, 3717)],  # Admin, SSO, Admin Dashboard, SOC2, Email, Secrets
    'phase4.py': [(3713, 4308)],  # Phase 4 + Browser + Vector + Monitoring
    'web_routes.py': [],  # Built-in
}

# Missing sections: Billing (3021-3097), Webhook (3097-3151), SSO (3439-3502), Phase2/3 (2887-2958)
# I'll merge those into appropriate routers

extra_ranges = {
    'auth.py': [(3097, 3217)],       # Billing + Webhook + Plugin Marketplace (actually plugins.py)
    'plugins.py': [(3217, 3439)],    # Workspaces (actually workspaces)
    'workspaces.py': [],
    'shared.py': [(2670, 2749)],
    'tools.py': [(2953, 3017)],      # Auth (no, this is proactive) 
}

# Actually, let me re-check section headers
section_map = {
    343: 'chat',
    581: 'dashboard',
    2512: 'shared',
    2749: 'notifications',
    2818: 'tools',
    2865: 'proactive',
    2887: 'phase2',
    2920: 'phase3',
    2954: 'auth',
    3017: 'billing',
    3093: 'webhook',
    3147: 'plugin_marketplace',
}

for fname, header_text in HEADER.items():
    body_lines = []
    ranges = body_ranges.get(fname, [])
    
    for start, end in ranges:
        # Read original file
        with open('apps/api/aeryn_api.py', 'r') as f:
            all_lines = f.readlines()
        
        for i in range(start - 1, min(end, len(all_lines))):
            line = all_lines[i]
            # Replace @app. with @router.
            line = line.replace('@app.', '@router.')
            # Skip duplicate import lines
            stripped = line.strip()
            if stripped.startswith('import ') and 'from fastapi' in stripped:
                continue
            if stripped.startswith('from fastapi') and 'import' in stripped:
                # Keep only new imports not in header
                if 'APIRouter' in stripped or 'Request' in stripped or 'WebSocket' in stripped or 'Response' in stripped or 'FileResponse' in stripped or 'JSONResponse' in stripped or 'HTMLResponse' in stripped:
                    continue
            if stripped.startswith('from pydantic') and 'import' in stripped:
                continue
            if stripped.startswith('from contextlib'):
                continue
            if 'sys.path.insert' in stripped:
                continue
            if 'import aeryn_core.utils.patch_sqlite' in stripped:
                continue
            if 'app = FastAPI' in stripped or 'app.add_middleware' in stripped or 'app.router' in stripped or 'app.include_router' in stripped:
                continue
            body_lines.append(line)
    
    # Merge extra sections for certain files
    if fname == 'auth.py':
        # Add billing + webhook
        with open('apps/api/aeryn_api.py', 'r') as f:
            all_lines = f.readlines()
        for i in range(3017 - 1, 3151):
            line = all_lines[i]
            line = line.replace('@app.', '@router.')
            body_lines.append(line)
    
    body_code = ''.join(body_lines)
    # Replace version strings
    body_code = body_code.replace('V41.0', 'V61.0').replace('version=41.0', 'version="61.0"')
    
    full_content = header_text.strip() + '\n\n' + body_code.strip() + '\n'
    
    write_path = f'apps/api/routers/{fname}'
    with open(write_path, 'w') as f:
        f.write(full_content)
    print(f"✅ {fname} written ({len(full_content)} chars)")

print("\nAll router files rebuilt!")
