import streamlit as st
import requests
import time
import datetime

st.set_page_config(layout="wide", page_title="Vet Feedback Agent")

API_URL = "http://127.0.0.1:8000"

# Initialize session state variables
if 'call_sid' not in st.session_state:
    st.session_state.call_sid = None
if 'call_active' not in st.session_state:
    st.session_state.call_active = False
if 'call_start_time' not in st.session_state:
    st.session_state.call_start_time = None

def display_call_summary(call_sid):
    # Display Transcript
    transcript_response = requests.get(f"{API_URL}/transcript/{call_sid}")
    if transcript_response.status_code == 200:
        data = transcript_response.json()
        transcript_html = ""
        for message in data.get("transcript", []):
            if message['role'] == 'agent':
                transcript_html += f"<p><b>🤖 Agent:</b> {message['content']}</p>"
            elif message['role'] == 'customer':
                transcript_html += f"<p><b>👤 Customer:</b> {message['content']}</p>"
        transcript_placeholder.markdown(transcript_html, unsafe_allow_html=True)

    # Display Conversation & Pet State in Sidebar
    state_response = requests.get(f"{API_URL}/conversation-state/{call_sid}")
    if state_response.status_code == 200:
        state_data = state_response.json()
        
        with state_placeholder.container():
            stage = state_data.get('stage', 'N/A').replace('_', ' ').capitalize()
            st.metric("Conversation Stage", stage)
            
            # Show progress based on stage
            stages = ["Greeting", "Collecting guardian", "Collecting pet details", 
                     "Collecting appointment", "Confirming", "Concluded"]
            current_index = stages.index(stage) if stage in stages else 0
            st.progress((current_index + 1) / len(stages))

        with pet_details_placeholder.container():
            details = state_data.get('details_collected', {})
            confirmed_status = "✅ Confirmed" if stage in ["Confirming", "Concluded"] else "⏳ Pending"

            st.subheader("🐾 Collected Details")

            st.subheader("🐾 Collected Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if details.get('guardian_name'):
                    st.success(f"**Guardian:** {details.get('guardian_name')}")
                else:
                    st.info("**Guardian:** Not collected")
                
                if details.get('pet_name'):
                    st.success(f"**Pet Name:** {details.get('pet_name')}")
                else:
                    st.info("**Pet Name:** Not collected")
                
                if details.get('pet_species'):
                    st.success(f"**Species:** {details.get('pet_species')}")
                else:
                    st.info("**Species:** Not collected")
            
            with col2:
                if details.get('pet_breed'):
                    st.success(f"**Breed:** {details.get('pet_breed')}")
                else:
                    st.info("**Breed:** Not collected")
                
                if details.get('pet_dob'):
                    st.success(f"**DOB/Age:** {details.get('pet_dob')}")
                else:
                    st.info("**DOB/Age:** Not collected")
                
                if details.get('appointment_date'):
                    appointment_text = details.get('appointment_date')
                    if details.get('appointment_time'):
                        appointment_text += f" at {details.get('appointment_time')}"
                    st.success(f"**Appointment:** {appointment_text}")
                else:
                    st.info("**Appointment:** Not scheduled")
            
            st.write(f"**Status:** {confirmed_status}")


# --- Sidebar for Controls and Status ---
with st.sidebar:
    st.title("📞 Control Panel")
    st.header("Start a New Call")
    phone_number = st.text_input("Enter customer phone number", key="phone_input")

    if st.button("Start Call", disabled=st.session_state.call_active):
        if phone_number:
            with st.spinner("Initiating call..."):
                try:
                    response = requests.post(f"{API_URL}/start-call", json={"phone_number": phone_number})
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.call_sid = data.get("sid")
                        st.session_state.call_active = True
                        st.session_state.call_start_time = time.time()
                        st.rerun()
                    else:
                        st.error(f"Failed to start call. Server responded with: {response.text}")
                except requests.ConnectionError:
                    st.error("Connection failed. Is the API server running?")
        else:
            st.warning("Please enter a phone number.")
    
    st.divider()
    
    st.header("Call Status")
    timer_placeholder = st.empty()
    if st.session_state.call_active:
        if st.button("End Call", type="primary"):
            with st.spinner("Ending call..."):
                requests.post(f"{API_URL}/end-call/{st.session_state.call_sid}")
                st.session_state.call_active = False
                st.rerun()
    
    st.subheader("Conversation State")
    state_placeholder = st.empty()

    st.subheader("🐾 Collected Details")
    pet_details_placeholder = st.empty()


# --- Main Area for Transcript ---
st.title("Vet Hospital Appointment Confirmation")
st.header("Live Call Transcript" if st.session_state.call_active else "Final Call Summary")
transcript_placeholder = st.empty()


if st.session_state.call_active:
    while st.session_state.call_active:
        try:
            status_response = requests.get(f"{API_URL}/call-status/{st.session_state.call_sid}")
            if status_response.status_code == 200:
                status = status_response.json().get("status")
                if status in ["completed", "canceled", "failed", "no-answer"]:
                    st.session_state.call_active = False
                    st.info("Call has ended.")
                    time.sleep(1)
                    st.rerun()
                    break
            
            elapsed_time = time.time() - st.session_state.call_start_time
            timer_placeholder.metric("Call Duration", str(datetime.timedelta(seconds=int(elapsed_time))))
            
            display_call_summary(st.session_state.call_sid)
            
            time.sleep(2)
        except requests.ConnectionError:
            st.error("Connection to API server has been lost.")
            st.session_state.call_active = False
            st.rerun()

elif st.session_state.call_sid:
    timer_placeholder.info("Call concluded.")
    display_call_summary(st.session_state.call_sid)

else:
    transcript_placeholder.info("Start a call from the control panel to see the transcript.")
    timer_placeholder.info("No active call.")
    state_placeholder.empty()
    pet_details_placeholder.empty()