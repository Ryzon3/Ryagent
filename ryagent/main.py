import asyncio
import sys
import os
from pathlib import Path

from .app.integrated_app import RyAgentApp
from .cfg.config import load_config


def main():
    """Main entry point for RyAgent CLI."""
    try:
        config = load_config()
        
        if not config.model.api_key:
            print("Error: OPENAI_API_KEY environment variable not set")
            print("Please set your OpenAI API key:")
            print("  export OPENAI_API_KEY='your-api-key-here'")
            sys.exit(1)
        
        os.chdir(config.app.workspace)
        
        app = RyAgentApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\nRyAgent terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting RyAgent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()