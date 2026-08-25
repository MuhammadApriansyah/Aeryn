class AheadOfTimeContractCompiler:
    def __init__(self):
        self.compiled_trie_registries = {}

    def compile_constitutional_rules_to_trie(self, division_code: int, rules_list: list) -> bool:
        trie = {}
        for rule in rules_list:
            current_level = trie
            words = str(rule).lower().split()
            for word in words:
                if word not in current_level:
                    current_level[word] = {}
                current_level = current_level[word]
            current_level["_LEAF_CONTRACT_VALID_"] = True
            
        self.compiled_trie_registries[division_code] = trie
        return True

    def evaluate_text_against_compiled_trie(self, division_code: int, raw_text: str) -> dict:
        if division_code not in self.compiled_trie_registries:
            return {"violations_detected": 0, "contract_status": "UNCOMPILED_BYPASS"}
            
        trie = self.compiled_trie_registries[division_code]
        words = str(raw_text).lower().split()
        violations = 0
        
        for i in range(len(words)):
            current_level = trie
            for j in range(i, len(words)):
                word = words[j]
                if word in current_level:
                    current_level = current_level[word]
                    if "_LEAF_CONTRACT_VALID_" in current_level:
                        violations += 1
                        break
                else:
                    break
                    
        return {
            "violations_detected": violations,
            "contract_status": "COMPLIANT" if violations == 0 else "BREACH_DETECTED"
        }
