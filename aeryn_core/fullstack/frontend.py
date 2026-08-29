#!/usr/bin/env python3
"""Frontend Generator."""
from typing import Dict, List

class FrontendGenerator:
    def generate(self, plan: Dict) -> Dict:
        files = {}
        for filepath in plan.get("structure", []):
            if filepath.endswith(".tsx"):
                if "App.tsx" in filepath:
                    files[filepath] = self._app_tsx()
                elif "Home" in filepath:
                    files[filepath] = self._home_page()
                elif "Layout" in filepath:
                    files[filepath] = self._layout()
                else:
                    files[filepath] = f"// {filepath}\nexport default function Component() {{ return null; }}\n"
            elif filepath.endswith(".ts"):
                if "main.tsx" in filepath:
                    files[filepath] = self._main_tsx()
                elif "useApi" in filepath:
                    files[filepath] = self._use_api()
                elif "api" in filepath:
                    files[filepath] = self._api_util()
                else:
                    files[filepath] = f"// {filepath}\n"
        return {"files": files, "dependencies": plan.get("dependencies", [])}
    
    def _app_tsx(self):
        return '''export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <h1>Aeryn App</h1>
    </div>
  );
}
'''
    
    def _home_page(self):
        return '''export default function Home() {
  return <div>Welcome to Aeryn</div>;
}
'''
    
    def _layout(self):
        return '''export default function Layout({ children }: { children: React.ReactNode }) {
  return <div className="container mx-auto p-4">{children}</div>;
}
'''
    
    def _main_tsx(self):
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    def _use_api(self):
        return '''import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from './utils/api';

export function useItems() {
  return useQuery({ queryKey: ['items'], queryFn: api.getItems });
}
'''
    
    def _api_util(self):
        return '''const BASE_URL = '/api';

export const api = {
  getItems: async () => fetch(`${BASE_URL}/items`).then(r => r.json()),
  createItem: async (data: any) => fetch(`${BASE_URL}/items`, { method: 'POST', body: JSON.stringify(data) }),
};
'''
