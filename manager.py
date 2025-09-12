# class ConversationManager:
#     def __init__(self):
#         self.conversations = {}
#         self.conversation_states = {}
#         self.covered_topics = {}
    
#     def initialize_conversation(self, call_sid):
#         self.conversations[call_sid] = [
#             {"role": "system", "content": "You are Alex from Sunny Meadows Veterinary Hospital. Start by introducing yourself and asking about their overall experience."}
#         ]
#         self.conversation_states[call_sid] = {
#             "stage": "introduction",
#             "topics_covered": set(),
#             "question_count": 0,
#             "customer_satisfaction": "neutral"
#         }
    
#     def update_conversation(self, call_sid, role, content):
#         if call_sid not in self.conversations:
#             self.initialize_conversation(call_sid)
        
#         self.conversations[call_sid].append({"role": role, "content": content})
        
#         # Update conversation state based on content
#         if role == "customer":
#             self._update_state_based_on_response(call_sid, content)
    
#     def _update_state_based_on_response(self, call_sid, response):
#         state = self.conversation_states[call_sid]
#         state["question_count"] += 1
        
#         # Detect topics mentioned in customer response
#         response_lower = response.lower()
#         topics_to_check = [
#             ("check-in", "checkin", "reception", "front desk"),
#             ("wait", "time", "waiting"),
#             ("vet", "doctor", "veterinarian", "examination"),
#             ("instructions", "advice", "prescription", "medication"),
#             ("overall", "experience", "satisfied", "happy")
#         ]
        
#         for topic_keywords in topics_to_check:
#             if any(keyword in response_lower for keyword in topic_keywords):
#                 state["topics_covered"].add(topic_keywords[0])
        
#         # Detect satisfaction level
#         if any(word in response_lower for word in ["good", "great", "excellent", "wonderful", "happy", "satisfied"]):
#             state["customer_satisfaction"] = "positive"
#         elif any(word in response_lower for word in ["bad", "poor", "terrible", "disappointed", "unhappy"]):
#             state["customer_satisfaction"] = "negative"
    
#     def get_conversation_context(self, call_sid):
#         if call_sid not in self.conversations:
#             return ""
        
#         # Limit conversation history to avoid token overflow
#         recent_messages = self.conversations[call_sid][-6:]  # Last 3 exchanges
#         return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
    
#     def get_conversation_state(self, call_sid):
#         return self.conversation_states.get(call_sid, {
#             "stage": "introduction",
#             "topics_covered": set(),
#             "question_count": 0,
#             "customer_satisfaction": "neutral"
#         })
    
#     def should_conclude(self, call_sid):
#         state = self.get_conversation_state(call_sid)
        
#         # Conclude if we've asked enough questions or covered main topics
#         if (state["question_count"] >= 5 or 
#             len(state["topics_covered"]) >= 3 or
#             state["stage"] == "conclusion"):
#             return True
        
#         return False

# # Global instance
# conversation_manager = ConversationManager()
# #working code
import re
from datetime import datetime

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.conversation_states = {}

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
            "confirmed_details": set(),
            "question_count": 0,
            "last_question": ""
        }

    def update_conversation(self, call_sid, role, content):
        if call_sid not in self.conversations:
            self.initialize_conversation(call_sid)
        
        self.conversations[call_sid].append({"role": role, "content": content})
        
        if role == "customer":
            self._extract_details_from_response(call_sid, content)
            self._update_state_based_on_response(call_sid, content)
        elif role == "agent":
            # Store the last question asked by agent
            state = self.conversation_states[call_sid]
            state["last_question"] = content

    def _extract_details_from_response(self, call_sid, response):
        state = self.conversation_states[call_sid]
        response_lower = response.lower()
        
        # Extract guardian name
        if not state["details_collected"]["guardian_name"]:
            name_patterns = [
                r"my name is (\w+)",
                r"it'?s (\w+)",
                r"i'?m (\w+)",
                r"this is (\w+)",
                r"you can call me (\w+)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    state["details_collected"]["guardian_name"] = match.group(1).capitalize()
                    break
        
        # Extract pet name
        if not state["details_collected"]["pet_name"]:
            pet_name_patterns = [
                r"pet'?s name is (\w+)",
                r"name is (\w+)",
                r"call (?:him|her|it) (\w+)",
                r"(\w+) is the name"
            ]
            
            for pattern in pet_name_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    state["details_collected"]["pet_name"] = match.group(1).capitalize()
                    break
        
        # Extract species
        if not state["details_collected"]["pet_species"]:
            species_patterns = [
                r"it'?s a (\w+)",
                r"species is (\w+)",
                r"(\w+) breed",
                r"(\bcat\b|\bdog\b|\bbird\b|\bfish\b|\bhamster\b|\brabbit\b)"
            ]
            
            for pattern in species_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    state["details_collected"]["pet_species"] = match.group(1).capitalize()
                    break
        
        # Extract breed
        if not state["details_collected"]["pet_breed"]:
            breed_patterns = [
                r"breed is ([^.?!]*)",
                r"(\w+)(?:\s+\w+)* breed",
                r"it'?s a ([^.?!]*)(?=and|\.|$)"
            ]
            
            for pattern in breed_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    breed = match.group(1).strip()
                    if breed and not breed.isdigit():  # Filter out numbers
                        state["details_collected"]["pet_breed"] = breed.capitalize()
                    break
        
        # Extract date of birth
        if not state["details_collected"]["pet_dob"]:
            dob_patterns = [
                r"date of birth is ([^.?!]*)",
                r"dob is ([^.?!]*)",
                r"born on ([^.?!]*)",
                r"(\d+(?:th|st|nd|rd)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
                r"(\d{1,2}/\d{1,2}/\d{4})"
            ]
            
            for pattern in dob_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    state["details_collected"]["pet_dob"] = match.group(1).capitalize()
                    break
        
        # Extract appointment date and time
        if not state["details_collected"]["appointment_date"]:
            appointment_patterns = [
                r"appointment is ([^.?!]*)",
                r"schedule for ([^.?!]*)",
                r"(\d+(?:th|st|nd|rd)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+at\s+\d{1,2}:\d{2}\s*(?:am|pm))",
                r"(\d{1,2}/\d{1,2}/\d{4}\s+at\s+\d{1,2}:\d{2}\s*(?:am|pm))"
            ]
            
            for pattern in appointment_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    appointment_info = match.group(1).capitalize()
                    # Separate date and time if possible
                    if " at " in appointment_info:
                        date_part, time_part = appointment_info.split(" at ", 1)
                        state["details_collected"]["appointment_date"] = date_part.strip()
                        state["details_collected"]["appointment_time"] = time_part.strip()
                    else:
                        state["details_collected"]["appointment_date"] = appointment_info
                    break

    def _update_state_based_on_response(self, call_sid, response):
        state = self.conversation_states[call_sid]
        state["question_count"] += 1
        response_lower = response.lower()

        # Check for positive confirmation
        is_positive_confirmation = any(word in response_lower for word in [
            "yes", "correct", "that's right", "perfect", "sounds good", 
            "yep", "right", "exactly", "confirmed", "go ahead"
        ])
        
        # Check for negative response
        is_negative = any(word in response_lower for word in [
            "no", "not", "incorrect", "wrong", "change", "nope"
        ])
        
        # Update stage based on response
        if "last_question" in state:
            last_q = state["last_question"].lower()
            
            if "name" in last_q and state["details_collected"]["guardian_name"]:
                state["stage"] = "collecting_pet_details"
            
            elif ("pet" in last_q or "species" in last_q or "breed" in last_q or "dob" in last_q) and \
                 (state["details_collected"]["pet_name"] and state["details_collected"]["pet_species"]):
                state["stage"] = "collecting_appointment"
            
            elif "appointment" in last_q and state["details_collected"]["appointment_date"]:
                state["stage"] = "confirming_details"
            
            elif "correct" in last_q or "confirm" in last_q:
                if is_positive_confirmation:
                    state["details_collected"]["appointment_confirmed"] = True
                    state["stage"] = "conclusion"
                elif is_negative:
                    state["stage"] = "correcting_details"

    def get_conversation_context(self, call_sid):
        if call_sid not in self.conversations:
            return ""
        
        recent_messages = self.conversations[call_sid][-6:]
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
    
    def get_conversation_state(self, call_sid):
        return self.conversation_states.get(call_sid, {})
    
    def should_conclude(self, call_sid):
        state = self.get_conversation_state(call_sid)
        if not state:
            return False
        
        # Check if all details are confirmed and we're at conclusion stage
        details = state.get("details_collected", {})
        if (state.get("stage") == "conclusion" and 
            details.get("appointment_confirmed")):
            return True

        return False

# Global instance
conversation_manager = ConversationManager()