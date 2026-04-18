#!/usr/bin/env python3
"""
Comprehensive test script for all AURA tools.
Run this to verify all tools are working correctly.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from tools.registry import REGISTRY


def test_tool(tool_name, *args, **kwargs):
    """Test a single tool and return results."""
    print(f"\n{'='*50}")
    print(f"Testing: {tool_name}")
    print(f"{'='*50}")

    try:
        tool_func = REGISTRY[tool_name]
        result = tool_func(*args, **kwargs)

        print(f"Input: {args} {kwargs}")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Output: {result.get('output', 'no output')[:200]}{'...' if len(str(result.get('output', ''))) > 200 else ''}")

        return result

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {"status": "error", "output": str(e)}


def main():
    """Run all tool tests."""
    print("AURA Tools Test Suite")
    print("====================")

    results = {}

    # Test file operations first (we'll need these for other tests)
    print("\n--- FILE OPERATIONS ---")

    # Create a test directory
    results["make_directory"] = test_tool("make_directory", "test_tools_dir")

    # Write a test file
    results["write_file"] = test_tool("write_file", "test_tools_dir/test.txt\nHello, World!\nThis is a test file.")

    # Read the test file
    results["read_file"] = test_tool("read_file", "test_tools_dir/test.txt")

    # Find files
    results["find_file"] = test_tool("find_file", "test.txt")

    # Patch the file
    results["patch_file"] = test_tool("patch_file", "test_tools_dir/test.txt\nFIND:\nHello, World!\nREPLACE:\nHello, Universe!")

    # Rename the file
    results["rename_file"] = test_tool("rename_file", "test_tools_dir/test.txt\ntest_tools_dir/renamed.txt")

    # Delete directory (should fail because it's not empty)
    results["delete_directory_fail"] = test_tool("delete_directory", "test_tools_dir")

    # Clean up - delete the file first
    os.remove("test_tools_dir/renamed.txt")
    results["delete_directory"] = test_tool("delete_directory", "test_tools_dir")

    print("\n--- CODE EXECUTION ---")
    results["run_python"] = test_tool("run_python", "print('Hello from Python!')\nprint(2 + 2)")

    print("\n--- SHELL OPERATIONS ---")
    if sys.platform == "win32":
        results["run_shell"] = test_tool("run_shell", "echo Hello from shell!")
    else:
        results["run_shell"] = test_tool("run_shell", "echo 'Hello from shell!'")

    print("\n--- WEB OPERATIONS ---")
    results["web_search"] = test_tool("web_search", "python programming language")

    print("\n--- BROWSER OPERATIONS ---")
    # Note: These might require Playwright to be installed and configured
    try:
        results["browser_scrape"] = test_tool("browser_scrape", "https://httpbin.org/html")
    except Exception as e:
        results["browser_scrape"] = {"status": "error", "output": f"Browser not available: {e}"}

    # Skip browser_click and browser_fill as they require interactive elements

    print("\n--- GUI OPERATIONS ---")
    # Note: These require GUI environment and may not work in headless environments
    try:
        results["app_focus"] = test_tool("app_focus", "Command Prompt")  # Windows
    except Exception as e:
        try:
            results["app_focus"] = test_tool("app_focus", "Terminal")  # macOS/Linux
        except Exception as e2:
            results["app_focus"] = {"status": "error", "output": f"GUI operations not available: {e2}"}

    # Skip other GUI operations as they require specific windows/applications

    print("\n--- LLM CONSULTATION ---")
    results["consult_llm"] = test_tool("consult_llm", "What is the capital of France?")

    print("\n--- KAGGLE OPERATIONS ---")
    # Note: This requires Kaggle API credentials
    try:
        results["download_kaggle"] = test_tool("download_kaggle", "titanic")  # Small dataset
    except Exception as e:
        results["download_kaggle"] = {"status": "error", "output": f"Kaggle not configured: {e}"}

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    success_count = 0
    error_count = 0

    for tool_name, result in results.items():
        status = result.get("status", "unknown")
        if status == "ok":
            success_count += 1
            print(f"✅ {tool_name}: PASSED")
        else:
            error_count += 1
            print(f"❌ {tool_name}: FAILED - {result.get('output', 'unknown error')}")

    print(f"\nTotal: {len(results)} tools tested")
    print(f"Passed: {success_count}")
    print(f"Failed: {error_count}")

    if error_count == 0:
        print("\n All tools are working correctly!")
    else:
        print(f"\n {error_count} tools need attention.")

    return results


if __name__ == "__main__":
    main()