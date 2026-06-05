import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
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
        """Loads and validates the current configurations."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "Gemini_API_Key is missing in your .env file. "
                "Please configure it to proceed."
            )
        
        # Set standard LangChain Google API Key environment variable
        os.environ["GOOGLE_API_KEY"] = cls.GEMINI_API_KEY
        return cls()
