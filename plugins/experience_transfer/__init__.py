"""Experience Transfer — Extract lessons from Hermes to improve Aeryn."""
import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExperienceExtractor:
    """Extract learnings and patterns from Hermes session history."""
    
    def __init__(self, sessions_db: str = None):
        self.sessions_db = sessions_db or os.path.expanduser("~/.hermes/state.db")
    
    def extract_patterns(self, limit: int = 100) -> List[Dict]:
        """Extract successful patterns from Hermes session transcripts."""
        patterns = []
        
        if not os.path.exists(self.sessions_db):
            logger.warning(f"Hermes sessions DB not found: {self.sessions_db}")
            return patterns
        
        try:
            conn = sqlite3.connect(self.sessions_db)
            cursor = conn.execute("""
                SELECT s.id, s.title, s.model, s.source,
                       m.role, m.content, m.timestamp
                FROM sessions s
                JOIN messages m ON s.id = m.session_id
                ORDER BY s.started_at DESC
                LIMIT ?
            """, (limit,))
            
            sessions = {}
            for row in cursor:
                sid, title, model, source, role, content, ts = row
                if sid not in sessions:
                    sessions[sid] = {
                        "session_id": sid,
                        "title": title,
                        "model": model,
                        "source": source,
                        "messages": [],
                    }
                if isinstance(content, str) and len(content) > 20:
                    sessions[sid]["messages"].append({
                        "role": role,
                        "content": content[:1000],
                        "timestamp": ts,
                    })
            
            conn.close()
            
            # Extract patterns from conversations
            for sid, session in sessions.items():
                msgs = session["messages"]
                if len(msgs) < 2:
                    continue
                
                # Pattern 1: Task completion patterns (assistant followed by tool result)
                for i in range(len(msgs) - 1):
                    if msgs[i]["role"] == "assistant" and msgs[i+1]["role"] == "tool":
                        patterns.append({
                            "type": "task_completion",
                            "title": session.get("title", "unknown"),
                            "user_request": msgs[i-1]["content"] if i > 0 else "",
                            "assistant_response": msgs[i]["content"],
                            "tool_result": msgs[i+1]["content"][:200],
                            "source": session.get("source", "unknown"),
                        })
                
                # Pattern 2: User preferences (corrections, feedback)
                for msg in msgs:
                    content_lower = msg["content"].lower()
                    if any(w in content_lower for w in ["tidak", "salah", "bukan", "perbaiki", "ulang"]):
                        patterns.append({
                            "type": "user_feedback",
                            "title": session.get("title", "unknown"),
                            "feedback": msg["content"],
                            "source": session.get("source", "unknown"),
                        })
            
            logger.info(f"Extracted {len(patterns)} patterns from {len(sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
        
        return patterns[:limit]
    
    def extract_user_preferences(self) -> Dict:
        """Extract user preferences from Hermes session history."""
        prefs = {
            "language": "id",
            "style": "concise",
            "preferences": {},
        }
        
        patterns = self.extract_patterns(limit=50)
        
        for p in patterns:
            if p["type"] == "user_feedback":
                feedback = p["feedback"].lower()
                if "bahasa" in feedback or "indonesia" in feedback:
                    prefs["language"] = "id"
                if "panjang" in feedback or "detail" in feedback:
                    prefs["style"] = "detailed"
                if "pendek" in feedback or "singkat" in feedback:
                    prefs["style"] = "concise"
                if "jangan" in feedback:
                    # Extract specific "jangan X" preferences
                    prefs["preferences"][f"avoid_{len(prefs['preferences'])}"] = p["feedback"]
        
        return prefs
    
    def get_task_templates(self) -> List[Dict]:
        """Extract successful task templates from Hermes history."""
        templates = []
        
        patterns = [p for p in self.extract_patterns(limit=200) if p["type"] == "task_completion"]
        
        # Group by task type
        task_groups = {}
        for p in patterns:
            title = p.get("title", "unknown")
            task_type = title.split()[0] if title else "unknown"
            if task_type not in task_groups:
                task_groups[task_type] = []
            task_groups[task_type].append(p)
        
        # Extract templates from most common task types
        for task_type, patterns in sorted(task_groups.items(), key=lambda x: -len(x[1]))[:5]:
            templates.append({
                "task_type": task_type,
                "frequency": len(patterns),
                "sample_request": patterns[0]["user_request"] if patterns else "",
                "sample_response": patterns[0]["assistant_response"][:300] if patterns else "",
            })
        
        return templates


class AerynFineTuner:
    """Apply extracted learnings to improve Aeryn's behavior."""
    
    def __init__(self):
        self.extractor = ExperienceExtractor()
        self._lessons: List[Dict] = []
        self._preferences: Dict = {}
    
    async def initialize(self, pg_memory=None):
        """Load lessons into Aeryn memory."""
        logger.info("Initializing Aeryn fine-tuning...")
        
        # Extract patterns
        patterns = self.extractor.extract_patterns(limit=50)
        self._preferences = self.extractor.extract_user_preferences()
        
        # Store lessons in PostgreSQL memory
        if pg_memory:
            for i, pattern in enumerate(patterns[:20]):
                lesson_key = f"hermes_lesson_{pattern['type']}_{i}"
                lesson_value = json.dumps(pattern, ensure_ascii=False)
                try:
                    await pg_memory.remember(
                        lesson_key, lesson_value,
                        memory_type="lesson",
                        importance=0.7,
                        skip_embedding=True,
                    )
                except Exception as e:
                    logger.warning(f"Failed to store lesson: {e}")
            
            # Store preferences
            await pg_memory.remember(
                "hermes_user_preferences",
                json.dumps(self._preferences, ensure_ascii=False),
                memory_type="preference",
                importance=0.9,
                skip_embedding=True,
            )
        
        self._lessons = patterns
        logger.info(f"Loaded {len(patterns)} lessons from Hermes experience")
    
    def get_system_prompt_addon(self) -> str:
        """Generate system prompt addition based on learned lessons."""
        lines = []
        
        # Add language preference
        lang = self._preferences.get("language", "id")
        style = self._preferences.get("style", "concise")
        
        if lang == "id":
            lines.append("Bahasa utama: Indonesia. Gunakan bahasa Indonesia yang natural dan santai.")
        
        if style == "concise":
            lines.append("Gaya: Concise. Jawab langsung ke point, tidak perlu bertele-tele.")
        
        # Add specific lessons
        task_lessons = [l for l in self._lessons if l["type"] == "task_completion"][:5]
        if task_lessons:
            lines.append("\nPola tugas yang berhasil:")
            for lesson in task_lessons:
                req = lesson.get("user_request", "")[:100]
                resp = lesson.get("assistant_response", "")[:100]
                if req and resp:
                    lines.append(f"- {req} → {resp}")
        
        # Add user feedback lessons
        feedback_lessons = [l for l in self._lessons if l["type"] == "user_feedback"][:3]
        if feedback_lessons:
            lines.append("\nFeedback dari user:")
            for lesson in feedback_lessons:
                fb = lesson.get("feedback", "")[:150]
                if fb:
                    lines.append(f"- {fb}")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """Get fine-tuning statistics."""
        return {
            "total_lessons": len(self._lessons),
            "task_completions": len([l for l in self._lessons if l["type"] == "task_completion"]),
            "user_feedback": len([l for l in self._lessons if l["type"] == "user_feedback"]),
            "preferences": self._preferences,
        }
