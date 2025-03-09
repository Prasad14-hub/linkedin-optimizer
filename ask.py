import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
import os
from dotenv import load_dotenv
import hashlib

# Load environment variables from .env file
load_dotenv()

# Function to hash passwords for security (kept for mock login)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Mock database initialization (no MySQL dependency)
def init_db():
    """Mock database initialization for Streamlit Cloud compatibility."""
    print("Mock database initialized.")  # Debug only
    return None, None  # No real connection or cursor needed

# Format profile data from manual inputs
def format_profile_data(name, skills, about, experience, education):
    """Format manually entered profile data into a string, handling empty fields."""
    context = ""
    if name:
        context += f"Name: {name}\n"
    if skills:
        context += f"Skills: {skills}\n"
    if about:
        context += f"About: {about}\n"
    if experience:
        context += f"Experience:\n{experience}\n"
    if education:
        context += f"Education:\n{education}"
    return context.strip() or "No profile data provided."

# Format job data from manual inputs
def format_job_data(title, company, skills, description):
    """Format manually entered job data into a string, handling empty fields."""
    context = ""
    if title:
        context += f"Job Title: {title}\n"
    if company:
        context += f"Company: {company}\n"
    if skills:
        context += f"Skills: {skills}\n"
    if description:
        context += f"Description: {description}"
    return context.strip() or "No job data provided."

# Initialize mock database
conn, c = init_db()

# Initialize Groq LLM
llm = ChatGroq(model="llama3-70b-8192", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# Define a refined prompt with strict focus on the query
unified_prompt = PromptTemplate(
    input_variables=["query", "profile_context", "job_context", "career_goals", "chat_history"],
    template="""
    You are a LinkedIn profile optimization assistant. You have the following user data:
    - Profile: {profile_context}
    - Job Details: {job_context}
    - Career Goals: {career_goals}

    Here is the chat history for the current session:
    {chat_history}

    The user has asked: "{query}"

    **Instructions:**
    - Respond **only** to the specific request in the query. Do not include additional unsolicited advice or content (e.g., career guidance, cover letters) unless explicitly asked.
    - Match the query to one of the following categories and provide a focused response:
      - If the query contains "profile analysis" or "analyze my profile," analyze the profile data ({profile_context}) and suggest improvements, noting any missing sections.
      - If the query contains "job fit" or "job match" or "analyze job," compare the profile ({profile_context}) with the job details ({job_context}), provide a match score (0-100), and suggest improvements, noting missing data.
      - If the query contains "enhance content" or "improve profile," enhance all provided sections of the profile ({profile_context}) aligned with the job details ({job_context}) or general best practices if no job data is provided.
      - If the query contains "career guidance" or "counseling," provide career advice based on the profile ({profile_context}) and career goals ({career_goals}), identifying missing skills and suggesting resources.
      - If the query contains "cover letter," generate a personalized cover letter using the profile ({profile_context}) and job details ({job_context}), noting any missing data.
      - If the query asks about the "previous question" or "last question," refer to the chat history ({chat_history}) to identify and respond with the last question asked in this session.
      - For any other query, provide a concise, relevant response using the available data ({profile_context}, {job_context}, {career_goals}) and chat_history ({chat_history}), or indicate if the intent is unclear and suggest clarification.
    - Do not mix responses from different categories unless the query explicitly requests multiple tasks.

    Provide a clear, formatted response with markdown (e.g., **bold**, - bullets).
    """
)

# Initialize unified chain with RunnableSequence
unified_chain = RunnableSequence(unified_prompt | llm)

# Streamlit app setup
st.title("LinkedIn Optimizer Chat")

# Authentication (mocked without database)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.profile_context = ""
    st.session_state.job_context = ""
    st.session_state.career_goals = ""
    st.session_state.chat_history = []
    st.session_state.current_session = None  # No default session
    st.session_state.input_value = ""       # Initialize input value
    st.session_state.last_input = ""        # Track last processed input

if not st.session_state.logged_in:
    st.subheader("Login")
    login_email = st.text_input("Email", key="login_email")
    login_password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        if login_email and login_password:
            # Mock login (no database check)
            st.session_state.logged_in = True
            st.session_state.user_id = login_email
            st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
            st.session_state.chat_history = []
            st.session_state.input_value = ""
            st.session_state.last_input = ""
            st.success("Logged in successfully!")
            print(f"User {login_email} logged in. New session: {st.session_state.current_session}")
        else:
            st.error("Please enter both email and password.")

    st.subheader("Sign Up")
    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    
    if st.button("Sign Up"):
        if signup_email and signup_password:
            # Mock signup (no database insert)
            st.session_state.logged_in = True
            st.session_state.user_id = signup_email
            st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
            st.session_state.chat_history = []
            st.session_state.input_value = ""
            st.session_state.last_input = ""
            st.success("Account created and logged in!")
            print(f"User {signup_email} signed up. New session: {st.session_state.current_session}")
        else:
            st.error("Please enter both email and password.")
else:
    user_id = st.session_state.user_id

    # Sidebar for Manual Inputs and Session Management
    with st.sidebar:
        st.markdown(f"### Hello, {user_id}!")  # Improved "Welcome back" positioning
        
        st.header("Profile Setup")
        
        # Manual Profile Inputs
        st.subheader("Your Profile")
        profile_name = st.text_input("Name", value="Prasad Gavhane" if not st.session_state.profile_context else "", key="profile_name")
        profile_skills = st.text_input("Skills", value="Python, Generative AI" if not st.session_state.profile_context else "", key="profile_skills")
        profile_about = st.text_area("About", value="Experienced software engineer with a focus on AI and data analytics." if not st.session_state.profile_context else "", key="profile_about")
        profile_experience = st.text_area("Experience", value="Senior Software Engineer at LTIMindtree (2020-Present): Worked on Generative AI projects.\nSoftware Engineer at XYZ Corp (2018-2020): Developed Python-based applications." if not st.session_state.profile_context else "", key="profile_experience")
        profile_education = st.text_area("Education", value="B.Tech from IIT(ISM) Dhanbad (2014-2018)" if not st.session_state.profile_context else "", key="profile_education")
        
        if st.button("Save Profile", key="save_profile"):
            profile_context = format_profile_data(profile_name, profile_skills, profile_about, profile_experience, profile_education)
            st.session_state.profile_context = profile_context
            st.success("Profile saved successfully!")
            print(f"Profile saved for {user_id}: {profile_context}")

        # Manual Job Inputs
        st.subheader("Job Details")
        job_title = st.text_input("Job Title", value="Senior Software Engineer" if not st.session_state.job_context else "", key="job_title")
        job_company = st.text_input("Company", value="TechCorp" if not st.session_state.job_context else "", key="job_company")
        job_skills = st.text_input("Skills", value="Python, Generative AI, Software Development" if not st.session_state.job_context else "", key="job_skills")
        job_description = st.text_area("Description", value="Seeking a Senior Software Engineer with expertise in Python, Generative AI, and software development." if not st.session_state.job_context else "", key="job_description")
        
        if st.button("Save Job Details", key="save_job"):
            job_context = format_job_data(job_title, job_company, job_skills, job_description)
            st.session_state.job_context = job_context
            st.success("Job details saved successfully!")
            print(f"Job saved for {user_id}: {job_context}")

        # Career Goals
        st.subheader("Career Goals")
        career_goals = st.text_area("Enter your career goals:", value=st.session_state.career_goals, key="goals")
        if st.button("Save Goals", key="save_goals"):
            if career_goals:
                st.session_state.career_goals = career_goals
                st.success("Career goals saved!")
                print(f"Career goals saved for {user_id}: {career_goals}")
            else:
                st.error("Please enter career goals.")

        # Session Management
        st.subheader("Session Management")
        if st.button("Create New Session", key="new_session"):
            st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
            st.session_state.chat_history = []
            st.session_state.input_value = ""
            st.session_state.last_input = ""
            st.success("New session created!")
            print(f"New session for {user_id}: {st.session_state.current_session}")

        # Session History (mocked, no database)
        st.subheader("Session History")
        st.info("Session history is not persisted without a database. It resets on app restart.")

    # Main Chat Interface
    st.markdown(f"**Current Session: {st.session_state.current_session[-8:]}**")
    st.markdown("I can help with profile analysis, job fit analysis, content enhancement, career counseling, or cover letter generation. What would you like to do?")

    # Chat history display (oldest at top, newest at bottom)
    for message in st.session_state.chat_history:
        if message["role"] == "You":
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                    <div style="background-color: #e0e0e0; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word;">
                        {message['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                    <div style="background-color: #ffffff; padding: 10px; border: 1px solid #e0e0e0; border-radius: 10px; max-width: 70%; word-wrap: break-word;">
                        {message['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # User input form at the bottom
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Your question:", key="chat_input", value="")
        submit_button = st.form_submit_button(label="Ask")

        # Process input only if submitted and non-empty
        if submit_button and user_input:
            chat_history_str = "\n".join(
                f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history
            ) if st.session_state.chat_history else "No previous chat history in this session."

            response = unified_chain.invoke({
                "query": user_input,
                "profile_context": st.session_state.profile_context or "No profile data provided.",
                "job_context": st.session_state.job_context or "No job data provided.",
                "career_goals": st.session_state.career_goals or "No career goals provided.",
                "chat_history": chat_history_str
            })

            response_text = response.content if hasattr(response, 'content') else str(response)

            st.session_state.chat_history.append({"role": "You", "content": user_input})
            st.session_state.chat_history.append({"role": "Assistant", "content": response_text})
            # No database save since MySQL is removed
            st.session_state.last_input = user_input
            st.session_state.input_value = ""
            st.rerun()

# No conn.close() since no database connection