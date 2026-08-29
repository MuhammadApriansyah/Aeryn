#!/usr/bin/env python3
"""Fallback orchestrator — conditional security with directed fallback."""
import logging
from .detector import EnvironmentDetector
from .level0_basic import BasicSandbox
from .level1_namespace import NamespaceSandbox
from .level2_bubblewrap import BubblewrapSandbox
from .level3_full import FullSandbox

logger = logging.getLogger(__name__)

class FallbackOrchestrator:
    def __init__(self, memory_limit_mb=256, cpu_limit_sec=30, fd_limit=64):
        self.memory_limit = memory_limit_mb
        self.cpu_limit = cpu_limit_sec
        self.fd_limit = fd_limit
        self._level = EnvironmentDetector.detect_level()
        self._capabilities = EnvironmentDetector.get_capabilities()
        self._init_sandbox()
    
    def _init_sandbox(self):
        if self._level >= 3:
            self._sandbox = FullSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
        elif self._level >= 2:
            self._sandbox = BubblewrapSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
        elif self._level >= 1:
            self._sandbox = NamespaceSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
        else:
            self._sandbox = BasicSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
    
    @property
    def level(self):
        return self._level
    
    @property
    def capabilities(self):
        return self._capabilities
    
    def execute(self, command, timeout=None):
        try:
            result = self._sandbox.execute(command, timeout=timeout)
            if "error" in result and result["error"]:
                raise Exception(result["error"])
            return result
        except Exception as e:
            logger.warning(f"Level {self._level} failed: {e}, attempting fallback")
        
        # Try lower levels
        if self._level >= 2:
            try:
                logger.info("Falling back to Level 1 (namespace)")
                fallback = NamespaceSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
                result = fallback.execute(command, timeout=timeout)
                if "error" not in result:
                    result["fallback_from"] = self._level
                    result["fallback_to"] = 1
                    return result
            except Exception as e:
                logger.warning(f"Level 1 fallback failed: {e}")
        
        if self._level >= 1:
            try:
                logger.info("Falling back to Level 0 (basic)")
                fallback = BasicSandbox(self.memory_limit, self.cpu_limit, self.fd_limit)
                result = fallback.execute(command, timeout=timeout)
                if "error" not in result:
                    result["fallback_from"] = self._level
                    result["fallback_to"] = 0
                    return result
            except Exception as e:
                logger.warning(f"Level 0 fallback failed: {e}")
        
        # Ultimate fallback
        logger.error("All sandbox levels failed")
        return {"error": "All sandbox isolation levels failed"}
    
    def status(self):
        return {
            "level": self._level,
            "capabilities": self._capabilities,
            "sandbox_type": type(self._sandbox).__name__,
        }

fallback_orchestrator = FallbackOrchestrator()
