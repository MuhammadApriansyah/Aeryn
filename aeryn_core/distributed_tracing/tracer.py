#!/usr/bin/env python3
"""Distributed Tracing — OpenTelemetry integration."""
from typing import Dict

class DistributedTracer:
    def generate_config(self) -> Dict:
        return {
            "config/tracing.js": """import { NodeTracerProvider } from '@opentelemetry/node';
import { SimpleSpanProcessor } from '@opentelemetry/tracing';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

const provider = new NodeTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(new JaegerExporter({
  serviceName: process.env.SERVICE_NAME || 'aeryn-app',
})));
provider.register();
"""
        }
    
    def get_dependencies(self):
        return ["@opentelemetry/api", "@opentelemetry/node", "@opentelemetry/tracing", "@opentelemetry/exporter-jaeger"]

distributed_tracer = DistributedTracer()
