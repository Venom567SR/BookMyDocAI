# BookMyDocAI 🏥

BookMyDocAI is a fully automated, end-to-end multi-agent AI system designed for seamless doctor appointment booking. Built with Flask and LangGraph, this system demonstrates sophisticated agent orchestration for handling medical appointments without human intervention.

## 🤖 Agent Architecture

Our system employs a hierarchical multi-agent structure with three specialized agents working in harmony:

1. **Supervisor Agent** 👨‍💼
   - Acts as the central coordinator
   - Routes requests to appropriate specialized agents
   - Makes routing decisions based on query analysis
   - Possible routing paths:
     - Information Node
     - Booking Node
     - FINISH (when task is complete)

2. **Information Agent** ℹ️
   - Handles doctor availability queries
   - Provides hospital-related FAQs
   - Has access to specialized tools:
     - `check_availability_by_doctor`
     - `check_availability_by_specialization`

3. **Booking Agent** 📅
   - Manages all appointment-related operations
   - Handles tools for:
     - `set_appointment`: Creating new appointments
     - `cancel_appointment`: Canceling existing appointments
     - `reschedule_appointment`: Modifying appointment dates

## 🔄 Workflow Process

1. **Initial Request Processing**
   - User query is received with an identification number
   - Supervisor agent analyzes the request

2. **Request Routing**
   - Supervisor determines appropriate specialized agent:
     - Information requests → Information Node
     - Booking operations → Booking Node
     - Completed tasks → FINISH

3. **Specialized Processing**
   - Information Node:
     - Processes availability checks
     - Handles hospital information queries
   - Booking Node:
     - Manages appointment operations
     - Processes date-time specifications
     - Handles booking confirmations

4. **Response Generation**
   - Formats tool responses into user-friendly messages
   - Provides booking references and confirmation details

## 🛠️ Technology Stack

- **Backend Framework:** Flask
- **AI Framework:** LangGraph
- **Agent Communication:** LangChain Core
- **State Management:** StateGraph
- **Tool Integration:** Custom Toolkit System

## 🚀 Getting Started

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Venom567SR/BookMyDocAI.git
   cd BookMyDocAI
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Required Dependencies:**
   ```python
   langchain_core
   langgraph
   typing_extensions
   flask
   ```

4. **Run the Application:**
   ```bash
   python app.py
   ```

## 🎥 Demo Video

Check out our demo video to see BookMyDocAI in action:

[Watch Demo Video](media/BookMyDocAI.mp4)

https://github.com/Venom567SR/BookMyDocAI/blob/main/media/BookMyDocAI.mp4

## 🌟 Key Features

- **Smart Request Routing:** Intelligent classification of user requests
- **Specialized Agent Handling:** Dedicated agents for specific tasks
- **Advanced Tool Integration:** Custom tools for each operation type
- **Human-Friendly Responses:** Automated formatting of technical responses
- **Robust Error Handling:** Graceful error management and recovery
- **Flexible Architecture:** Easy to extend with new capabilities

## 💡 Implementation Highlights

- **State Management:** Uses TypedDict for structured state handling
- **Message Formatting:** Automatic conversion of tool calls to human-readable messages
- **Date Processing:** Smart handling of various date-time formats
- **Agent Communication:** Structured message passing between agents

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT](LICENSE)

## 🤝 Related Projects

Part of the AI assistant family:
- [InsightAI](https://github.com/Venom567SR/InsightAI)
- [JobFitAI](https://github.com/Venom567SR/JobFitAI)
- [DiagnostAI](https://github.com/Venom567SR/DiagnostAI)
- [AutoSummaryAI](https://github.com/Venom567SR/AutoSummaryAI)

---

*Built with ❤️ by [Venom567SR](https://github.com/Venom567SR)*