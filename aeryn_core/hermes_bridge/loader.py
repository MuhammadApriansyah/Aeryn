#!/usr/bin/env python3
"""
Shared Loader — Load skills dan scripts dari Aeryn + Hermes.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

HERMES_HOME = os.path.expanduser("~/.hermes")
AERYN_HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_skills():
    """
    Load skills — Aeryn custom (priority) + Hermes shared.
    
    Returns:
        dict: {name: path_to_skill_md}
    """
    skills = {}
    
    # 1. Load Aeryn custom skills (priority)
    aeryn_skills = os.path.join(AERYN_HOME, "skills")
    if os.path.exists(aeryn_skills):
        for name in os.listdir(aeryn_skills):
            path = os.path.join(aeryn_skills, name, "SKILL.md")
            if os.path.exists(path):
                skills[name] = path
                logger.debug(f"Loaded Aeryn skill: {name}")
    
    # 2. Load Hermes shared skills (if available)
    hermes_skills = os.path.join(HERMES_HOME, "skills")
    if os.path.exists(hermes_skills):
        for name in os.listdir(hermes_skills):
            path = os.path.join(hermes_skills, name, "SKILL.md")
            if os.path.exists(path) and name not in skills:
                skills[name] = path
                logger.debug(f"Loaded Hermes skill: {name}")
    
    return skills

def load_scripts():
    """
    Load scripts — Aeryn custom (priority) + Hermes shared.
    
    Returns:
        dict: {name: path_to_script}
    """
    scripts = {}
    
    # 1. Aeryn custom scripts
    aeryn_scripts = os.path.join(AERYN_HOME, "scripts")
    if os.path.exists(aeryn_scripts):
        for f in os.listdir(aeryn_scripts):
            if f.endswith('.py') and not f.startswith('_'):
                name = f[:-3]
                scripts[name] = os.path.join(aeryn_scripts, f)
                logger.debug(f"Loaded Aeryn script: {name}")
    
    # 2. Hermes shared scripts (if available)
    hermes_scripts = os.path.join(HERMES_HOME, "scripts")
    if os.path.exists(hermes_scripts):
        for f in os.listdir(hermes_scripts):
            if f.endswith('.py') and not f.startswith('_'):
                name = f[:-3]
                if name not in scripts:
                    scripts[name] = os.path.join(hermes_scripts, f)
                    logger.debug(f"Loaded Hermes script: {name}")
    
    return scripts

def get_skill(name):
    """Get skill by name."""
    skills = load_skills()
    return skills.get(name)

def get_script(name):
    """Get script by name."""
    scripts = load_scripts()
    return scripts.get(name)

def list_all_skills():
    """List all available skills."""
    return list(load_skills().keys())

def list_all_scripts():
    """List all available scripts."""
    return list(load_scripts().keys())
