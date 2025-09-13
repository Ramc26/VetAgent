from crewai import Task
from agents import vet_appointment_agent, data_extraction_agent

confirmation_task = Task(
    description="""You are a friendly veterinary appointment coordinator. Based on what information has already been collected, decide what to ask next.

DETAILS ALREADY COLLECTED:
{details_collected}

CONVERSATION HISTORY:
{conversation_context}

CONVERSATION STAGE: {conversation_stage}

Follow this decision logic:
1. If no guardian name is collected: Ask for the guardian's name in a friendly way
2. If guardian name known but no pet details: Ask about the pet's name and date of birth or age
3. If Pet's name and dob known but no Species and breed: Ask about the species, and breed
4. If pet details known but no appointment: Ask about the appointment date and time
5. If all details collected(Gaurdian anme, pet's name, dob/age, species and breed, Appointment time and date) but not confirmed: Summarize all details and ask for confirmation
6. If confirmed: Ask for any questions or concerns before ending the call.
5. If No Questions or concerns: Thank them warmly, confirm the appointment is set, and say goodbye

IMPORTANT: When confirming, explicitly state that the appointment is confirmed to trigger the confirmation flag.

Be natural, friendly, and conversational. Use the person's and pet's names when you know them.
Only ask for information that's missing. Don't repeat questions for information already provided.

Your response should be a single, friendly, conversational sentence or question.""",
    expected_output="A natural, friendly conversational response that moves the appointment confirmation forward.",
    agent=vet_appointment_agent
)

data_extraction_task = Task(
    description="""Analyze the conversation carefully and extract ONLY the specific information mentioned. Be very precise.

CONVERSATION HISTORY:
{conversation_context}

CURRENT DETAILS COLLECTED:
{current_details}

Extract ONLY the following information if explicitly mentioned:
- guardian_name: ONLY the human's name (not pet name)
- pet_name: ONLY the pet's name (not human name)  
- pet_species: ONLY the animal type (dog, cat, etc.)
- pet_breed: ONLY the specific breed name
- pet_dob: ONLY the date of birth or age
- appointment_date: ONLY the appointment date
- appointment_time: ONLY the appointment time

CRITICAL RULES:
1. guardian_name and pet_name MUST be different. If they're the same, you made an error.
2. pet_species should be simple: "dog", "cat", "bird", etc.
3. pet_breed should be the specific breed: "German Shepherd", "Bengal", "Golden Retriever", etc.
4. If someone says "it's a dog" - species is "dog", breed is empty until specified.
5. If someone says "German Shepherd" - species is "dog", breed is "German Shepherd".

Determine the current conversation stage from:
- greeting: Just started, no details collected
- collecting_guardian: Getting guardian name
- collecting_pet_details: Getting pet information  
- collecting_appointment: Getting appointment details
- confirming: Confirming all details
- concluded: All details confirmed, ready to end call

Return ONLY a valid JSON object with this exact structure:
{
  "extracted_details": {
    "guardian_name": "value or empty",
    "pet_name": "value or empty", 
    "pet_species": "value or empty",
    "pet_breed": "value or empty",
    "pet_dob": "value or empty",
    "appointment_date": "value or empty",
    "appointment_time": "value or empty"
  },
  "conversation_stage": "stage_name"
}""",
    expected_output="A valid JSON object with accurately extracted details and conversation stage",
    agent=data_extraction_agent
)