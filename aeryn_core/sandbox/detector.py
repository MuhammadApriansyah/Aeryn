#!/usr/bin/env python3
"""Environment detection for sandbox capabilities."""
import os
import shutil
import ctypes
import ctypes.util
import logging

logger = logging.getLogger(__name__)

class EnvironmentDetector:
    """Detect available sandbox capabilities."""
    
    @staticmethod
    def has_bubblewrap():
        return shutil.which("bwrap") is not None
    
    @staticmethod
    def has_secimport():
        try:
            import secimport
            return True
        except ImportError:
            return False
    
    @staticmethod
    def has_unshare():
        try:
            libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
            return hasattr(libc, "unshare")
        except:
            return False
    
    @staticmethod
    def has_root():
        return os.getuid() == 0
    
    @staticmethod
    def has_cgroups():
        return os.path.exists("/sys/fs/cgroup")
    
    @classmethod
    def detect_level(cls):
        """Detect highest available sandbox level (0-3)."""
        if cls.has_bubblewrap() and cls.has_secimport() and cls.has_root():
            return 3
        if cls.has_bubblewrap():
            return 2
        if cls.has_unshare():
            return 1
        return 0
    
    @classmethod
    def get_capabilities(cls):
        """Get dict of all capabilities."""
        return {
            "bubblewrap": cls.has_bubblewrap(),
            "secimport": cls.has_secimport(),
            "unshare": cls.has_unshare(),
            "root": cls.has_root(),
            "cgroups": cls.has_cgroups(),
            "level": cls.detect_level(),
        }
