#!/usr/bin/env python3
"""Fullstack project templates."""
from .react_fastify import ReactFastifyTemplate
from .vue_fastify import VueFastifyTemplate

TEMPLATES = {
    "react": ReactFastifyTemplate,
    "vue": VueFastifyTemplate,
}

def get_template(name: str):
    return TEMPLATES.get(name, ReactFastifyTemplate)

__all__ = ['TEMPLATES', 'get_template', 'ReactFastifyTemplate', 'VueFastifyTemplate']
