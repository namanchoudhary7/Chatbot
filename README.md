Agent execution after user input:
    [User Input] 
     │
     ▼
    1. Agent Invocation (agent.invoke) ──► Loads history from InMemorySaver (thread_id)
     │
     ▼
    2. State Resolution ──────────────────► Merges incoming message into State ["messages"]
     │
     ▼
    3. Middleware Hook (@before_model) ──► Runs trim_messages() ──► Updates State
     │
     ▼
    4. Model Call (Gemini) ───────────────► Receives trimmed history + system_prompt
     │
     ▼
    5. Persistence & Output ──────────────► Saves response to Checkpointer ──► Prints to Console