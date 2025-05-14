from typing import Literal, List, Any, Dict
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
import re
import json

class Router(TypedDict):
    next: Literal["information_node", "booking_node", "FINISH"]
    reasoning: str

class AgentState(TypedDict):
    messages: Annotated[list[Any], add_messages]
    id_number: int
    next: str
    query: str
    current_reasoning: str

def format_tool_call_to_human_message(tool_call_content: str) -> str:
    """Formats a tool call JSON string into a user-friendly message."""
    try:
        # Clean the tool call string by removing any markers
        clean_json = (tool_call_content
                     .replace("<tool_call>", "")
                     .replace("<｜tool▁calls▁end｜>", "")
                     .replace("<｜tool▓l▁calls▓end▓｜>", ""))
        
        # Parse the JSON data
        tool_data = json.loads(clean_json)
        
        # Extract tool name and arguments
        tool_name = tool_data.get("name", "")
        args = tool_data.get("arguments", {})
        
        # Format response based on tool type
        if tool_name == "set_appointment":
            doctor_name = args.get("doctor_name", "").title()
            
            # Handle different formats of id_number (either direct value or nested object)
            id_number = args.get("id_number")
            if isinstance(id_number, dict):
                id_number = id_number.get("id")
                
            # Extract date information
            date_info = args.get("desired_date", {}).get("date", "")
            
            # Format into a human-readable message
            return (f"Your appointment with Dr. {doctor_name} has been successfully scheduled for {date_info}. "
                    f"Your booking reference number is: #{id_number}. "
                    f"Please arrive 15 minutes before your appointment time. Thank you!")
            
        elif tool_name == "cancel_appointment":
            appointment_id = args.get("appointment_id")
            return f"Your appointment (ID: {appointment_id}) has been successfully cancelled. Thank you."
            
        elif tool_name == "reschedule_appointment":
            appointment_id = args.get("appointment_id")
            new_date = args.get("new_date", {}).get("date", "")
            return (f"Your appointment (ID: {appointment_id}) has been rescheduled to {new_date}. "
                    f"Please arrive 15 minutes before your appointment time. Thank you!")
            
        elif tool_name == "check_availability_by_doctor":
            doctor_name = args.get("doctor_name", "").title()
            date = args.get("date", "")
            return f"Available time slots for Dr. {doctor_name} on {date} have been checked."
            
        elif tool_name == "check_availability_by_specialization":
            specialization = args.get("specialization", "").title()
            date = args.get("date", "")
            return f"Available time slots for {specialization} specialists on {date} have been checked."
        
        # Generic response if tool type isn't recognized
        return "Your request has been processed successfully. Thank you for using our service."
        
    except Exception as e:
        # If there's an error parsing the tool call, return the original content
        return tool_call_content

class DoctorAppointmentAgent:
    def __init__(self):
        llm_model = LLMModel()
        self.llm_model = llm_model.get_model()
    
    def supervisor_node(self, state: AgentState) -> Command[Literal['information_node', 'booking_node', '__end__']]:
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
                                            # Append the ID message rather than replacing all messages
                                            'messages': state["messages"] + [HumanMessage(content=f"user's identification number is {state['id_number']}")]
                            })
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': reasoning}
                    )
    
    def information_node(self, state: AgentState) -> Command[Literal['supervisor']]:
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
        
        information_agent = create_react_agent(model=self.llm_model, tools=[check_availability_by_doctor, check_availability_by_specialization], prompt=system_prompt)
        
        result = information_agent.invoke(state)
        
        # Get the content from the last message
        content = result["messages"][-1].content
        
        # Check if the content looks like a tool call and format it if needed
        if "<tool_call>" in content or "<｜tool▁calls▁end｜>" in content or "<｜tool▓l▁calls▓end▓｜>" in content:
            content = format_tool_call_to_human_message(content)
        
        return Command(
            update={
                "messages": state["messages"] + [
                    AIMessage(content=content, name="information_node"),
                ]
            },
            goto="supervisor",
        )

    def booking_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        print("*****************called booking node************")
        
        # Preprocess any messages in the state to handle date format with "at"
        processed_messages = []
        
        for message in state["messages"]:
            if isinstance(message, HumanMessage):
                content = message.content
                # Check if there's a date pattern with "at" in it
                date_pattern = r'(\d{2}-\d{2}-\d{4})\s+at\s+(\d{2}:\d{2})'
                updated_content = re.sub(date_pattern, r'\1 \2', content)
                processed_messages.append(HumanMessage(content=updated_content))
            else:
                processed_messages.append(message)
        
        # Replace the original messages with processed ones
        processed_state = dict(state)
        processed_state["messages"] = processed_messages
        
        # Updated system prompt to handle date format with "at"
        system_prompt = "You are specialized agent to set, cancel or reschedule appointment based on the query. You have access to the tool.\n Make sure to ask user politely if you need any further information to execute the tool.\n For your information, Always consider current year is 2024.\n Note: If the user provides a date format like '22-05-2024 at 14:30', please convert it to '22-05-2024 14:30' format before processing."
        
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

        try:
            result = booking_agent.invoke(processed_state)
            
            # Get the content from the last message
            content = result["messages"][-1].content if result["messages"] else "No response received."
            
            # Check if the content looks like a tool call and format it if needed
            if content and ("<tool_call>" in content or "<｜tool▁calls▁end｜>" in content or "<｜tool▓l▁calls▓end▓｜>" in content):
                content = format_tool_call_to_human_message(content)
            
            # If content is empty or None, provide a default message
            if not content:
                content = "I apologize, but I'm having trouble processing your request. Could you provide more details about your booking needs?"
               
        except Exception as e:
            content = f"I apologize for the inconvenience. An error occurred while processing your request: {str(e)}"
            print(f"Error in booking_node: {str(e)}")

        return Command(
            update={
                "messages": state["messages"] + [
                    AIMessage(content=content, name="booking_node"),
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