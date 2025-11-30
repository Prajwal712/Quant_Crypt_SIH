#!/usr/bin/env python3
"""
Setup script for Quantum Email Encryption System
Installs dependencies and verifies the installation
"""

import subprocess
import sys
import os

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}")
        return False

    print("✓ Python version is compatible")
    return True

def install_requirements():
    """Install required packages"""
    print_header("Installing Dependencies")

    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')

    if not os.path.exists(requirements_file):
        print("❌ Error: requirements.txt not found")
        return False

    print("Installing packages from requirements.txt...")
    print("This may take a few minutes...\n")

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            requirements_file
        ])
        print("\n✓ All dependencies installed successfully")
        return True

    except subprocess.CalledProcessError:
        print("\n❌ Error: Failed to install dependencies")
        print("   Try running manually: pip install -r requirements.txt")
        return False

def verify_imports():
    """Verify that all modules can be imported"""
    print_header("Verifying Installation")

    modules = [
        ("cryptography", "Cryptography library"),
        ("flask", "Flask web framework"),
        ("google.auth", "Google Auth"),
        ("googleapiclient", "Google API Client"),
    ]

    all_ok = True

    for module, name in modules:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - Import failed")
            all_ok = False

    return all_ok

def verify_project_structure():
    """Verify project directory structure"""
    print_header("Verifying Project Structure")

    required_dirs = [
        "src",
        "src/qkd",
        "src/key_management",
        "src/cryptography",
        "src/email_engine",
        "src/GUI",
        "examples"
    ]

    required_files = [
        "src/qkd/qkd_simulator.py",
        "src/key_management/key_manager.py",
        "src/cryptography/security_levels.py",
        "src/email_engine/quantum_email.py",
        "src/GUI/quantum_email_gui.py",
        "examples/example_usage.py"
    ]

    all_ok = True

    print("Checking directories...")
    for directory in required_dirs:
        path = os.path.join(os.path.dirname(__file__), directory)
        if os.path.exists(path):
            print(f"✓ {directory}/")
        else:
            print(f"✗ {directory}/ - Missing")
            all_ok = False

    print("\nChecking files...")
    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - Missing")
            all_ok = False

    return all_ok

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")

    directories = [
        "key_store",
        "logs"
    ]

    for directory in directories:
        path = os.path.join(os.path.dirname(__file__), directory)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"✓ Created {directory}/")
        else:
            print(f"✓ {directory}/ already exists")

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")

    print("""
    Your Quantum Email Encryption System is ready to use!

    Next Steps:
    ──────────────────────────────────────────────────────────

    1. Quick Start:
       python main.py

    2. Launch GUI:
       cd src/GUI
       python quantum_email_gui.py

    3. Run Examples:
       cd examples
       python example_usage.py

    4. Read Documentation:
       - README.md         : Overview
       - QUICKSTART.md     : Quick start guide
       - DOCUMENTATION.md  : Technical details
       - SYSTEM_SUMMARY.md : System summary

    5. Gmail Integration (Optional):
       - Follow instructions in QUICKSTART.md
       - Set up Google Cloud credentials
       - Place credentials.json in src/email_engine/

    ──────────────────────────────────────────────────────────

    For help, see: README.md or DOCUMENTATION.md

    SIH 2024 - Quantum Email Encryption System
    """)

def main():
    """Main setup function"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     QUANTUM EMAIL ENCRYPTION SYSTEM - SETUP               ║
    ║     SIH 2024                                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Verify project structure
    if not verify_project_structure():
        print("\n❌ Project structure verification failed")
        print("   Make sure you're running this from the project root directory")
        sys.exit(1)

    # Ask user if they want to install dependencies
    print("\nThis script will:")
    print("  1. Install Python dependencies")
    print("  2. Verify installation")
    print("  3. Create necessary directories")
    print()

    response = input("Continue? (y/n): ").strip().lower()

    if response != 'y':
        print("\nSetup cancelled.")
        sys.exit(0)

    # Install requirements
    if not install_requirements():
        sys.exit(1)

    # Verify imports
    if not verify_imports():
        print("\n❌ Installation verification failed")
        print("   Some packages failed to import")
        sys.exit(1)

    # Create directories
    create_directories()

    # Print next steps
    print_next_steps()

if __name__ == '__main__':
    main()
