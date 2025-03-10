import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
import psycopg2
import os
from dotenv import load_dotenv
import hashlib
from groq import Groq
from gtts import gTTS
import io

# Load environment variables from .env file to securely access API keys and database credentials
load_dotenv()

# Initialize the Groq client for potential future use (e.g., API calls), though not currently used for transcription
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to hash passwords using SHA-256 for secure storage in the database
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Set up the PostgreSQL database connection and create necessary tables
def init_db():
    try:
        # Establish connection to Neon PostgreSQL using credentials from environment variables
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT", "5432"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database="linkedin",
            sslmode="require"
        )
        c = conn.cursor()
        print("Successfully connected to PostgreSQL database.")
        
        # Create the users table to store user credentials and data if it doesn’t already exist
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id VARCHAR(255) PRIMARY KEY, 
                     password VARCHAR(255), 
                     profile_data TEXT, 
                     job_data TEXT, 
                     career_goals TEXT)''')
        print("Users table created or confirmed.")
        
        # Ensure all required columns exist in the users table, adding any that are missing
        for column, col_type in [
            ('password', 'VARCHAR(255)'),
            ('profile_data', 'TEXT'),
            ('job_data', 'TEXT'),
            ('career_goals', 'TEXT')
        ]:
            c.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='{column}'")
            if not c.fetchone():
                c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
                print(f"Added missing column '{column}' to users table.")
        
        # Create the session_history table to log chat interactions
        c.execute('''CREATE TABLE IF NOT EXISTS session_history (
                     user_id VARCHAR(255), 
                     session_group VARCHAR(255), 
                     session_id SERIAL PRIMARY KEY, 
                     query TEXT, 
                     response TEXT, 
                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        print("Session history table created or confirmed.")
        
        # Add session_group column to session_history if it’s missing, and update older records
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='session_history' AND column_name='session_group'")
        if not c.fetchone():
            c.execute("ALTER TABLE session_history ADD COLUMN session_group VARCHAR(255)")
            print("Added session_group column to session_history.")
            c.execute("UPDATE session_history SET session_group = 'legacy_session' WHERE session_group IS NULL")
            print("Assigned 'legacy_session' to existing records.")
        
        conn.commit()
        print("Database initialization completed successfully.")
        return conn, c
    except psycopg2.Error as err:
        st.error(f"Failed to connect to PostgreSQL: {err}")
        print(f"Database connection error: {err}")
        return None, None

# Format profile data into a clean, readable string for use in prompts or display
def format_profile_data(name, skills, about, experience, education):
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

# Format job data similarly for consistency and clarity
def format_job_data(title, company, skills, description):
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

# Convert text to audio using gTTS for the audio output option
def text_to_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

# Initialize database connection at startup
conn, c = init_db()
if conn is None or c is None:
    st.error("Database connection failed - please verify credentials in .env file.")
    st.stop()

# Configure the Groq LLM for generating text responses
llm = ChatGroq(model="llama3-70b-8192", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# Define the prompt template for the LLM, providing clear instructions for various tasks
unified_prompt = PromptTemplate(
    input_variables=["query", "profile_context", "job_context", "career_goals", "chat_history"],
    template="""
    You’re a LinkedIn profile optimization assistant here to help users polish their professional presence. You’ve got access to the following info:
    - User’s Profile: {profile_context}
    - Job Details: {job_context}
    - Career Goals: {career_goals}

    Here’s what’s been said in this session so far:
    {chat_history}

    The user just asked: "{query}"

    **Here’s what I need you to do:**
    - Stick strictly to what the user is asking for - no extra fluff or unsolicited advice unless they explicitly want it.
    - Figure out what they’re after based on these categories and give a spot-on answer:
      - If they say "profile analysis" or "analyze my profile," dig into their profile data ({profile_context}). Point out what’s strong, what’s weak, and suggest specific tweaks. Flag anything missing that could help.
      - If it’s "job fit," "job match," or "analyze job," compare their profile ({profile_context}) to the job details ({job_context}). Give a match score from 0 to 100, explain why, and recommend upgrades. Note if data’s missing.
      - For "enhance content" or "improve profile," take their profile sections ({profile_context}) and rewrite them to shine - align with the job ({job_context}) if it’s there, or just use LinkedIn best practices if not.
      - If they want "career guidance" or "counseling," use their profile ({profile_context}) and goals ({career_goals}) to offer tailored advice. Highlight gaps in skills or experience and suggest practical next steps or resources.
      - For "cover letter," whip up a custom cover letter using their profile ({profile_context}) and job details ({job_context}). Call out any missing info that’d make it better.
      - If they ask about the "previous question" or "last question," check the chat history ({chat_history}), find the last thing they asked, and repeat or answer it clearly.
      - For anything else, give a concise, relevant reply based on what you’ve got ({profile_context}, {job_context}, {career_goals}, {chat_history}). If it’s unclear what they mean, say so and ask them to clarify.
    - Don’t mash up different tasks unless they specifically ask for a combo. Keep it clean and focused.
    - Write naturally, like you’re explaining it to a friend - no fancy formatting tricks, just plain, clear language.
    """
)

# Create a sequence to chain the prompt with the LLM for smooth execution
unified_chain = RunnableSequence(unified_prompt | llm)

# Start the Streamlit app with a clear title
st.title("LinkedIn Optimizer Chat")

# Initialize session state variables to manage login and chat context
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.profile_context = ""
    st.session_state.job_context = ""
    st.session_state.career_goals = ""
    st.session_state.chat_history = []
    st.session_state.current_session = None
    st.session_state.input_value = ""
    st.session_state.last_input = ""

# Handle login and signup before showing the main app
if not st.session_state.logged_in:
    st.subheader("Login")
    login_email = st.text_input("Email", key="login_email")
    login_password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        if login_email and login_password:
            hashed_password = hash_password(login_password)
            c.execute("SELECT profile_data, job_data, career_goals FROM users WHERE user_id=%s AND password=%s", (login_email, hashed_password))
            result = c.fetchone()
            if result:
                # Successful login - populate session state with user data
                st.session_state.logged_in = True
                st.session_state.user_id = login_email
                st.session_state.profile_context = result[0] if result[0] else ""
                st.session_state.job_context = result[1] if result[1] else ""
                st.session_state.career_goals = result[2] if result[2] else ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Login successful - welcome back!")
                print(f"User {login_email} logged in with session: {st.session_state.current_session}")
                st.rerun()
            else:
                st.error("Invalid email or password - please check and retry.")
        else:
            st.error("Both email and password are required.")

    st.subheader("Sign Up")
    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    
    if st.button("Sign Up"):
        if signup_email and signup_password:
            hashed_password = hash_password(signup_password)
            try:
                c.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", (signup_email, hashed_password))
                conn.commit()
                # New user created - log them in automatically
                st.session_state.logged_in = True
                st.session_state.user_id = signup_email
                st.session_state.profile_context = ""
                st.session_state.job_context = ""
                st.session_state.career_goals = ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Signup complete - you’re logged in!")
                print(f"User {signup_email} signed up with session: {st.session_state.current_session}")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("Email already in use - please log in instead.")
        else:
            st.error("Email and password are required for signup.")
else:
    user_id = st.session_state.user_id

    # Sidebar for user data input and session management
    with st.sidebar:
        st.markdown(f"### Hello, {user_id}!")  
        
        st.header("Profile Setup")
        
        st.subheader("Your Profile")
        profile_name = st.text_input("Name", value="Prasad Gavhane" if not st.session_state.profile_context else "", key="profile_name")
        profile_skills = st.text_input("Skills", value="Python, Generative AI" if not st.session_state.profile_context else "", key="profile_skills")
        profile_about = st.text_area("About", value="Experienced software engineer with a focus on AI and data analytics." if not st.session_state.profile_context else "", key="profile_about")
        profile_experience = st.text_area("Experience", value="Senior Software Engineer at LTIMindtree (2020-Present): Worked on Generative AI projects.\nSoftware Engineer at XYZ Corp (2018-2020): Developed Python-based applications." if not st.session_state.profile_context else "", key="profile_experience")
        profile_education = st.text_area("Education", value="B.Tech from IIT(ISM) Dhanbad (2014-2018)" if not st.session_state.profile_context else "", key="profile_education")
        
        if st.button("Save Profile", key="save_profile"):
            profile_context = format_profile_data(profile_name, profile_skills, profile_about, profile_experience, profile_education)
            st.session_state.profile_context = profile_context
            c.execute("UPDATE users SET profile_data=%s WHERE user_id=%s", (profile_context, user_id))
            conn.commit()
            st.success("Profile data saved successfully.")
            print(f"Profile updated for {user_id}: {profile_context}")

        st.subheader("Job Details")
        job_title = st.text_input("Job Title", value="Senior Software Engineer" if not st.session_state.job_context else "", key="job_title")
        job_company = st.text_input("Company", value="TechCorp" if not st.session_state.job_context else "", key="job_company")
        job_skills = st.text_input("Skills", value="Python, Generative AI, Software Development" if not st.session_state.job_context else "", key="job_skills")
        job_description = st.text_area("Description", value="Seeking a Senior Software Engineer with expertise in Python, Generative AI, and software development." if not st.session_state.job_context else "", key="job_description")
        
        if st.button("Save Job Details", key="save_job"):
            job_context = format_job_data(job_title, job_company, job_skills, job_description)
            st.session_state.job_context = job_context
            c.execute("UPDATE users SET job_data=%s WHERE user_id=%s", (job_context, user_id))
            conn.commit()
            st.success("Job details saved successfully.")
            print(f"Job details updated for {user_id}: {job_context}")

        st.subheader("Career Goals")
        career_goals = st.text_area("Enter your career goals:", value=st.session_state.career_goals, key="goals")
        if st.button("Save Goals", key="save_goals"):
            if career_goals:
                st.session_state.career_goals = career_goals
                c.execute("UPDATE users SET career_goals=%s WHERE user_id=%s", (career_goals, user_id))
                conn.commit()
                st.success("Career goals saved successfully.")
                print(f"Career goals updated for {user_id}: {career_goals}")
            else:
                st.error("Please enter career goals before saving.")

        st.subheader("Session Management")
        if st.button("Create New Session", key="new_session"):
            st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
            st.session_state.chat_history = []
            st.session_state.input_value = ""
            st.session_state.last_input = ""
            st.success("New session created.")
            print(f"New session started for {user_id}: {st.session_state.current_session}")

        st.subheader("Session History")
        try:
            # Fetch a summary of past sessions for the user, showing the first query of each group
            c.execute("""
                SELECT session_group, query, timestamp
                FROM session_history 
                WHERE user_id=%s 
                AND session_id IN (
                    SELECT MIN(session_id) 
                    FROM session_history 
                    WHERE user_id=%s 
                    GROUP BY session_group
                )
                ORDER BY timestamp DESC
            """, (user_id, user_id))
            sessions = c.fetchall()
            for session_group, first_query, _ in sessions:
                session_group = session_group if session_group else "legacy_session"
                summary = (first_query[:30] + "...") if len(first_query) > 30 else first_query
                if st.button(f"Session: {summary}", key=f"hist_{session_group}"):
                    st.session_state.current_session = session_group
                    st.session_state.chat_history = []
                    st.session_state.input_value = ""
                    st.session_state.last_input = ""
                    c.execute("SELECT query, response FROM session_history WHERE user_id=%s AND session_group=%s ORDER BY session_id", (user_id, session_group))
                    history = c.fetchall()
                    for query, response in history:
                        st.session_state.chat_history.append({"role": "You", "content": query})
                        st.session_state.chat_history.append({"role": "Assistant", "content": response})
                    st.success(f"Loaded session: {summary}")
        except psycopg2.Error as e:
            st.warning(f"Failed to load session history: {e}. Using fallback method.")
            print(f"Session history query failed: {e}")
            c.execute("SELECT query, response FROM session_history WHERE user_id=%s ORDER BY timestamp DESC LIMIT 10", (user_id,))
            history = c.fetchall()
            if history and st.button("Load Legacy Session", key="hist_legacy"):
                st.session_state.current_session = "legacy_session"
                st.session_state.chat_history = []
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                for query, response in history:
                    st.session_state.chat_history.append({"role": "You", "content": query})
                    st.session_state.chat_history.append({"role": "Assistant", "content": response})
                st.success("Loaded legacy session data.")

    # Display the current session ID in the main area
    st.markdown(f"**Current Session: {st.session_state.current_session[-8:]}**")
    st.markdown("I can help with profile analysis, job fit analysis, content enhancement, career counseling, or cover letter generation. What would you like to do?")

    # Show chat history with user messages on the right and assistant on the left
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
            if isinstance(message["content"], tuple) and len(message["content"]) == 2:
                text_response, audio_data = message["content"]
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                        <div style="background-color: #ffffff; padding: 10px; border: 1px solid #e0e0e0; border-radius: 10px; max-width: 70%; word-wrap: break-word;">
                            {text_response}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.audio(audio_data, format="audio/mp3")
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

    # Form for user input with text entry and output type selection
    with st.form(key="chat_form", clear_on_submit=True):
        st.write("Ask your question:")
        user_input = st.text_input("Type your question:", key="chat_input", value="", label_visibility="collapsed")
        output_type = st.selectbox("Select output type:", ["Text", "Audio"], index=0, key="output_type")
        submit_button = st.form_submit_button(label="Ask")

        # Process user input when the form is submitted
        if submit_button and user_input:
            query = user_input
            # Construct chat history string to provide context to the LLM
            chat_history_str = "\n".join(
                f"{msg['role']}: {msg['content'][0] if isinstance(msg['content'], tuple) else msg['content']}"
                for msg in st.session_state.chat_history
            ) if st.session_state.chat_history else "No previous chat history in this session."

            # Send the query to the LLM with all relevant context
            response = unified_chain.invoke({
                "query": query,
                "profile_context": st.session_state.profile_context or "No profile data provided.",
                "job_context": st.session_state.job_context or "No job data provided.",
                "career_goals": st.session_state.career_goals or "No career goals provided.",
                "chat_history": chat_history_str
            })

            response_text = response.content if hasattr(response, 'content') else str(response)

            # Handle the selected output type (text or audio)
            if output_type == "Audio":
                audio_data = text_to_audio(response_text)
                if audio_data:
                    response_content = (response_text, audio_data)
                else:
                    response_content = response_text
            else:
                response_content = response_text

            # Update chat history with the new query and response
            st.session_state.chat_history.append({"role": "You", "content": query})
            st.session_state.chat_history.append({"role": "Assistant", "content": response_content})

            # Store the interaction in the database for persistence
            try:
                c.execute("INSERT INTO session_history (user_id, session_group, query, response) VALUES (%s, %s, %s, %s)", 
                          (user_id, st.session_state.current_session, query, response_text))
                conn.commit()
            except psycopg2.Error as e:
                st.warning(f"Failed to save chat to history: {e}. Proceeding without saving.")
                print(f"Database insert error: {e}")
            
            st.session_state.last_input = query
            st.session_state.input_value = ""
            st.rerun()

# Close the database connection when the app shuts down
conn.close()
