import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

class LLMModel:
    def __init__(self, model_name="deepseek-r1-distill-llama-70b"):
        if not model_name:
            raise ValueError("Model is not defined.")
        self.model_name = model_name
        self.groq_model=ChatGroq(model=self.model_name)
        
    def get_model(self):
        return self.groq_model

if __name__ == "__main__":
    llm_instance = LLMModel()  
    llm_model = llm_instance.get_model()
    response=llm_model.invoke("hi")

    print(response)