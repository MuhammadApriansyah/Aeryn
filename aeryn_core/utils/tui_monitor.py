import os
import sys
import time
import re

class CognitiveTerminalUserInterface:
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance

    def render_static_header(self, session_id: str, is_thinking: bool, system_metrics: dict, active_model: str):
        os.system('clear' if os.name == 'posix' else 'cls')
        terminal_columns = 80
        try:
            terminal_columns = os.get_terminal_size().columns
        except Exception:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass
        
        print("\033[96m" + r"""
  █████╗ ███████╗██████╗ ██╗   ██╗███╗   ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
 ██╔══██╗██╔════╝██╔══██╗╚██╗ ██╔╝████╗  ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
 ███████║█████╗  ██████╔╝ ╚████╔╝ ██╔██╗ ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
 ██╔══██║██╔══╝  ██╔══██╗  ╚██╔╝  ██║╚██╗██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
 ██║  ██║███████╗██║  ██║   ██║   ██║ ╚████║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
 ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   
""" + "\033[0m")
        print("\033[90m⚡ Aeryn Cognitive Core - Sovereign Digital Intelligence\033[0m")
        print("\033[90m" + "─" * terminal_columns + "\033[0m")
        
        logo_ascii = [
            r"     .:::. .:::.     ",
            r"    ::::::'::::::    ",
            r"    ':::::::::::'    ",
            r"      ':::::::'      ",
            r"        ':::'        ",
            r"          '          "
        ]
        
        status_text = "THINKING" if is_thinking else "READY"
        info_lines = [
            f"\033[96mAeryn Core v26.0 (2026.08.24)\033[0m",
            f"▸ \033[97mActive Engine\033[0m   : {active_model}",
            f"▸ \033[97mSystem Status\033[0m   : {status_text} (Memory Pools: {system_metrics['memory_pools']})",
            f"▸ \033[97mEpistemic Memory\033[0m  : CogMem L3 Chunks ({system_metrics['long_term']})",
            f"\033[90mSession: {session_id[:12]}\033[0m"
        ]
        
        print("\033[90m┌" + "─" * (terminal_columns - 2) + "┐\033[0m")
        for i in range(max(len(logo_ascii), len(info_lines))):
            left_part = logo_ascii[i] if i < len(logo_ascii) else " " * 21
            right_part = info_lines[i] if i < len(info_lines) else ""
            
            clean_right = right_part
            for code in ["\033[96m", "\033[0m", "\033[97m", "\033[90m", "\033[92m", "\033[93m"]:
                clean_right = clean_right.replace(code, "")
                
            padding_length = max(0, terminal_columns - 30 - len(clean_right))
            print(f"\033[90m│\033[0m  {left_part}  \033[90m│\033[0m  {right_part}" + " " * padding_length + "\033[90m│\033[0m")
        print("\033[90m└" + "─" * (terminal_columns - 2) + "┘\033[0m\n")
        print(" [ RIWAYAT PERCAKAPAN AGENT ]")
        print("\033[90m" + "─" * terminal_columns + "\033[0m\n")

    def launch_realtime_chat_interface(self, target_session_id: str):
        is_thinking = False
        metrics = {
            "memory_pools": len(self.orchestrator.memory_pool.shared_pool),
            "long_term": len(self.orchestrator.cog_mem.long_term_consolidation)
        }
        
        self.render_static_header(target_session_id, is_thinking, metrics, "AERYN_INTERNAL_SIMULATOR")
        print("\n   Sistem pasif. Masukkan stimulus taktis untuk memulai proses nalar...\n")
        
        while True:
            try:
                user_msg = input("\033[96m> \033[0m")
                
                clean_msg = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', user_msg)
                clean_msg = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_msg)
                
                if not clean_msg.strip():
                    continue
                    
                if clean_msg.lower() in ["/quit", "/exit"]:
                    break
                
                is_thinking = True
                
                raw_text_output = (
                    f"<think>Mengevaluasi arahan: {clean_msg}. "
                    "Memeriksa status FSM dan keselarasan memori.</think>"
                    f"Instruksi diterima. Aeryn Core memproses: \"{clean_msg}\" secara mandiri tanpa dependensi luar."
                )
                
                if "<think>" in raw_text_output and "</think>" in raw_text_output:
                    parts = raw_text_output.split("</think>")
                    think_raw = parts[0].replace("<think>", "").strip()
                    agent_reply = parts[-1].strip()
                else:
                    think_raw = f"Menganalisis stimulus input: {clean_msg}"
                    agent_reply = raw_text_output

                print("\033[90m┆ [Reasoning & Introspection]\033[0m")
                words_chunk = think_raw.split()
                animated_text = ""
                for word in words_chunk:
                    animated_text += word + " "
                    sys.stdout.write(f"\r\033[90m┆ {animated_text}\033[0m")
                    sys.stdout.flush()
                    time.sleep(0.03)
                print("\n")
                
                print("\033[90mL\033[0m \033[96mTool calls (1)\033[0m")
                print("\033[90m  L_ \033[96m● \033[97mCognitiveOrchestrator(\033[90m\"digest_stateful_stream\"\033[97m)\033[0m\n")
                
                print("\033[90mL\033[0m \033[97mResponse\033[0m")
                print(f"\033[96m┆ \033[97m{agent_reply}\033[0m\n")
                
                self.orchestrator.digest_external_llm_response(target_session_id, clean_msg, raw_text_output)
                
                is_thinking = False
                metrics["memory_pools"] = len(self.orchestrator.memory_pool.shared_pool)
                metrics["long_term"] = len(self.orchestrator.cog_mem.long_term_consolidation)
                
            except KeyboardInterrupt:
                break
