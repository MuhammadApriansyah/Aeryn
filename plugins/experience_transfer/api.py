"""Experience Transfer API Routes."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/experience/status")
async def experience_status():
    """Get experience transfer status."""
    try:
        from . import AerynFineTuner
        tuner = AerynFineTuner()
        stats = tuner.get_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/experience/lessons")
async def experience_lessons(limit: int = 20):
    """Get extracted lessons."""
    try:
        from . import ExperienceExtractor
        extractor = ExperienceExtractor()
        patterns = extractor.extract_patterns(limit=limit)
        return {"status": "ok", "lessons": patterns, "count": len(patterns)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/experience/preferences")
async def experience_preferences():
    """Get extracted user preferences."""
    try:
        from . import ExperienceExtractor
        extractor = ExperienceExtractor()
        prefs = extractor.extract_user_preferences()
        return {"status": "ok", "preferences": prefs}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/experience/initialize")
async def experience_initialize():
    """Initialize fine-tuning: load lessons into Aeryn memory."""
    try:
        from . import AerynFineTuner
        tuner = AerynFineTuner()
        
        # Try to use PostgreSQL memory if available
        pg_memory = None
        try:
            from plugins.postgres_memory import get_postgres_memory
            pg_memory = get_postgres_memory()
        except ImportError:
            pass
        
        await tuner.initialize(pg_memory)
        
        return {
            "status": "ok",
            "lessons_loaded": len(tuner._lessons),
            "system_prompt_addon": tuner.get_system_prompt_addon(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
