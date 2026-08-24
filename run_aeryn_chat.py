import sys
import os

def main():
    try:
        from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator
        from aeryn_core.utils.tui_monitor import CognitiveTerminalUserInterface
        
        core_brain = UnifiedCognitiveOrchestrator(dimension=384)
        tui = CognitiveTerminalUserInterface(core_brain)
        tui.launch_realtime_chat_interface(target_session_id="AERYN_CORE_LIVE")
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()
        print("[AERYN TUI] Keluar bersih dari sirkuit terminal.")
        sys.exit(0)

if __name__ == "__main__":
    main()
