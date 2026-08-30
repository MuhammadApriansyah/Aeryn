#!/usr/bin/env python3
"""Fix broken router files."""
import re

with open('/home/sen/aeryn-core-agent/apps/api/aeryn_api.py', 'r') as f:
    lines = f.readlines()

# Headers for each file
HEADERS = {
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
from aeryn_core.utils.error_recovery import get_error_recovery

router = APIRouter()

''',
    'shared.py': '''"""V61.0 — Shared DB endpoints router for Aeryn API."""
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
    'auth.py': '''"""V61.0 — Auth router for Aeryn API."""
from fastapi import APIRouter, Header
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
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.logger import warn, log_exception

router = APIRouter()

''',
    'admin.py': '''"""V61.0 — Admin endpoints router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.soc2_compliance import get_soc2_compliance
from aeryn_core.safety.secrets_runtime import get_secrets_manager, get_plugin_runtime
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.platform.telegram_bot import get_telegram_bot
from aeryn_core.auth.sso_manager import get_sso_manager
from aeryn_core.utils.logger import warn

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
from aeryn_core.utils.logger import info, warn, error
from aeryn_core.utils.performance import get_optimizer, get_uptime
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.platform.auto_task import get_auto_task
from aeryn_core.reasoning.proactive_engine import get_proactive_engine
from aeryn_core.reasoning.proactive_v2 import get_proactive_v2
from aeryn_core.memory.temporal_memory import get_temporal_memory

router = APIRouter()

''',
}

# Sections to extract
EXTRACT = {
    'dashboard.py': [(581, 863)],
    'shared.py': [(2512, 2748)],
    'auth.py': [(2962, 3151)],  # Auth + Billing
    'admin.py': [(3498, 3717)],  # Admin Dashboard + SSO + SOC2 + Email + Secrets
    'phase4.py': [(3713, 4308)],  # Phase 4 + Browser + Vector + Monitoring
}

for fname, ranges in EXTRACT.items():
    body = []
    for start, end in ranges:
        for i in range(start - 1, min(end, len(lines))):
            line = lines[i]
            # Replace @app. with @router.
            line = line.replace('@app.', '@router.')
            stripped = line.strip()
            # Skip duplicate imports
            if stripped.startswith('import ') and 'from fastapi' in stripped:
                continue
            if stripped.startswith('from fastapi') and 'import' in stripped:
                if any(x in stripped for x in ['APIRouter', 'Request', 'WebSocket', 'Response', 'FileResponse', 'JSONResponse', 'HTMLResponse']):
                    continue
            if stripped.startswith('from pydantic') and 'import' in stripped:
                continue
            if stripped.startswith('from contextlib'):
                continue
            if 'sys.path.insert' in stripped:
                continue
            if 'import aeryn_core.utils.patch_sqlite' in stripped:
                continue
            if any(x in stripped for x in ['app = FastAPI', 'app.add_middleware', 'app.router', 'app.include_router']):
                continue
            
            body.append(line)
    
    body_str = ''.join(body)
    body_str = body_str.replace('V41.0', 'V61.0').replace('version=41.0', 'version="61.0"')
    body_str = body_str.replace('version="40.55"', 'version="61.0"')
    
    full = HEADERS[fname] + body_str
    
    with open(f'/home/sen/aeryn-core-agent/apps/api/routers/{fname}', 'w') as f:
        f.write(full)
    print(f"✅ {fname} rebuilt ({len(full)} chars)")

# Now fix auth.py - add BaseModel class definitions
print("\n✅ All broken files rebuilt")
