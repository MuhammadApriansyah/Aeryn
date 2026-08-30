#!/usr/bin/env python3
"""Custom Generators — Replace default generators."""
from typing import Dict, Callable

class GeneratorRegistry:
    def __init__(self):
        self._generators: Dict[str, Callable] = {}
    
    def register(self, name: str, generator_fn: Callable):
        self._generators[name] = generator_fn
    
    def get(self, name: str) -> Callable:
        return self._generators.get(name)
    
    def list_generators(self):
        return list(self._generators.keys())

generator_registry = GeneratorRegistry()
