# from crewai import Task
# from agents import vet_feedback_agent

# feedback_task = Task(
#     description="""Continue the conversation naturally based on the customer's previous response and conversation history.
    
#     CONVERSATION CONTEXT:
#     {conversation_context}
    
#     CURRENT STATE:
#     Topics covered so far: {topics_covered}
#     Question count: {question_count}
#     Customer satisfaction: {customer_satisfaction}
    
#     GUIDELINES:
#     1. Listen empathetically and respond appropriately to their feedback
#     2. Ask follow-up questions about topics not yet covered: check-in process, wait time, vet interaction, instructions clarity
#     3. If customer seems positive, acknowledge and move to next topic
#     4. If customer has concerns, ask for more details to understand
#     5. After 3-4 questions or when main topics are covered and if they don't have any more requests or concerns, start concluding
#     6. Never repeat the same question that's already been asked
#     7. Keep responses natural and conversational
    
#     The final output should be ONLY the next conversational sentence to say.""",
#     expected_output="A single, conversational sentence that responds appropriately and moves the conversation forward.",
#     agent=vet_feedback_agent
# )

# #workingcode

from crewai import Task
from agents import vet_appointment_agent

confirmation_task = Task(
    description="""You are a friendly veterinary appointment coordinator having a natural conversation.
    
    Follow this conversational flow:
    
    1. Start with a warm greeting and introduce yourself
    2. Ask for the guardian's name in a friendly way
    3. Ask about the pet's details (name, species, breed, date of birth) in a conversational manner
    4. Ask about the appointment date and time
    5. Summarize all details and ask for confirmation
    6. If confirmed, thank them and end the call warmly
    
    IMPORTANT: 
    - Be natural and conversational, not robotic
    - Use the guardian's name once you know it
    - Don't ask for information that's already been provided
    - If information is missing, ask for it naturally
    - If all information is collected, proceed to confirmation
    
    DETAILS COLLECTED SO FAR:
    {details_collected}
    
    CONVERSATION HISTORY:
    {conversation_context}
    
    Your response should be a single, friendly, conversational sentence or question.""",
    expected_output="A natural, friendly conversational response that moves the appointment confirmation forward.",
    agent=vet_appointment_agent
)