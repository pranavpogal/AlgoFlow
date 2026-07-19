import os


# Tests must stay deterministic even when a developer's local backend/.env enables live Gemini.
os.environ["ENABLE_GEMINI_CLASSIFICATION"] = "false"
os.environ["ENABLE_GEMINI_HINTS"] = "false"
os.environ["ENABLE_LIVE_ADK"] = "false"
