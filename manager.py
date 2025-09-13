import re
import json
from crewai import Crew, Process
from agents import data_extraction_agent
from tasks import data_extraction_task

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.conversation_states = {}
        self.data_extraction_crew = Crew(
            agents=[data_extraction_agent],
            tasks=[data_extraction_task],
            process=Process.sequential,
            verbose=False
        )

    def initialize_conversation(self, call_sid):
        self.conversations[call_sid] = []
        self.conversation_states[call_sid] = {
            "stage": "greeting",
            "details_collected": {
                "guardian_name": "",
                "pet_name": "",
                "pet_species": "",
                "pet_breed": "",
                "pet_dob": "",
                "appointment_date": "",
                "appointment_time": "",
                "appointment_confirmed": False
            },
            "question_count": 0
        }

    def update_conversation(self, call_sid, role, content):
        if call_sid not in self.conversations:
            self.initialize_conversation(call_sid)
        
        self.conversations[call_sid].append({"role": role, "content": content})
        
        if role == "customer":
            self._extract_details_with_agent(call_sid)

    def _extract_details_with_agent(self, call_sid):
        """Use the data extraction agent to analyze the conversation and extract details"""
        try:
            crew_input = {
                "conversation_context": self.get_conversation_context(call_sid),
                "current_details": str(self.conversation_states[call_sid]["details_collected"])
            }

            extraction_result = self.data_extraction_crew.kickoff(inputs=crew_input)
            
            # Try to parse the JSON response
            try:
                # Clean the response to extract just the JSON part
                response_text = extraction_result.raw.strip()
                
                # Handle different JSON response formats
                if '```json' in response_text:
                    json_str = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    json_str = response_text.split('```')[1].split('```')[0].strip()
                elif response_text.startswith('{') and response_text.endswith('}'):
                    json_str = response_text
                else:
                    # Try to find JSON object in the text
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        json_str = json_match.group()
                    else:
                        raise ValueError("No JSON found in response")
                
                extracted_data = json.loads(json_str)
                
                # Validate the extracted data
                self._validate_extracted_data(extracted_data)
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON parsing failed: {e}")
                raise ValueError("Invalid JSON response from extraction agent")
            
            # Update details collected
            current_details = self.conversation_states[call_sid]["details_collected"]
            extracted_details = extracted_data.get("extracted_details", {})
            
            for key, value in extracted_details.items():
                if value and value.strip() and value.strip() != "empty":
                    # Special validation for names to prevent mixing guardian and pet names
                    if key == "guardian_name" and value == current_details.get("pet_name"):
                        continue  # Don't overwrite pet name with guardian name
                    if key == "pet_name" and value == current_details.get("guardian_name"):
                        continue  # Don't overwrite guardian name with pet name
                    
                    current_details[key] = value.strip()
            
            # Update conversation stage
            new_stage = extracted_data.get("conversation_stage")
            if new_stage and new_stage in ["greeting", "collecting_guardian", "collecting_pet_details", 
                                         "collecting_appointment", "confirming", "concluded"]:
                self.conversation_states[call_sid]["stage"] = new_stage
            
        except Exception as e:
            print(f"Error in data extraction: {e}")
            # Fallback to improved extraction if AI extraction fails
            self._improved_fallback_extraction(call_sid)

    def _validate_extracted_data(self, extracted_data):
        """Validate that the extracted data makes sense"""
        details = extracted_data.get("extracted_details", {})
        
        # Guardian and pet names should not be the same
        if (details.get("guardian_name") and details.get("pet_name") and 
            details.get("guardian_name").lower() == details.get("pet_name").lower()):
            raise ValueError("Guardian and pet names cannot be the same")
        
        # Species should be simple animal types
        species = details.get("pet_species", "").lower()
        if species and species not in ["dog", "cat", "bird", "rabbit", "hamster", "fish", "reptile"]:
            # If it's a complex species, it might actually be a breed
            if details.get("pet_breed"):
                # If we already have a breed, this might be an error
                raise ValueError(f"Invalid species: {species}")
    
    def _improved_fallback_extraction(self, call_sid):
        """Improved fallback extraction with better pattern matching"""
        state = self.conversation_states[call_sid]
        conversation = self.conversations.get(call_sid, [])
        
        # Analyze the entire conversation for better context
        full_text = " ".join([msg["content"] for msg in conversation if msg["role"] == "customer"])
        full_text_lower = full_text.lower()
        
        # Improved patterns with better context awareness
        patterns = {
            "guardian_name": [
                r"my name is (\w+)", 
                r"it'?s (\w+)", 
                r"i'?m (\w+)",
                r"this is (\w+)",
                r"you can call me (\w+)",
                r"call me (\w+)"
            ],
            "pet_name": [
                r"pet'?s name is (\w+)", 
                r"name is (\w+)", 
                r"call (?:him|her|it) (\w+)",
                r"(\w+) is (?:my|the) (?:pet|dog|cat)",
                r"(\w+)'s (?:appointment|visit)"
            ],
            "pet_species": [
                r"it'?s a (\w+)", 
                r"species is (\w+)", 
                r"(\bdog\b|\bcat\b|\bbird\b|\bfish\b|\bhamster\b|\brabbit\b)",
                r"she'?s a (\w+)",
                r"he'?s a (\w+)"
            ],
            "pet_breed": [
                r"breed is ([^.,!?]*)", 
                r"(\w+(?:\s+\w+)*) breed",
                r"she'?s a ([^.,!?]*)",
                r"he'?s a ([^.,!?]*)",
                r"(\bGerman Shepherd\b|\bGolden Retriever\b|\bLabrador\b|\bBengal\b|\bSiamese\b|\bPersian\b)"
            ],
            "pet_dob": [
                r"date of birth is ([^.,!?]*)", 
                r"dob is ([^.,!?]*)", 
                r"born on ([^.,!?]*)",
                r"(\d+ months? old)",
                r"(\d+ years? old)",
                r"age is (\d+)"
            ],
            "appointment_date": [
                r"appointment is ([^.,!?]*)", 
                r"schedule for ([^.,!?]*)",
                r"(\w+ \d+(?:st|nd|rd|th))",
                r"(\d+/\d+/\d+)",
                r"([A-Za-z]+ \d+)"
            ],
            "appointment_time": [
                r"at (\d{1,2}:\d{2}\s*(?:am|pm))", 
                r"time is (\d{1,2}:\d{2}\s*(?:am|pm))",
                r"(\d{1,2}\s*(?:am|pm))",
                r"(\d{1,2}:\d{2})"
            ]
        }
        
        for field, field_patterns in patterns.items():
            if not state["details_collected"][field]:
                for pattern in field_patterns:
                    match = re.search(pattern, full_text_lower)
                    if match:
                        extracted_value = match.group(1).strip()
                        
                        # Additional validation
                        if field == "guardian_name" and extracted_value == state["details_collected"].get("pet_name"):
                            continue
                        if field == "pet_name" and extracted_value == state["details_collected"].get("guardian_name"):
                            continue
                            
                        state["details_collected"][field] = extracted_value.capitalize()
                        break

    def get_conversation_context(self, call_sid):
        if call_sid not in self.conversations:
            return ""
        
        # Get the full conversation history
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversations[call_sid]])
    
    def get_conversation_state(self, call_sid):
        return self.conversation_states.get(call_sid, {})
    
    def should_conclude(self, call_sid):
        state = self.get_conversation_state(call_sid)
        if not state:
            return False
        
        # Check if all essential details are collected and confirmed
        details = state.get("details_collected", {})
        essential_details = [
            details.get("guardian_name"),
            details.get("pet_name"), 
            details.get("pet_species"),
            details.get("appointment_date")
        ]
        
        # Check if the agent has said goodbye
        last_agent_message = ""
        if call_sid in self.conversations and self.conversations[call_sid]:
            agent_messages = [msg["content"] for msg in self.conversations[call_sid] if msg["role"] == "agent"]
            if agent_messages:
                last_agent_message = agent_messages[-1].lower()
        
        goodbye_phrases = ["thank you", "goodbye", "have a great day", "look forward to seeing you"]
        said_goodbye = any(phrase in last_agent_message for phrase in goodbye_phrases)
        
        # All essential details should be present and agent should have concluded
        return (all(essential_details) and said_goodbye)

# Global instance
conversation_manager = ConversationManager()