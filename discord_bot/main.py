#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from discord_bot.bot import run_bot

def main():
    try:
        print("Starting Claude Assistant Discord Bot...")
        print(f"Python version: {sys.version}")

        required_env_vars = [
            'DISCORD_BOT_TOKEN',
            'VITE_SUPABASE_URL',
            'VITE_SUPABASE_ANON_KEY'
        ]

        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
            print("\nPlease set the following in your .env file:")
            for var in missing_vars:
                print(f"  {var}=your_value_here")
            sys.exit(1)

        run_bot()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
