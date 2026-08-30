#!/usr/bin/env python3
"""Test V57 features: Multi-Region, Distributed Tracing, Advanced Monitoring."""
import sys, os
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_multi_region_deploy():
    from aeryn_core.multi_region_deploy import multi_region_deployer
    
    config = multi_region_deployer.generate_deploy_config(["us-east", "eu-west"])
    assert "regions" in config
    assert len(config["regions"]) == 2
    assert config["regions"]["us-east"]["provider"] == "aws"
    
    tf = multi_region_deployer.generate_terraform(["us-east", "ap-southeast"])
    assert "aws_lb" in tf
    assert "us-east" in tf
    
    regions = multi_region_deployer.list_regions()
    assert len(regions) >= 4
    
    print("MultiRegionDeployer OK")


def test_distributed_tracing():
    from aeryn_core.distributed_tracing import distributed_tracer
    
    config = distributed_tracer.generate_config()
    assert "config/tracing.js" in config
    assert "opentelemetry" in config["config/tracing.js"].lower()
    
    deps = distributed_tracer.get_dependencies()
    assert "@opentelemetry/api" in deps
    
    print("DistributedTracer OK")


def test_advanced_monitoring():
    from aeryn_core.advanced_monitoring import advanced_monitor
    
    config = advanced_monitor.generate_config()
    assert "config/monitoring.js" in config
    assert "promclient" in config["config/monitoring.js"].lower()
    
    deps = advanced_monitor.get_dependencies()
    assert "promclient" in deps
    
    print("AdvancedMonitor OK")


if __name__ == "__main__":
    test_multi_region_deploy()
    test_distributed_tracing()
    test_advanced_monitoring()
    print("All V57 tests passed!")
