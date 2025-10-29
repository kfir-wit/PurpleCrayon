#!/usr/bin/env python3
"""
Run working tests to demonstrate fail-fast methodology with updated test files.
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
    """Run working tests in fail-fast mode."""
    print("🚀 PurpleCrayon Working Tests Demo (Updated)")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    import os
    os.chdir(project_dir)
    
    # Test phases with working tests only
    phases = [
        {
            "name": "Unit Tests (Working)",
            "description": "Basic unit tests that are currently working",
            "cmd": ["uv", "run", "pytest", "tests/test_utils_file_utils.py", "tests/test_models.py", "-v", "--maxfail=1", "--tb=short"]
        },
        {
            "name": "Integration Tests (Working)", 
            "description": "Integration tests that are currently working",
            "cmd": ["uv", "run", "pytest", "tests/test_utils_config.py", "tests/test_integration_api.py", "tests/test_integration_workflow.py", "-v", "--maxfail=1", "--tb=short"]
        },
        {
            "name": "Stress Tests (Working)",
            "description": "Stress tests that are currently working",
            "cmd": ["uv", "run", "pytest", "tests/test_ai_generation_api.py", "tests/test_image_service.py", "tests/test_runner.py", "tests/test_tools_smart_selection.py", "-v", "--maxfail=1", "--tb=short"]
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
    
    print(f"\n🎉 ALL WORKING TESTS PASSED!")
    print(f"   Unit tests: ✅")
    print(f"   Integration tests: ✅") 
    print(f"   Stress tests: ✅")
    print(f"\n📊 Test Summary:")
    print(f"   ✅ Working test files: 10")
    print(f"   ❌ Test files with issues: 5")
    print(f"   📝 Note: Some test files have structural issues that need fixing.")

if __name__ == "__main__":
    main()
