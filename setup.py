#!/usr/bin/env python3
"""
AutoAV Setup Script
Installs dependencies and configures the environment
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_platform():
    """Check if platform is supported"""
    if platform.system() != "Darwin":
        print("❌ AutoAV is currently only supported on macOS")
        return False
    print("✅ macOS detected")
    return True


def install_homebrew():
    """Install Homebrew if not present"""
    if run_command("which brew", "Checking for Homebrew"):
        print("✅ Homebrew already installed")
        return True
    
    print("🔄 Installing Homebrew...")
    install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    return run_command(install_script, "Installing Homebrew")


def install_clamav():
    """Install ClamAV"""
    if run_command("which clamscan", "Checking for ClamAV"):
        print("✅ ClamAV already installed")
        return True
    
    return run_command("brew install clamav", "Installing ClamAV")


def update_clamav_database():
    """Update ClamAV virus definitions"""
    print("🔄 Updating ClamAV virus definitions...")
    return run_command("freshclam", "Updating ClamAV database")


def install_python_dependencies():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing Python dependencies")


def create_env_file():
    """Create .env file template"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_content = """# AutoAV Environment Variables

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override default model
# OPENAI_MODEL=gpt-4

# Optional: Override default configuration
# CONFIG_FILE=config.yaml

# Optional: Enable verbose logging
# LOG_LEVEL=DEBUG
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file template")
        print("⚠️  Please edit .env file and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def make_executable():
    """Make main.py executable"""
    try:
        os.chmod("main.py", 0o755)
        print("✅ Made main.py executable")
        return True
    except Exception as e:
        print(f"❌ Failed to make main.py executable: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 AutoAV Setup Script")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_platform():
        sys.exit(1)
    
    # Install dependencies
    if not install_homebrew():
        print("❌ Failed to install Homebrew")
        sys.exit(1)
    
    if not install_clamav():
        print("❌ Failed to install ClamAV")
        sys.exit(1)
    
    if not update_clamav_database():
        print("⚠️  Failed to update ClamAV database - you may need to run 'freshclam' manually")
    
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Setup configuration
    if not create_env_file():
        print("❌ Failed to create environment file")
        sys.exit(1)
    
    if not make_executable():
        print("⚠️  Failed to make main.py executable")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run: python main.py")
    print("3. Or run: ./main.py (if executable)")
    print("\nExample usage:")
    print("  python main.py")
    print("  python main.py --model gpt-3.5-turbo")
    print("  python main.py --verbose")


if __name__ == "__main__":
    main() 