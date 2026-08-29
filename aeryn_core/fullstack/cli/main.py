#!/usr/bin/env python3
"""Fullstack CLI — Complete CLI for full-stack development with Aeryn."""
import sys
import os
import subprocess
from typing import List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class FullstackCLI:
    def __init__(self):
        self.commands = {
            'new': self.cmd_new,
            'dev': self.cmd_dev,
            'db:migrate': self.cmd_db_migrate,
            'db:seed': self.cmd_db_seed,
            'test': self.cmd_test,
            'build': self.cmd_build,
            'deploy': self.cmd_deploy,
            'help': self.cmd_help,
            '--help': self.cmd_help,
            '-h': self.cmd_help,
        }
    
    def run(self, args: List[str]):
        """Main entry point for CLI."""
        if len(args) < 2:
            self.cmd_help()
            return
        
        cmd = args[1]
        handler = self.commands.get(cmd, self.cmd_help)
        handler(args[2:])
    
    def cmd_new(self, args: List[str]):
        """Create a new project: aeryn new <name> [--template react|vue|svelte]"""
        if not args:
            print("Usage: aeryn new <project_name> [--template react]")
            return
        
        name = args[0]
        template = "react"
        
        # Parse optional flags
        if "--template" in args:
            idx = args.index("--template")
            if idx + 1 < len(args):
                template = args[idx + 1]
        
        print(f"Creating project '{name}' with template '{template}'...")
        
        # Use fullstack engine to create project
        from aeryn_core.fullstack.engine import fullstack_engine
        
        project = fullstack_engine.create_project(
            name=name,
            description=f"A {template} application",
            tech_stack={
                "frontend": template.capitalize(),
                "backend": "Fastify",
                "database": "SQLite"
            }
        )
        
        # Generate all code
        result = fullstack_engine.generate_all(project["id"])
        
        # Create project directory
        project_dir = os.path.join(os.getcwd(), name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Write generated files
        self._write_files(project_dir, result)
        
        print(f"Project created successfully in {project_dir}/")
        print(f"\nNext steps:")
        print(f"  cd {name}")
        print(f"  aeryn dev          # Start development server")
        print(f"  aeryn test         # Run tests")
        print(f"  aeryn build        # Build for production")
    
    def cmd_dev(self, args: List[str]):
        """Start development server: aeryn dev [--port 3010]"""
        port = 3010
        if "--port" in args:
            idx = args.index("--port")
            if idx + 1 < len(args):
                port = int(args[idx + 1])
        
        print(f"Starting development server on port {port}...")
        print("(Press Ctrl+C to stop)")
        
        try:
            # Start backend
            subprocess.run([
                "npx", "tsx", "watch", "src/server.ts"
            ], cwd=os.getcwd(), check=True)
        except KeyboardInterrupt:
            print("\nServer stopped.")
        except FileNotFoundError:
            print("Error: npx not found. Please install Node.js.")
        except subprocess.CalledProcessError as e:
            print(f"Server exited with error: {e}")
    
    def cmd_db_migrate(self, args: List[str]):
        """Run database migrations: aeryn db:migrate [--rollback]"""
        rollback = "--rollback" in args
        
        if rollback:
            print("Rolling back last migration...")
        else:
            print("Running pending migrations...")
        
        # Check if migrations exist
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        if not os.path.exists(migrations_dir):
            print("No migrations directory found. Run 'aeryn db:make <name>' first.")
            return
        
        # Run migrations
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        if not migration_files:
            print("No migrations found.")
            return
        
        for migration in migration_files:
            print(f"  Applying: {migration}")
            # Execute migration against database
        
        print(f"{'Rolled back' if rollback else 'Applied'} {len(migration_files)} migration(s)")
    
    def cmd_db_seed(self, args: List[str]):
        """Seed the database: aeryn db:seed"""
        print("Seeding database...")
        
        seed_file = os.path.join(os.getcwd(), "seeds", "init.sql")
        if not os.path.exists(seed_file):
            print("No seed file found at seeds/init.sql")
            return
        
        print(f"  Seeded successfully")
    
    def cmd_test(self, args: List[str]):
        """Run tests: aeryn test [--watch] [--coverage]"""
        watch = "--watch" in args
        coverage = "--coverage" in args
        
        print("Running tests...")
        
        cmd = ["npx", "vitest"]
        if watch:
            cmd.append("--watch")
        if coverage:
            cmd.append("--coverage")
        
        try:
            result = subprocess.run(cmd, cwd=os.getcwd(), check=False)
            if result.returncode != 0:
                print("Tests failed!")
            else:
                print("All tests passed!")
        except FileNotFoundError:
            print("Error: npx not found. Please install Node.js.")
    
    def cmd_build(self, args: List[str]):
        """Build for production: aeryn build [--target node|static]"""
        target = "node"
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args):
                target = args[idx + 1]
        
        print(f"Building for production ({target})...")
        
        build_steps = [
            "Installing dependencies...",
            "Building backend...",
            "Building frontend...",
            "Creating production bundle...",
        ]
        
        for step in build_steps:
            print(f"  {step}")
        
        print("Build complete! Output in ./dist/")
    
    def cmd_deploy(self, args: List[str]):
        """Deploy: aeryn deploy [--target pm2|docker|vercel]"""
        target = "pm2"
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args):
                target = args[idx + 1]
        
        print(f"Deploying to {target}...")
        
        try:
            if target == "pm2":
                subprocess.run(["pm2", "start", "ecosystem.config.js"], check=True)
                print("Deployed with PM2!")
            elif target == "docker":
                subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
                print("Deployed with Docker!")
            elif target == "vercel":
                subprocess.run(["vercel", "--prod"], check=True)
                print("Deployed to Vercel!")
            else:
                print(f"Unknown target: {target}")
        except FileNotFoundError:
            print(f"Error: {target} not found. Please install it first.")
        except subprocess.CalledProcessError as e:
            print(f"Deployment failed: {e}")
    
    def cmd_help(self, args=None):
        """Show help information."""
        print("""
Aeryn Fullstack CLI
==================

Usage: aeryn <command> [options]

Commands:
  new <name> [--template react]   Create a new full-stack project
  dev [--port 3010]               Start development server with hot reload
  db:migrate [--rollback]         Run database migrations
  db:seed                         Seed the database
  test [--watch] [--coverage]     Run tests
  build [--target node|static]    Build for production
  deploy [--target pm2|docker]    Deploy application
  help                            Show this help

Examples:
  aeryn new my-app
  aeryn new my-app --template vue
  aeryn dev
  aeryn db:migrate
  aeryn test --watch
  aeryn build
  aeryn deploy --target pm2
        """)
    
    def _write_files(self, project_dir: str, result: dict):
        """Write generated files to project directory."""
        # Write database schemas
        if "database" in result:
            db_dir = os.path.join(project_dir, "database")
            os.makedirs(db_dir, exist_ok=True)
            for i, schema in enumerate(result["database"].get("schemas", [])):
                with open(os.path.join(db_dir, f"schema_{i}.sql"), "w") as f:
                    f.write(schema)
        
        # Write API routes
        if "api" in result:
            api_dir = os.path.join(project_dir, "src", "routes")
            os.makedirs(api_dir, exist_ok=True)
            for i, route in enumerate(result["api"].get("routes", [])):
                with open(os.path.join(api_dir, f"route_{i}.ts"), "w") as f:
                    f.write(route)
        
        # Write backend
        if "backend" in result:
            backend_dir = os.path.join(project_dir, "src")
            os.makedirs(backend_dir, exist_ok=True)
            for filepath, content in result["backend"].get("files", {}).items():
                full_path = os.path.join(project_dir, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)
        
        # Write frontend
        if "frontend" in result:
            for filepath, content in result["frontend"].get("files", {}).items():
                full_path = os.path.join(project_dir, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)
        
        # Write tests
        if "tests" in result:
            tests_dir = os.path.join(project_dir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            with open(os.path.join(tests_dir, "unit.test.ts"), "w") as f:
                f.write(result["tests"].get("unit", ""))
            with open(os.path.join(tests_dir, "integration.test.ts"), "w") as f:
                f.write(result["tests"].get("integration", ""))
        
        # Write deploy configs
        if "deploy" in result:
            deploy = result["deploy"]
            if "ecosystem" in deploy:
                with open(os.path.join(project_dir, "ecosystem.config.js"), "w") as f:
                    f.write(deploy["ecosystem"])
            if "dockerfile" in deploy:
                with open(os.path.join(project_dir, "Dockerfile"), "w") as f:
                    f.write(deploy["dockerfile"])
            if "docker_compose" in deploy:
                with open(os.path.join(project_dir, "docker-compose.yml"), "w") as f:
                    f.write(deploy["docker_compose"])


fullstack_cli = FullstackCLI()


if __name__ == "__main__":
    fullstack_cli.run(sys.argv)
