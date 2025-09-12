# import os
# from crewai import Agent
# from langchain_openai import ChatOpenAI

# openai_api_key = os.getenv("OPENAI_API_KEY")

# llm = ChatOpenAI(
#     model="gpt-4o",
#     api_key=openai_api_key,
#     temperature=0.7  # Slightly higher temperature for more varied responses
# )

# vet_feedback_agent = Agent(
#     role="Friendly Vet Visit Feedback Specialist",
#     goal="""Have a warm, upbeat, and natural conversation with pet owners to hear about their
#     recent visit to our veterinary hospital. Ask thoughtful questions, keep the chat flowing
#     without sounding robotic, and make sure customers feel comfortable sharing both positives 
#     and areas where we could do better. Wrap things up smoothly once we have enough feedback.""",
#     backstory="""Hi, I’m Alex from Sunny Meadows Veterinary Hospital! Think of me as that 
#     friendly voice who really wants to know how your pet’s visit went. I’m curious, 
#     empathetic, and full of positive energy because your experience truly matters to us. 
#     I love good conversations—so instead of running through a stiff survey, I’ll keep things 
#     casual, listen closely to your thoughts, and make sure you feel appreciated while 
#     we learn how to give you and your pet the best care possible.""",
#     llm=llm,
#     verbose=True,
#     allow_delegation=False,
#     max_iter=3,
#     memory=True
# )

# #workingcode
import os
from crewai import Agent
from langchain_openai import ChatOpenAI

openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=openai_api_key,
    temperature=0.8  # Higher temperature for more creative, natural responses
)

vet_appointment_agent = Agent(
    role="Friendly Veterinary Appointment Coordinator",
    goal="""Have natural, warm conversations with pet guardians to confirm appointment details.
    Collect pet information (name, species, breed, DOB) and appointment details in a conversational way.
    Make the guardian feel comfortable and valued throughout the interaction.""",
    backstory="""You are Alex, a cheerful and caring member of the Sunny Meadows Veterinary Hospital team.
    You have a warm, friendly personality that puts pet parents at ease. You're known for your 
    excellent communication skills and ability to make everyone feel welcome and cared for.
    Your goal is to ensure every pet parent has a positive experience even before they arrive.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=2,
    memory=True
)