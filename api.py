from fastapi import FastAPI, Form, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
import os
from crewai import Crew, Process

from agents import vet_appointment_agent
from tasks import confirmation_task
from manager import conversation_manager

load_dotenv()

app = FastAPI()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ngrok_base_url = os.getenv("NGROK_BASE_URL")

client = Client(account_sid, auth_token)

@app.post("/start-call")
async def start_call(request: Request):
    data = await request.json()
    customer_number = data.get("phone_number")
    if not customer_number:
        return {"status": "error", "message": "Phone number is required"}
    webhook_url = f"{ngrok_base_url}/voice-webhook"
    call = client.calls.create(to=customer_number, from_=twilio_number, url=webhook_url)
    conversation_manager.initialize_conversation(call.sid)
    return {"status": "success", "sid": call.sid}

@app.post("/end-call/{call_sid}")
async def end_call(call_sid: str):
    try:
        client.calls(call_sid).update(status='completed')
        return {"status": "success", "message": "Call ended successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    try:
        call = client.calls(call_sid).fetch()
        return {"status": call.status}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/voice-webhook")
async def voice_webhook(CallSid: str = Form(...), SpeechResult: str = Form(None)):
    response = VoiceResponse()
    
    if SpeechResult:
        conversation_manager.update_conversation(CallSid, "customer", SpeechResult)
    
    # Check if we should end the call first
    if conversation_manager.should_conclude(CallSid):
        response.say("Thank you for confirming all the details! We look forward to seeing you and your pet. Have a wonderful day!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        # End the call through Twilio
        try:
            client.calls(CallSid).update(status='completed')
        except Exception as e:
            print(f"Error ending call: {e}")
        
        return Response(content=str(response), media_type="application/xml")
    
    state = conversation_manager.get_conversation_state(CallSid)
    
    appointment_crew = Crew(
        agents=[vet_appointment_agent],
        tasks=[confirmation_task],
        process=Process.sequential,
        verbose=True
    )
    
    crew_input = {
        "call_sid": CallSid,
        "conversation_context": conversation_manager.get_conversation_context(CallSid),
        "details_collected": state.get("details_collected", {})
    }

    crew_result = appointment_crew.kickoff(inputs=crew_input)
    agent_response_text = crew_result.raw

    conversation_manager.update_conversation(CallSid, "agent", agent_response_text)
    
    full_webhook_url = f"{ngrok_base_url}/voice-webhook"
    gather = Gather(input='speech', action=full_webhook_url, timeout=10, speechTimeout='auto')
    gather.say(agent_response_text, voice='Polly.Joanna-Neural')
    response.append(gather)

    return Response(content=str(response), media_type="application/xml")

async def _end_call_after_delay(call_sid, delay_seconds=2):
    """End the call after a short delay to allow the final message to play"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    try:
        client.calls(call_sid).update(status='completed')
    except Exception as e:
        print(f"Error ending call: {e}")

@app.get("/transcript/{call_sid}")
async def get_transcript(call_sid: str):
    return {"transcript": conversation_manager.conversations.get(call_sid, [])}

@app.get("/conversation-state/{call_sid}")
async def get_conversation_state(call_sid: str):
    return conversation_manager.get_conversation_state(call_sid)