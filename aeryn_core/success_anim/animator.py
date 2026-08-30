#!/usr/bin/env python3
"""Success Animation."""
import time, sys

class SuccessAnimator:
    def celebrate(self, message="Project berhasil dibuat!"):
        frames = ["🎉", "🎊", "✨", "🌟", "⭐"]
        sys.stdout.write("\n")
        for frame in frames:
            sys.stdout.write(f"\r  {frame} {message}")
            sys.stdout.flush()
            time.sleep(0.2)
        sys.stdout.write("\n\n")
    
    def complete(self, project_name, project_path):
        print("\n" + "="*50)
        print("🎉 PROJECT BERHASIL DIBUAT!")
        print("="*50)
        print(f"  📁 {project_name}")
        print(f"  📍 {project_path}")
        print(f"  🚀 Siap untuk dikembangkan!")
        print("="*50)

success_animator = SuccessAnimator()
