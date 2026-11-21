"""
Protected Live AI Test Runner.
Ensures external AI credits are NEVER consumed automatically.
Requires:
  1. RUN_LIVE_AI_TESTS=true in environment.
  2. A configured API key or local endpoint for the active provider.
  3. Uses only minimal test payloads (1 small scene) to conserve credits.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import Config
from app.ai.provider_factory import AIProviderFactory
from app.ai.schemas import Stage1EpisodeSummary
from app.utils.logging import logger


def main():
    print("=" * 60)
    print("PROMOFINDER AI — PROTECTED LIVE AI TEST RUNNER")
    print("=" * 60)

    # 1. Guard check
    live_flag = os.getenv("RUN_LIVE_AI_TESTS", "").lower().strip()
    if live_flag not in ("true", "1", "yes"):
        print("\n[SKIPPED] Live AI tests are disabled by default to protect paid credits.")
        print("To run live tests explicitly, set:")
        print("  export RUN_LIVE_AI_TESTS=true")
        print("and configure your API key in .env, then re-run:")
        print("  python scripts/run_live_tests.py\n")
        sys.exit(0)

    # 2. Check provider and credentials
    provider_name = Config.AI_PROVIDER
    model_name = Config.AI_MODEL
    print(f"\nConfigured Provider: {provider_name}")
    print(f"Configured Model:    {model_name}")

    if provider_name == "mock":
        print("\n[NOTE] Active provider is 'mock'. Switching to live provider requires updating AI_PROVIDER in .env.")
        sys.exit(0)

    key = Config.get_api_key_for_provider(provider_name)
    if not key and provider_name not in ("ollama",):
        print(f"\n[ERROR] No API key configured for provider '{provider_name}'.")
        print(f"Please set {provider_name.upper()}_API_KEY in .env before executing live tests.")
        sys.exit(1)

    # 3. Connection check
    print("\nAttempting lightweight connection check...")
    provider = AIProviderFactory.get_provider(provider_name, model_name, api_key=key)
    connected, msg = provider.check_connection()
    if not connected:
        print(f"[FAILED] Connection check failed: {msg}")
        print("Notice: Credential presence does not guarantee remaining account balance or quota.")
        sys.exit(1)
    print(f"[SUCCESS] {msg}")

    # 4. Minimal test payload
    print("\nRunning single minimal test call (Micro-payload: 1 sentence)...")
    try:
        test_prompt = "Episode Number: 1\nTitle: Test\nLogline: Betrayal at altar.\nScreenplay Content:\nJULIANA: Why are you doing this?\nGERALD: Because I changed my mind."
        output = provider.generate_structured_output(
            prompt=test_prompt,
            schema=Stage1EpisodeSummary,
            system_prompt="Extract structured episode summary."
        )
        print("[SUCCESS] Live AI call succeeded. Structured response validated:")
        print(f"  Episode: {output.episode_number}")
        print(f"  Logline: {output.logline}")
        print(f"  Key conflicts: {output.key_conflicts}")
        print("\nLive test complete! No further API calls were made.")
    except Exception as e:
        print(f"[ERROR] Live test call failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
