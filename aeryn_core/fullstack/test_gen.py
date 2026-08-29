#!/usr/bin/env python3
"""Test Generator."""
from typing import Dict

class TestGenerator:
    def generate(self, plan: Dict) -> Dict:
        return {
            "unit": self._generate_unit_tests(plan),
            "integration": self._generate_integration_tests(plan),
            "e2e": self._generate_e2e_tests(plan),
        }
    
    def _generate_unit_tests(self, plan: Dict) -> str:
        return '''import { describe, it, expect } from 'vitest';
import { ItemsService } from '../src/services/index';

describe('ItemsService', () => {
  const service = new ItemsService();
  
  it('should list items', () => {
    expect(service.list()).toEqual([]);
  });
  
  it('should create item', () => {
    const item = service.create({ name: 'test' });
    expect(item.name).toBe('test');
  });
});
'''
    
    def _generate_integration_tests(self, plan: Dict) -> str:
        return '''import { describe, it, expect } from 'vitest';

describe('API Integration', () => {
  it('should return health status', async () => {
    const res = await fetch('http://localhost:3010/health');
    const data = await res.json();
    expect(data.status).toBe('ok');
  });
  
  it('should list items', async () => {
    const res = await fetch('http://localhost:3010/api/items');
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });
});
'''
    
    def _generate_e2e_tests(self, plan: Dict) -> str:
        return '''import { test, expect } from '@playwright/test';

test('home page loads', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await expect(page.locator('h1')).toContainText('Aeryn');
});
'''
