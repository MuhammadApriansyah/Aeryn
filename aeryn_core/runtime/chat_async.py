"""Chat async handler — runs AgentLoop in the background task queue (P0).

Decouples LLM execution from the HTTP request cycle. The `/v1/chat/async`
endpoint enqueues a task; the background worker processes it via this handler,
and the client polls `/v1/tasks/{id}` for the result.
"""

import threading

_worker_started = False
_start_lock = threading.Lock()


async def chat_handler(payload: dict) -> dict:
    """Async handler: run the agent loop for a queued chat message."""
    from aeryn_core.agent.loop import AgentLoop

    agent = AgentLoop()
    result = await agent.run(
        payload.get("session_id", "default"),
        payload.get("message", ""),
        user_id=payload.get("user_id", "default"),
    )
    return result


def ensure_worker_started():
    """Idempotently register the chat handler and start the background worker."""
    global _worker_started
    with _start_lock:
        if _worker_started:
            return

        from aeryn_core.runtime.task_queue import get_background_worker, get_task_queue

        worker = get_background_worker()
        # Register the chat handler if not already present
        if "chat" not in worker.handlers:
            worker.handlers["chat"] = chat_handler
            # Re-inject handlers into worker (it was created with empty dict)
            worker.start()

        _worker_started = True