import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the project root (where .env lives) regardless of cwd
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env", override=True)

class Config:
    # All values are read AFTER load_dotenv() so they are never None
    GEMINI_API_KEY = os.getenv("Gemini_API_Key")

    # SMTP configurations for sending notifications
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL")
    SMTP_SENDER_PASSWORD = os.getenv("SMTP_SENDER_PASSWORD")

    # ElevenLabs Voice Calling & Synthesis configurations
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
    ELEVENLABS_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    @classmethod
    def load_config(cls):
        """Reloads env and returns a validated Config instance."""
        # Re-load .env each time so hot-reload in Streamlit picks up changes
        load_dotenv(dotenv_path=_PROJECT_ROOT / ".env", override=True)

        # Refresh class-level attributes after re-loading
        cls.GEMINI_API_KEY         = os.getenv("Gemini_API_Key")
        cls.SMTP_SERVER            = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        cls.SMTP_PORT              = int(os.getenv("SMTP_PORT", "587"))
        cls.SMTP_SENDER_EMAIL      = os.getenv("SMTP_SENDER_EMAIL")
        cls.SMTP_SENDER_PASSWORD   = os.getenv("SMTP_SENDER_PASSWORD")
        cls.ELEVENLABS_API_KEY     = os.getenv("ELEVENLABS_API_KEY")
        cls.ELEVENLABS_AGENT_ID    = os.getenv("ELEVENLABS_AGENT_ID")
        cls.ELEVENLABS_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
        cls.ELEVENLABS_VOICE_ID    = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "Gemini_API_Key is missing in your .env file. "
                "Please configure it to proceed."
            )

        # Set standard LangChain Google API Key environment variable
        os.environ["GOOGLE_API_KEY"] = cls.GEMINI_API_KEY
        return cls()
