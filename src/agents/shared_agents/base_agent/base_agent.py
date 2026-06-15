from abc import ABC, abstractmethod
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config

class BaseAgent(ABC):
    def __init__(self, system_prompt: str, temperature: float = 0.2):
        # Dynamically load configurations and setup GOOGLE_API_KEY
        self.config = Config.load_config()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.config.GEMINI_API_KEY,
            temperature=temperature
        )
        self.system_prompt = system_prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input_text}")
        ])

    def get_chain(self):
        """Returns the runnable LangChain sequence for this agent."""
        return self.prompt_template | self.llm

    @abstractmethod
    def run(self, *args, **kwargs):
        """Abstract execution method to be defined by each child agent."""
        pass
