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

# Hey, loading the environment variables from our .env file here - keeps secrets safe!
load_dotenv()

# Setting up the Groq client - not using it for transcription anymore, but keeping it handy.
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Simple function to hash passwords - keeps things secure for user login.
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database setup function - connects to Neon PostgreSQL and gets tables ready.
def init_db():
    try:
        # Connecting to the Neon DB with all the credentials from .env
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT", "5432"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database="linkedin",
            sslmode="require"
        )
        c = conn.cursor()
        print("Nice, we’re in - connected to PostgreSQL!")
        
        # Creating the users table if it doesn’t exist yet
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id VARCHAR(255) PRIMARY KEY, 
                     password VARCHAR(255), 
                     profile_data TEXT, 
                     job_data TEXT, 
                     career_goals TEXT)''')
        print("Users table is good to go.")
        
        # Checking and adding any missing columns to users table - keeps it flexible
        for column, col_type in [
            ('password', 'VARCHAR(255)'),
            ('profile_data', 'TEXT'),
            ('job_data', 'TEXT'),
            ('career_goals', 'TEXT')
        ]:
            c.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='{column}'")
            if not c.fetchone():
                c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
                print(f"Added {column} to users table - wasn’t there before!")
        
        # Setting up session_history table for chat logs
        c.execute('''CREATE TABLE IF NOT EXISTS session_history (
                     user_id VARCHAR(255), 
                     session_group VARCHAR(255), 
                     session_id SERIAL PRIMARY KEY, 
                     query TEXT, 
                     response TEXT, 
                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        print("Session history table is set.")
        
        # Making sure session_group column exists - older data might not have it
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='session_history' AND column_name='session_group'")
        if not c.fetchone():
            c.execute("ALTER TABLE session_history ADD COLUMN session_group VARCHAR(255)")
            print("Added session_group to session_history.")
            c.execute("UPDATE session_history SET session_group = 'legacy_session' WHERE session_group IS NULL")
            print("Updated old rows with a default session group.")
        
        conn.commit()
        print("DB setup done - we’re ready to roll!")
        return conn, c
    except psycopg2.Error as err:
        st.error(f"Uh-oh, couldn’t connect to PostgreSQL: {err}")
        print(f"DB connection failed: {err}")
        return None, None

# Handy function to format profile data into a neat string
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

# Same deal for job data - keeps it clean and readable
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

# Converts text to audio with gTTS - pretty cool for audio output option
def text_to_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        st.error(f"Couldn’t generate audio: {e}")
        return None

# Let’s get that DB connection going
conn, c = init_db()
if conn is None or c is None:
    st.error("Database connection failed - check your credentials!")
    st.stop()

# Setting up the Groq LLM - this is our brain for text responses
llm = ChatGroq(model="llama3-70b-8192", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# Here’s the beefy prompt - detailed instructions for the LLM to nail responses
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

# Chaining the prompt with the LLM - makes it all flow together
unified_chain = RunnableSequence(unified_prompt | llm)

# Kicking off the Streamlit app - simple title to start
st.title("LinkedIn Optimizer Chat")

# Login state setup - gotta track who’s in and their session
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

# If they’re not logged in, show the login/signup screens
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
                # User’s in! Set up their session
                st.session_state.logged_in = True
                st.session_state.user_id = login_email
                st.session_state.profile_context = result[0] if result[0] else ""
                st.session_state.job_context = result[1] if result[1] else ""
                st.session_state.career_goals = result[2] if result[2] else ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Logged in - welcome aboard!")
                print(f"User {login_email} logged in. Session: {st.session_state.current_session}")
                st.rerun()
            else:
                st.error("Wrong email or password - try again.")
        else:
            st.error("Fill in both fields, please!")

    st.subheader("Sign Up")
    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    
    if st.button("Sign Up"):
        if signup_email and signup_password:
            hashed_password = hash_password(signup_password)
            try:
                c.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", (signup_email, hashed_password))
                conn.commit()
                # New user’s ready - log them in right away
                st.session_state.logged_in = True
                st.session_state.user_id = signup_email
                st.session_state.profile_context = ""
                st.session_state.job_context = ""
                st.session_state.career_goals = ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Signed up and logged in - let’s get started!")
                print(f"User {signup_email} signed up. Session: {st.session_state.current_session}")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("That email’s taken - log in instead.")
        else:
            st.error("Need an email and password to sign up!")
else:
    user_id = st.session_state.user_id

    # Sidebar stuff - profile, job, goals, and session controls
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
            st.success("Profile saved - looking good!")
            print(f"Profile saved for {user_id}: {profile_context}")

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
            st.success("Job details saved - all set!")
            print(f"Job saved for {user_id}: {job_context}")

        st.subheader("Career Goals")
        career_goals = st.text_area("Enter your career goals:", value=st.session_state.career_goals, key="goals")
        if st.button("Save Goals", key="save_goals"):
            if career_goals:
                st.session_state.career_goals = career_goals
                c.execute("UPDATE users SET career_goals=%s WHERE user_id=%s", (career_goals, user_id))
                conn.commit()
                st.success("Goals saved - nice vision!")
                print(f"Career goals saved for {user_id}: {career_goals}")
            else:
                st.error("Gotta write some goals first!")

        st.subheader("Session Management")
        if st.button("Create New Session", key="new_session"):
            st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
            st.session_state.chat_history = []
            st.session_state.input_value = ""
            st.session_state.last_input = ""
            st.success("Fresh session started!")
            print(f"New session for {user_id}: {st.session_state.current_session}")

        st.subheader("Session History")
        try:
            # Grabbing session summaries for the user
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
            st.warning(f"Session history load failed: {e}. Falling back to basics.")
            print(f"History query bombed: {e}")
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

    # Main chat area - showing the session and what we can do
    st.markdown(f"**Current Session: {st.session_state.current_session[-8:]}**")
    st.markdown("I can help with profile analysis, job fit analysis, content enhancement, career counseling, or cover letter generation. What would you like to do?")

    # Displaying the chat history - user on right, assistant on left
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

    # Input form - just text now, nice and simple
    with st.form(key="chat_form", clear_on_submit=True):
        st.write("Ask your question:")
        user_input = st.text_input("Type your question:", key="chat_input", value="", label_visibility="collapsed")
        output_type = st.selectbox("Select output type:", ["Text", "Audio"], index=0, key="output_type")
        submit_button = st.form_submit_button(label="Ask")

        # When they hit submit, process the text input
        if submit_button and user_input:
            query = user_input
            # Building chat history string for context
            chat_history_str = "\n".join(
                f"{msg['role']}: {msg['content'][0] if isinstance(msg['content'], tuple) else msg['content']}"
                for msg in st.session_state.chat_history
            ) if st.session_state.chat_history else "No previous chat history in this session."

            # Firing off the query to the LLM
            response = unified_chain.invoke({
                "query": query,
                "profile_context": st.session_state.profile_context or "No profile data provided.",
                "job_context": st.session_state.job_context or "No job data provided.",
                "career_goals": st.session_state.career_goals or "No career goals provided.",
                "chat_history": chat_history_str
            })

            response_text = response.content if hasattr(response, 'content') else str(response)

            # Handling output type - text or audio
            if output_type == "Audio":
                audio_data = text_to_audio(response_text)
                if audio_data:
                    response_content = (response_text, audio_data)
                else:
                    response_content = response_text
            else:
                response_content = response_text

            # Adding to chat history
            st.session_state.chat_history.append({"role": "You", "content": query})
            st.session_state.chat_history.append({"role": "Assistant", "content": response_content})

            # Saving to DB - gotta keep that history!
            try:
                c.execute("INSERT INTO session_history (user_id, session_group, query, response) VALUES (%s, %s, %s, %s)", 
                          (user_id, st.session_state.current_session, query, response_text))
                conn.commit()
            except psycopg2.Error as e:
                st.warning(f"Couldn’t save to history: {e}. Moving on anyway.")
                print(f"DB insert failed: {e}")
            
            st.session_state.last_input = query
            st.session_state.input_value = ""
            st.rerun()

# Finally closing the DB connection
conn.close()