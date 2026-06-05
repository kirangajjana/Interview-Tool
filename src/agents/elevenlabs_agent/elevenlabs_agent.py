import requests
import os
from src.config import Config

class ElevenLabsAgent:
    def __init__(self):
        self.config = Config.load_config()
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID", "")
        self.phone_number_id = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "o6qTxWUeRyzRYZyUNDVJ") # Default voice ID from config

    def trigger_outbound_call(self, to_number: str, candidate_name: str, company_name: str = "Hackthon") -> dict:
        """
        Triggers an outbound voice call using ElevenLabs Conversational AI
        via Twilio webhook integrations, passing required dynamic variables.
        """
        if not self.api_key or not self.agent_id or not self.phone_number_id:
            return {
                "success": False,
                "message": "Missing ElevenLabs credentials (API Key, Agent ID, or Phone Number ID) in environment configuration."
            }

        url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "agent_id": self.agent_id,
            "agent_phone_number_id": self.phone_number_id,
            "to_number": to_number,
            "conversation_initiation_client_data": {
                "type": "conversation_initiation_client_data",
                "dynamic_variables": {
                    "candidate_name": candidate_name,
                    "company_name": company_name,
                    "Hackthon": company_name,
                    "hackthon": company_name
                }
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Successfully initiated ElevenLabs outbound call to {to_number}.",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": f"ElevenLabs API error: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"HTTP request failed: {str(e)}"
            }

    def generate_tts_audio(self, text: str) -> bytes:
        """
        Synthesizes speech from text using ElevenLabs Text-to-Speech API.
        Useful as a direct audio preview in the browser.
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API Key is not configured.")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        data = {
            "text": text,
            "model_id": "eleven_flash_v2",
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"ElevenLabs TTS synthesis failed: {response.text}")
