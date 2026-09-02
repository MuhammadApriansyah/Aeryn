"""Reasoning Router — All reasoning systems wired to API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/reasoning", tags=["reasoning"])


# ========================================
# Cerewet Mode — Commitment tracking
# ========================================

class CommitmentRequest(BaseModel):
    user_id: str
    commitment: str
    context: str = ""


@router.post("/cerewet/detect")
async def cerewet_detect(text: str = ""):
    """Detect commitment in text."""
    from aeryn_core.reasoning.cerewet_mode import detect_commitment
    
    result = detect_commitment(text)
    return {"commitment_detected": result}


@router.post("/cerewet/add")
async def cerewet_add(req: CommitmentRequest):
    """Add a commitment."""
    from aeryn_core.reasoning.cerewet_mode import add_commitment
    
    result = add_commitment(req.user_id, req.commitment, req.context)
    return {"status": "ok", "result": result}


@router.get("/cerewet/pending/{user_id}")
async def cerewet_pending(user_id: str):
    """Get pending commitments."""
    from aeryn_core.reasoning.cerewet_mode import pending_for
    
    result = pending_for(user_id)
    return {"pending": result, "count": len(result)}


@router.post("/cerewet/settle")
async def cerewet_settle(user_id: str, commitment_id: str):
    """Settle a commitment."""
    from aeryn_core.reasoning.cerewet_mode import settle_commitment
    
    result = settle_commitment(user_id, commitment_id)
    return {"status": "ok", "result": result}


# ========================================
# Constitutional AI
# ========================================

@router.get("/constitutional/principles")
async def constitutional_principles():
    """Get constitutional principles."""
    from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
    
    ai = get_constitutional_ai()
    principles = ai.get_principles()
    
    return {"principles": principles}


@router.post("/constitutional/check")
async def constitutional_check(action: str, context: str = ""):
    """Check action against principles."""
    from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
    
    ai = get_constitutional_ai()
    result = ai.check_action(action, context)
    
    return {"result": result}


# ========================================
# Context Manager
# ========================================

@router.post("/context/estimate-tokens")
async def context_estimate_tokens(text: str = ""):
    """Estimate token count."""
    from aeryn_core.reasoning.context_manager import get_context_manager
    
    manager = get_context_manager()
    tokens = manager.estimate_tokens(text)
    
    return {"tokens": tokens}


@router.post("/context/trim-messages")
async def context_trim_messages(messages: List[Dict[str, str]], max_tokens: int = 4000):
    """Trim messages to fit context window."""
    from aeryn_core.reasoning.context_manager import get_context_manager
    
    manager = get_context_manager()
    trimmed = manager.trim_messages(messages, max_tokens)
    
    return {"trimmed": trimmed, "original_count": len(messages)}


@router.get("/context/should-summarize")
async def context_should_summarize(message_count: int = 10):
    """Check if context should be summarized."""
    from aeryn_core.reasoning.context_manager import get_context_manager
    
    manager = get_context_manager()
    should = manager.should_summarize(message_count)
    
    return {"should_summarize": should}


# ========================================
# Context Specialization
# ========================================

class ContextBuildRequest(BaseModel):
    goal: str
    context: str = ""


@router.post("/context/classify")
async def context_classify(goal: str):
    """Classify a goal."""
    from aeryn_core.reasoning.context_specialization import GoalClassifier
    
    classifier = GoalClassifier()
    result = classifier.classify(goal)
    
    return {"classification": result}


@router.post("/context/build")
async def context_build(req: ContextBuildRequest):
    """Build context for a goal."""
    from aeryn_core.reasoning.context_specialization import ContextBuilder
    
    builder = ContextBuilder()
    result = builder.build(req.goal, req.context)
    
    return {"context": result}


# ========================================
# Dream Synthesis
# ========================================

@router.post("/dream/synthesize")
async def dream_synthesize(content: str):
    """Synthesize a dream from content."""
    from aeryn_core.reasoning.dream_synthesis import get_dream_synthesizer
    
    synthesizer = get_dream_synthesizer()
    result = synthesizer.synthesize(content)
    
    return {"dream": result}


@router.get("/dream/insights")
async def dream_insights(limit: int = 5):
    """Get dream insights."""
    from aeryn_core.reasoning.dream_synthesis import get_dream_synthesizer
    
    synthesizer = get_dream_synthesizer()
    insights = synthesizer.get_insights(limit)
    
    return {"insights": insights}


@router.get("/dream/summary")
async def dream_summary(limit: int = 3):
    """Get dream summary."""
    from aeryn_core.reasoning.dream_synthesis import get_dream_synthesizer
    
    synthesizer = get_dream_synthesizer()
    summary = synthesizer.generate_summary(limit)
    
    return {"summary": summary}


# ========================================
# Emotion Tone
# ========================================

@router.get("/emotion/tone-directive")
async def emotion_tone_directive(mood: str = "neutral"):
    """Get tone directive for mood."""
    from aeryn_core.reasoning.emotion_tone import tone_directive
    
    directive = tone_directive(mood)
    
    return {"directive": directive}


# ========================================
# Emotional Intelligence
# ========================================

class EmotionRequest(BaseModel):
    text: str
    user_id: str = ""


@router.post("/emotion/detect-mood")
async def emotion_detect_mood(req: EmotionRequest):
    """Detect mood from text."""
    from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
    
    ei = get_emotional_intelligence()
    result = ei.detect_mood(req.text, req.user_id)
    
    return {"mood": result}


@router.post("/emotion/empathy-response")
async def emotion_empathy_response(req: EmotionRequest):
    """Get empathy response."""
    from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
    
    ei = get_emotional_intelligence()
    result = ei.get_empathy_response(req.text, req.user_id)
    
    return {"response": result}


# ========================================
# Long Horizon Planner
# ========================================

class TaskRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    parent_id: str = ""


@router.post("/planner/create-task")
async def planner_create_task(req: TaskRequest):
    """Create a long-term task."""
    from aeryn_core.reasoning.long_horizon import get_long_horizon_planner
    
    planner = get_long_horizon_planner()
    result = planner.create_task(req.title, req.description, req.priority, req.parent_id)
    
    return {"task": result}


@router.post("/planner/decompose-task")
async def planner_decompose_task(task_id: str):
    """Decompose a task into subtasks."""
    from aeryn_core.reasoning.long_horizon import get_long_horizon_planner
    
    planner = get_long_horizon_planner()
    result = planner.decompose_task(task_id)
    
    return {"subtasks": result}


@router.get("/planner/task/{task_id}")
async def planner_get_task(task_id: str):
    """Get a task."""
    from aeryn_core.reasoning.long_horizon import get_long_horizon_planner
    
    planner = get_long_horizon_planner()
    task = planner.get_task(task_id)
    
    return {"task": task}


# ========================================
# Planner
# ========================================

class PlanRequest(BaseModel):
    goal: str
    steps: List[str] = []


@router.post("/planner/make-plan")
async def planner_make_plan(req: PlanRequest):
    """Make a plan."""
    from aeryn_core.reasoning.planner import make_plan
    
    result = make_plan(req.goal, req.steps)
    
    return {"plan": result}


@router.get("/planner/load-plan")
async def planner_load_plan(plan_id: str = ""):
    """Load a plan."""
    from aeryn_core.reasoning.planner import load_plan
    
    result = load_plan(plan_id)
    
    return {"plan": result}


# ========================================
# Proactive Engine
# ========================================

class SuggestionRequest(BaseModel):
    user_id: str
    suggestion: str
    context: str = ""


@router.post("/proactive/create")
async def proactive_create(req: SuggestionRequest):
    """Create a suggestion."""
    from aeryn_core.reasoning.proactive_engine import get_proactive_engine
    
    engine = get_proactive_engine()
    result = engine.create_suggestion(req.user_id, req.suggestion, req.context)
    
    return {"status": "ok", "result": result}


@router.get("/proactive/unread/{user_id}")
async def proactive_unread(user_id: str, limit: int = 10):
    """Get unread suggestions."""
    from aeryn_core.reasoning.proactive_engine import get_proactive_engine
    
    engine = get_proactive_engine()
    results = engine.get_unread(user_id, limit)
    
    return {"suggestions": results, "count": len(results)}


@router.post("/proactive/mark-read")
async def proactive_mark_read(user_id: str, suggestion_id: str):
    """Mark suggestion as read."""
    from aeryn_core.reasoning.proactive_engine import get_proactive_engine
    
    engine = get_proactive_engine()
    result = engine.mark_read(user_id, suggestion_id)
    
    return {"status": "ok", "result": result}


# ========================================
# Daily Briefing (Proactive V2)
# ========================================

@router.get("/proactive/daily/{user_id}")
async def proactive_daily(user_id: str, time_of_day: str = "morning"):
    """Get daily briefing."""
    from aeryn_core.reasoning.proactive_v2 import get_daily_briefing
    
    briefing = get_daily_briefing()
    if time_of_day == "morning":
        result = briefing.generate_morning(user_id)
    else:
        result = briefing.generate_evening(user_id)
    
    return {"briefing": result}


@router.get("/proactive/patterns/{user_id}")
async def proactive_patterns(user_id: str):
    """Detect patterns."""
    from aeryn_core.reasoning.proactive_v2 import get_proactive_v2
    
    engine = get_proactive_v2()
    patterns = engine.detect_patterns(user_id)
    
    return {"patterns": patterns}


@router.get("/proactive/anomalies/{user_id}")
async def proactive_anomalies(user_id: str):
    """Detect anomalies."""
    from aeryn_core.reasoning.proactive_v2 import get_proactive_v2
    
    engine = get_proactive_v2()
    anomalies = engine.detect_anomalies(user_id)
    
    return {"anomalies": anomalies}


# ========================================
# Reasoning Style
# ========================================

@router.get("/reasoning-style/needs-research")
async def reasoning_style_needs_research(query: str = ""):
    """Check if query needs research."""
    from aeryn_core.reasoning.reasoning_style import needs_research
    
    result = needs_research(query)
    
    return {"needs_research": result}


@router.get("/reasoning-style/next-token-hint")
async def reasoning_style_next_token_hint(context: str = ""):
    """Get next token hint."""
    from aeryn_core.reasoning.reasoning_style import build_next_token_hint
    
    result = build_next_token_hint(context)
    
    return {"hint": result}


# ========================================
# Reflection
# ========================================

class ReflectionRequest(BaseModel):
    goal: str
    outcome: str
    strategy: str = ""


@router.post("/reflection/reflect")
async def reflection_reflect(req: ReflectionRequest):
    """Reflect on a run."""
    from aeryn_core.reasoning.reflection import PostRunReflection
    
    refl = PostRunReflection()
    result = refl.reflect(req.goal, req.outcome, req.strategy)
    
    return {"reflection": result}


@router.get("/reflection/recent-strategy")
async def reflection_recent_strategy(limit: int = 5):
    """Get recent strategies."""
    from aeryn_core.reasoning.reflection import PostRunReflection
    
    refl = PostRunReflection()
    strategies = refl.find_recent_strategy(limit)
    
    return {"strategies": strategies}


# ========================================
# Reminder
# ========================================

class ReminderRequest(BaseModel):
    user_id: str
    content: str
    due_at: str = ""


@router.post("/reminder/set")
async def reminder_set(req: ReminderRequest):
    """Set a reminder."""
    from aeryn_core.reasoning.reminder import set_reminder
    
    result = set_reminder(req.user_id, req.content, req.due_at)
    
    return {"status": "ok", "result": result}


@router.get("/reminder/due/{user_id}")
async def reminder_due(user_id: str):
    """Get due reminders."""
    from aeryn_core.reasoning.reminder import due_reminders
    
    results = due_reminders(user_id)
    
    return {"reminders": results, "count": len(results)}


@router.get("/reminder/pending-count/{user_id}")
async def reminder_pending_count(user_id: str):
    """Get pending reminder count."""
    from aeryn_core.reasoning.reminder import pending_count
    
    count = pending_count(user_id)
    
    return {"count": count}


# ========================================
# Self Improvement
# ========================================

class FeedbackRequest(BaseModel):
    user_id: str
    interaction_id: str
    feedback: str
    rating: int = 0


@router.post("/self-improvement/record")
async def self_improvement_record(req: FeedbackRequest):
    """Record interaction."""
    from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
    
    engine = get_self_improvement_engine()
    result = engine.record_interaction(req.user_id, req.interaction_id, req.feedback, req.rating)
    
    return {"status": "ok", "result": result}


@router.post("/self-improvement/submit-feedback")
async def self_improvement_submit_feedback(req: FeedbackRequest):
    """Submit feedback."""
    from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
    
    engine = get_self_improvement_engine()
    result = engine.submit_feedback(req.user_id, req.interaction_id, req.feedback, req.rating)
    
    return {"status": "ok", "result": result}


@router.get("/self-improvement/feedback-stats/{user_id}")
async def self_improvement_feedback_stats(user_id: str):
    """Get feedback statistics."""
    from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
    
    engine = get_self_improvement_engine()
    stats = engine.get_feedback_stats(user_id)
    
    return {"stats": stats}


@router.post("/self-improvement/analyze")
async def self_improvement_analyze(user_id: str):
    """Analyze patterns."""
    from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
    
    engine = get_self_improvement_engine()
    result = engine.analyze_patterns(user_id)
    
    return {"analysis": result}


@router.post("/self-improvement/optimize")
async def self_improvement_optimize(user_id: str, prompt: str = ""):
    """Optimize prompt."""
    from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
    
    engine = get_self_improvement_engine()
    result = engine.optimize_prompt(user_id, prompt)
    
    return {"optimized": result}


# ========================================
# Health
# ========================================

@router.get("/health")
async def reasoning_health():
    """Reasoning module health check."""
    return {"status": "healthy", "module": "reasoning"}
