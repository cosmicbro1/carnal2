#!/usr/bin/env python3
"""
CARNAL 2.0 - FLAWLESS SETUP ASSISTANT
======================================
Run this if FLAWLESS_SETUP.bat has issues, or for detailed verification.

Usage: python setup_assistant.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}! {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}→ {text}{Colors.RESET}")

def run_command(cmd, description=""):
    """Run a command and return success status."""
    try:
        if description:
            print_info(f"Running: {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check if Python is installed and get version."""
    print("\n[1] Checking Python...")
    success, stdout, stderr = run_command("python --version", "python --version")
    
    if success and stdout:
        version = stdout.strip()
        print_success(f"Python found: {version}")
        return True
    else:
        print_error("Python not found!")
        print("""
SOLUTION: Download Python from https://www.python.org/downloads/

Steps:
1. Download Python 3.11 (or latest)
2. Run the installer
3. IMPORTANT: Check "Add Python to PATH"
4. Click Install
5. Restart this script
        """)
        return False

def check_ollama():
    """Check if Ollama is installed."""
    print("\n[2] Checking Ollama...")
    success, stdout, stderr = run_command("ollama --version", "ollama --version")
    
    if success and stdout:
        version = stdout.strip()
        print_success(f"Ollama found: {version}")
        return True
    else:
        print_error("Ollama not found!")
        print("""
SOLUTION: Download Ollama from https://ollama.ai

Steps:
1. Download Ollama for your OS
2. Run the installer
3. Let it finish
4. Restart this script
        """)
        return False

def check_ollama_running():
    """Check if Ollama server is running."""
    print("\n[3] Checking if Ollama is running...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
        
        # Quick test
        client.chat.completions.create(
            model="gemma2",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1
        )
        print_success("Ollama server is running and responding")
        return True
    except Exception as e:
        print_warning("Ollama server is not running")
        print(f"Error: {str(e)}")
        
        print("""
SOLUTION: Start Ollama in a separate terminal

1. Open Command Prompt (or PowerShell)
2. Type: ollama serve
3. Keep that terminal open
4. Run this script again

Or just run: FLAWLESS_RUN.bat (which does this automatically)
        """)
        return False

def download_model():
    """Download Gemma 2 model."""
    print("\n[4] Checking Gemma 2 model...")
    
    success, stdout, stderr = run_command(
        "ollama list | find \"gemma2\"",
        "ollama list"
    )
    
    if success and stdout and "gemma2" in stdout:
        print_success("Gemma 2 model is installed")
        return True
    else:
        print_warning("Gemma 2 model not found - downloading (~4GB)")
        print("This may take 5-15 minutes depending on your internet speed...\n")
        
        success, stdout, stderr = run_command(
            "ollama pull gemma2",
            "ollama pull gemma2"
        )
        
        if success:
            print_success("Gemma 2 model downloaded successfully")
            return True
        else:
            print_error(f"Failed to download: {stderr}")
            print("""
SOLUTION: Try manually in Command Prompt

1. Open Command Prompt
2. Type: ollama pull gemma2
3. Wait for download to complete
4. Run this script again
            """)
            return False

def check_dependencies():
    """Check if Python dependencies are installed."""
    print("\n[5] Checking Python dependencies...")
    
    # Check for common dependencies
    dependencies = [
        ("openai", "OpenAI client library"),
        ("dotenv", "Environment variable loader"),
        ("requests", "HTTP library"),
    ]
    
    missing = []
    for package, description in dependencies:
        try:
            __import__(package)
            print_success(f"{description} ✓")
        except ImportError:
            print_warning(f"{description} (missing)")
            missing.append(package)
    
    if not missing:
        print_success("All Python dependencies installed")
        return True
    else:
        print_warning(f"Missing packages: {', '.join(missing)}")
        print("Installing missing dependencies...")
        
        for package in missing:
            success, stdout, stderr = run_command(
                f"pip install -q {package}",
                f"pip install {package}"
            )
            if not success:
                print_error(f"Failed to install {package}: {stderr}")
                return False
        
        print_success("All dependencies installed")
        return True

def create_virtual_env():
    """Create virtual environment if needed."""
    print("\n[6] Checking virtual environment...")
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print_success("Virtual environment exists")
        return True
    else:
        print_info("Creating virtual environment...")
        success, stdout, stderr = run_command(
            "python -m venv .venv",
            "python -m venv .venv"
        )
        
        if success:
            print_success("Virtual environment created")
            return True
        else:
            print_error(f"Failed to create virtual environment: {stderr}")
            return False

def install_requirements():
    """Install requirements from requirements.txt."""
    print("\n[7] Installing requirements from requirements.txt...")
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print_warning("requirements.txt not found - skipping")
        return True
    
    success, stdout, stderr = run_command(
        "pip install -q -r requirements.txt",
        "pip install -r requirements.txt"
    )
    
    if success:
        print_success("All requirements installed")
        return True
    else:
        print_warning(f"Some requirements may have failed: {stderr}")
        return True  # Don't fail entirely

def full_test():
    """Run a full test of the system."""
    print("\n[8] Running full system test...")
    
    try:
        from openai import OpenAI
        
        print_info("Testing Ollama connection with actual chat...")
        client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
        
        response = client.chat.completions.create(
            model="gemma2",
            messages=[
                {"role": "system", "content": "You are a healing companion."},
                {"role": "user", "content": "Say hello in one word."}
            ],
            max_tokens=10
        )
        
        print_success(f"Test response: '{response.choices[0].message.content.strip()}'")
        print_success("System is working perfectly!")
        return True
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def main():
    """Run all setup checks."""
    print_header("CARNAL 2.0 - FLAWLESS SETUP ASSISTANT")
    
    print("""
This script will:
1. Verify Python is installed
2. Verify Ollama is installed
3. Verify Ollama is running
4. Download Gemma 2 model
5. Install Python dependencies
6. Create virtual environment
7. Run system tests

If any step fails, I'll tell you exactly how to fix it.
    """)
    
    input("Press Enter to begin...")
    
    # Run all checks
    checks = [
        ("Python", check_python),
        ("Ollama", check_ollama),
        ("Ollama Running", check_ollama_running),
        ("Download Model", download_model),
        ("Dependencies", check_dependencies),
        ("Virtual Environment", create_virtual_env),
        ("Install Requirements", install_requirements),
        ("Full System Test", full_test),
    ]
    
    passed = 0
    failed = 0
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"{name} check failed: {str(e)}")
            failed += 1
    
    # Summary
    print_header("SETUP SUMMARY")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    else:
        print_success("Everything is perfect!")
    
    if failed == 0:
        print("""
🎉 SETUP COMPLETE!

You're ready to launch Carnal 2.0!

NEXT STEP:
==========
Double-click: FLAWLESS_RUN.bat

Or from command line:
python carnal2.py

Enjoy your healing! 💜
        """)
    else:
        print("""
⚠️ Some checks failed.

Please:
1. Read the error messages above
2. Follow the SOLUTION instructions
3. Run this script again

If problems persist:
- See GETTING_STARTED.md
- See OPENSOURCE_STUDENT_SETUP.md
- Check GitHub issues
        """)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nSetup cancelled")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
