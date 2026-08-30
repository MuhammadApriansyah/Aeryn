#!/usr/bin/env python3
"""Multi-Region Deploy — Deploy to multiple regions."""
from typing import Dict, List

class MultiRegionDeployer:
    def __init__(self):
        self._regions = {
            "us-east": {"name": "US East (Virginia)", "provider": "aws", "region": "us-east-1"},
            "us-west": {"name": "US West (Oregon)", "provider": "aws", "region": "us-west-2"},
            "eu-west": {"name": "EU West (Ireland)", "provider": "aws", "region": "eu-west-1"},
            "ap-southeast": {"name": "Asia Pacific (Singapore)", "provider": "aws", "region": "ap-southeast-1"},
        }
    
    def generate_deploy_config(self, regions: List[str]) -> Dict:
        """Generate deploy config for multiple regions."""
        config = {"regions": {}, "load_balancer": {"enabled": True, "strategy": "latency"}}
        
        for region in regions:
            if region in self._regions:
                config["regions"][region] = {
                    "provider": self._regions[region]["provider"],
                    "region": self._regions[region]["region"],
                    "replicas": 2,
                }
        
        return config
    
    def generate_terraform(self, regions: List[str]) -> str:
        """Generate Terraform config for multi-region."""
        tf = '''
provider "aws" {
  region = "us-east-1"
}

# Application Load Balancer
resource "aws_lb" "app" {
  name               = "aeryn-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids
}
'''
        for region in regions:
            tf += '''

            
# {region} deployment
module "app_{region}" {
  source = "./modules/app"
  region = "{region}"
  replicas = 2
}
'''
        return tf
    
    def list_regions(self) -> Dict:
        return self._regions

multi_region_deployer = MultiRegionDeployer()
