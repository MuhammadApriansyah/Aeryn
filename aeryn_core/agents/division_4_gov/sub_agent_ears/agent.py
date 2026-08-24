class SubAgentEarsRequirementsParser:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, user_prompt: str) -> dict:
        if not user_prompt:
            return {"ears_compliant": False}
            
        has_requirement = any(keyword in user_prompt.lower() for keyword in ["shall", "must", "should", "require"])
        return {"ears_compliant": has_requirement}
