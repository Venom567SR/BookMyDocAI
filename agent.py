from typing import Literal, List, Any
from langchain_core.tools import tool
from langgraph.types import Command
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from prompt_lib.prompt import system_prompt
from utils.llm import LLMModel
from toolkit.toolkits import *

class Router(TypedDict):
    next: Literal["information_node","booking_node","FINISH"]
    reasoning: str

class AgentState(TypedDict):
    messages: Annotated[list[Any], add_messages]
    id_number: int
    next:str
    query: str
    current_reasoning: str

class DoctorAppointmentAgent:
    def __init__(self):
        llm_model = LLMModel()
        self.llm_model=llm_model.get_model()
    
    def supervisor_node(self, state:AgentState) -> Command[Literal['information_node', 'booking_node', '__end__']]:
        print("**************************below is my state right after entering****************************")
        print(state)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"user's identification number is {state['id_number']}"},
        ] + state["messages"]
        
        print("***********************this is my message*****************************************")
        print(messages)
        
        query = ''
        if len(state['messages']) == 1:
            query = state['messages'][0].content
        
        print("************below is my query********************")    
        print(query)
        
        # Modify this part - directly prompt the model instead of using structured_output
        tools_prompt = """
        Based on the user's query, determine which specialized node should handle this request.
        If the user is asking about doctor availability or hospital information, respond with "information_node".
        If the user is trying to book, cancel, or reschedule an appointment, respond with "booking_node".
        If the query has been completely answered or no further action is needed, respond with "FINISH".
        
        Your response should be in this format:
        Next: [information_node/booking_node/FINISH]
        Reasoning: [your reasoning for the selection]
        """
        
        # Create chat messages for prompting
        prompt_messages = messages + [{"role": "system", "content": tools_prompt}]
        
        # Make a regular call to the model without structured output
        response_text = self.llm_model.invoke(prompt_messages)
        
        # Parse the response to extract next and reasoning
        response_text = response_text.content if hasattr(response_text, 'content') else str(response_text)
        
        # Extract the next node and reasoning from the response
        next_node = None
        reasoning = ""
        
        for line in response_text.split('\n'):
            if line.lower().startswith('next:'):
                next_node = line.split(':', 1)[1].strip()
            elif line.lower().startswith('reasoning:'):
                reasoning = line.split(':', 1)[1].strip()
        
        # Default to booking_node if parsing fails
        if not next_node:
            next_node = "booking_node"
            reasoning = "Default routing due to parsing issue."
        
        goto = next_node
        
        print("********************************this is my goto*************************")
        print(goto)
        
        print("********************************")
        print(reasoning)
            
        if goto == "FINISH":
            goto = END
            
        print("**************************below is my state****************************")
        print(state)
        
        if query:
            return Command(goto=goto, update={'next': goto, 
                                            'query': query, 
                                            'current_reasoning': reasoning,
                                            'messages': [HumanMessage(content=f"user's identification number is {state['id_number']}")]
                            })
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': reasoning}
                    )
    
    def information_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        print("*****************called information node************")
        
        system_prompt = "You are specialized agent to provide information related to availability of doctors or any FAQs related to hospital based on the query. You have access to the tool.\n Make sure to ask user politely if you need any further information to execute the tool.\n For your information, Always consider current year is 2024."
        
        system_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        system_prompt
                    ),
                    (
                        "placeholder", 
                        "{messages}"
                    ),
                ]
            )
        
        information_agent = create_react_agent(model=self.llm_model, tools=[check_availability_by_doctor,check_availability_by_specialization], prompt=system_prompt)
        
        result = information_agent.invoke(state)
        
        return Command(
            update={
                "messages": state["messages"] + [
                    AIMessage(content=result["messages"][-1].content, name="information_node"),
                ]
            },
            goto="supervisor",
        )

    def booking_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        print("*****************called booking node************")
        
        system_prompt = "You are specialized agent to set, cancel or reschedule appointment based on the query. You have access to the tool.\n Make sure to ask user politely if you need any further information to execute the tool.\n For your information, Always consider current year is 2024."
        
        system_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        system_prompt
                    ),
                    (
                        "placeholder", 
                        "{messages}"
                    ),
                ]
            )
            
        booking_agent = create_react_agent(model=self.llm_model, tools=[set_appointment, cancel_appointment, reschedule_appointment], prompt=system_prompt)

        result = booking_agent.invoke(state)
        
        return Command(
            update={
                "messages": state["messages"] + [
                    AIMessage(content=result["messages"][-1].content, name="booking_node"),
                ]
            },
            goto="supervisor",
        )

    def workflow(self):
        self.graph = StateGraph(AgentState)
        self.graph.add_node("supervisor", self.supervisor_node)
        self.graph.add_node("information_node", self.information_node)
        self.graph.add_node("booking_node", self.booking_node)
        self.graph.add_edge(START, "supervisor")
        self.app = self.graph.compile()
        return self.app