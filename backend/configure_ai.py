#!/usr/bin/env python3
"""
Interactive script to help configure AI/LLM settings for Pathavana.
"""

import os
import sys
from pathlib import Path
import shutil
from typing import Optional


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * len(text))


def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")


def get_env_path() -> Path:
    """Get the path to the .env file."""
    return Path(__file__).parent / ".env"


def backup_env_file():
    """Create a backup of the existing .env file."""
    env_path = get_env_path()
    if env_path.exists():
        backup_path = env_path.with_suffix(".env.backup")
        shutil.copy2(env_path, backup_path)
        print_success(f"Backed up existing .env to {backup_path.name}")


def read_env_file() -> dict:
    """Read the current .env file."""
    env_vars = {}
    env_path = get_env_path()
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    return env_vars


def write_env_file(env_vars: dict):
    """Write the updated .env file."""
    env_path = get_env_path()
    
    # Read the original file to preserve comments and order
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add the LLM configuration
    updated = False
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_vars:
                new_lines.append(f'{key}="{env_vars[key]}"\n')
                del env_vars[key]
                updated = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Add any remaining new variables
    if env_vars:
        new_lines.append("\n# AI/LLM Configuration (added by configure_ai.py)\n")
        for key, value in env_vars.items():
            new_lines.append(f'{key}="{value}"\n')
    
    # Write the file
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print_success("Updated .env file with new configuration")


def configure_openai() -> dict:
    """Configure OpenAI settings."""
    print_header("OpenAI Configuration")
    
    print("You'll need an API key from: https://platform.openai.com/api-keys")
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print_error("API key cannot be empty")
        return {}
    
    print("\nAvailable models:")
    print("1. gpt-3.5-turbo (Fastest, most economical)")
    print("2. gpt-4 (Most capable)")
    print("3. gpt-4-turbo (Fast and capable)")
    
    model_choice = input("\nSelect model (1-3) [default: 1]: ").strip() or "1"
    
    models = {
        "1": "gpt-3.5-turbo",
        "2": "gpt-4",
        "3": "gpt-4-turbo"
    }
    
    model = models.get(model_choice, "gpt-3.5-turbo")
    
    return {
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": api_key,
        "LLM_MODEL": model
    }


def configure_azure_openai() -> dict:
    """Configure Azure OpenAI settings."""
    print_header("Azure OpenAI Configuration")
    
    print("You'll need to set up Azure OpenAI in the Azure Portal first.")
    print("Required information:")
    print("- API Key from your Azure OpenAI resource")
    print("- Endpoint URL (e.g., https://your-resource.openai.azure.com/)")
    print("- Deployment name from Azure AI Studio")
    
    api_key = input("\nEnter your Azure OpenAI API key: ").strip()
    endpoint = input("Enter your endpoint URL: ").strip()
    deployment = input("Enter your deployment name: ").strip()
    
    if not all([api_key, endpoint, deployment]):
        print_error("All fields are required")
        return {}
    
    # Ensure endpoint has trailing slash
    if not endpoint.endswith('/'):
        endpoint += '/'
    
    return {
        "LLM_PROVIDER": "azure_openai",
        "AZURE_OPENAI_API_KEY": api_key,
        "AZURE_OPENAI_ENDPOINT": endpoint,
        "AZURE_OPENAI_DEPLOYMENT_NAME": deployment,
        "AZURE_OPENAI_API_VERSION": "2024-02-01"
    }


def configure_anthropic() -> dict:
    """Configure Anthropic Claude settings."""
    print_header("Anthropic Claude Configuration")
    
    print("You'll need an API key from: https://console.anthropic.com/")
    api_key = input("Enter your Anthropic API key: ").strip()
    
    if not api_key:
        print_error("API key cannot be empty")
        return {}
    
    print("\nAvailable models:")
    print("1. claude-3-haiku-20240307 (Fastest)")
    print("2. claude-3-sonnet-20240229 (Balanced)")
    print("3. claude-3-opus-20240229 (Most capable)")
    
    model_choice = input("\nSelect model (1-3) [default: 2]: ").strip() or "2"
    
    models = {
        "1": "claude-3-haiku-20240307",
        "2": "claude-3-sonnet-20240229",
        "3": "claude-3-opus-20240229"
    }
    
    model = models.get(model_choice, "claude-3-sonnet-20240229")
    
    return {
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": api_key,
        "LLM_MODEL": model
    }


def main():
    """Main configuration flow."""
    print_header("Pathavana AI Configuration Helper")
    
    # Check if .env exists
    env_path = get_env_path()
    if not env_path.exists():
        print_warning(".env file not found. Creating from .env.example...")
        example_path = env_path.parent / ".env.example"
        if example_path.exists():
            shutil.copy2(example_path, env_path)
            print_success("Created .env from .env.example")
        else:
            print_error(".env.example not found. Please create .env manually.")
            return
    
    # Backup existing file
    backup_env_file()
    
    # Read current configuration
    current_env = read_env_file()
    current_provider = current_env.get("LLM_PROVIDER", "none")
    
    print(f"\nCurrent LLM Provider: {current_provider}")
    
    # Choose provider
    print("\nAvailable LLM Providers:")
    print("1. OpenAI (Recommended for quick setup)")
    print("2. Azure OpenAI")
    print("3. Anthropic Claude")
    print("4. Skip (keep current configuration)")
    
    choice = input("\nSelect provider (1-4): ").strip()
    
    config = {}
    
    if choice == "1":
        config = configure_openai()
    elif choice == "2":
        config = configure_azure_openai()
    elif choice == "3":
        config = configure_anthropic()
    elif choice == "4":
        print_info("Keeping current configuration")
        return
    else:
        print_error("Invalid choice")
        return
    
    if not config:
        print_error("Configuration failed")
        return
    
    # Add common LLM settings
    print("\n" + Colors.OKCYAN + "Additional Settings" + Colors.ENDC)
    
    # Temperature
    temp = input("Model temperature (0.0-1.0) [default: 0.7]: ").strip()
    config["LLM_TEMPERATURE"] = temp if temp else "0.7"
    
    # Max tokens
    max_tokens = input("Max response tokens [default: 2000]: ").strip()
    config["LLM_MAX_TOKENS"] = max_tokens if max_tokens else "2000"
    
    # Streaming
    streaming = input("Enable streaming responses? (yes/no) [default: yes]: ").strip().lower()
    config["LLM_STREAMING_ENABLED"] = "true" if streaming != "no" else "false"
    
    # Update .env file
    current_env.update(config)
    write_env_file(config)
    
    print_header("Configuration Complete!")
    
    print("\nNext steps:")
    print("1. Restart the backend server for changes to take effect")
    print("2. Run 'python test_ai_agent_fix.py' to test the configuration")
    print("3. Check logs/app.log if you encounter any issues")
    
    print_info("\nRemember to keep your API keys secure and never commit them to git!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        sys.exit(1)