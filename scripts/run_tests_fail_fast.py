#!/usr/bin/env python3
"""
Fail-fast test runner for PurpleCrayon.

This script runs tests in the following order:
1. Unit tests (basic functionality)
2. Integration tests (API-dependent)
3. Stress tests (comprehensive, for releases)

If any test fails, the script stops immediately.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def main():
    """Run tests in fail-fast mode."""
    print("🚀 PurpleCrayon Fail-Fast Test Runner")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    import os
    os.chdir(project_dir)
    
    # Test phases
    phases = [
        {
            "name": "Unit Tests",
            "marker": "unit",
            "description": "Basic unit tests that should run first",
            "cmd": ["uv", "run", "pytest", "-m", "unit", "-v", "--maxfail=1", "--tb=short"]
        },
        {
            "name": "Integration Tests", 
            "marker": "integration",
            "description": "Integration tests requiring API keys",
            "cmd": ["uv", "run", "pytest", "-m", "integration", "-v", "--maxfail=1", "--tb=short"]
        },
        {
            "name": "Stress Tests",
            "marker": "stress", 
            "description": "Comprehensive tests for major releases",
            "cmd": ["uv", "run", "pytest", "-m", "stress", "-v", "--maxfail=1", "--tb=short"]
        }
    ]
    
    # Run each phase
    for i, phase in enumerate(phases, 1):
        print(f"\n📋 Phase {i}/3: {phase['name']}")
        print(f"   {phase['description']}")
        
        success = run_command(phase['cmd'], phase['name'])
        
        if not success:
            print(f"\n❌ {phase['name']} FAILED!")
            print(f"   Stopping execution due to fail-fast mode.")
            print(f"   Fix the failing tests before proceeding to the next phase.")
            sys.exit(1)
        else:
            print(f"\n✅ {phase['name']} PASSED!")
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"   Unit tests: ✅")
    print(f"   Integration tests: ✅") 
    print(f"   Stress tests: ✅")
    print(f"\n🚀 Ready for deployment!")

if __name__ == "__main__":
    main()
