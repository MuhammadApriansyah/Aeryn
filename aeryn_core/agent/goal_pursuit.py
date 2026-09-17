"""V61.3 — Goal Pursuit (F4.2): daemon otonom mengejar goal aktif.

Saat idle (queue kosong), daemon mengambil goal ber-prioritas tertinggi
dan mengeksekusi langkah berikutnya yang belum selesai — menandai progress
+ mencatat jejak ke fact graph (bitemporal). Non-LLM: langkah = aksi
terukur yang bisa diverifikasi (mirror heartbeat/progress pattern).
"""
import json
import logging

logger = logging.getLogger("aeryn.goals")


def pursue_next_goal() -> dict | None:
    """Ambil goal aktif prio tertinggi → eksekusi langkah berikutnya.

    Returns: {"goal_id", "title", "step", "progress", "done"} atau None.
    """
    from aeryn_core.agent.goal_store import get_goal_store

    gs = get_goal_store()
    goal = gs.next_goal()
    if not goal:
        return None

    steps = goal.get("steps") or []
    progress = int(goal.get("progress") or 0)

    # Langkah berikutnya: progress 0-24 -> step 0, 25-49 -> step 1, dst.
    idx = min(progress * len(steps) // 100, len(steps) - 1) if steps else None

    if steps and idx is not None:
        step = steps[idx]
    else:
        # Goal tanpa steps: satu langkah "kerja" generik terukur
        step = "review-and-advance"
        idx = 0

    # Eksekusi langkah: catat jejak nyata ke fact graph (bitemporal)
    try:
        from aeryn_core.memory.fact_store import get_fact_store
        get_fact_store().record(
            entity="goal",
            predicate="step_executed",
            fact=json.dumps({
                "goal_id": goal["id"],
                "title": goal["title"],
                "step_index": idx,
                "step": step,
            }),
            source="daemon-goal-pursuit",
        )
        traced = True
    except Exception as e:
        logger.warning("goal trace: %s", e)
        traced = False

    # Naikkan progress (per langkah; kalau tanpa steps → +25 per pursuit)
    if steps:
        new_progress = min(100, progress + (100 // len(steps)))
    else:
        new_progress = min(100, progress + 25)
    gs.update_progress(goal["id"], new_progress,
                       note=f"step {idx + 1}: {step}" + ("" if traced else " (trace gagal)"))

    return {
        "goal_id": goal["id"],
        "title": goal["title"],
        "step": step,
        "step_index": idx,
        "progress": new_progress,
        "done": new_progress >= 100,
        "traced": traced,
    }
