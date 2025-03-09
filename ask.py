import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableSequence
import psycopg2
import os
from dotenv import load_dotenv
import hashlib

# Load environment variables from .env file
load_dotenv()

# Function to hash passwords for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to initialize PostgreSQL database connection (using Neon)
def init_db():
    """Initialize PostgreSQL database connection to Neon and create or update necessary tables."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),  # e.g., "your_host.neon.tech"
            port=os.getenv("PG_PORT", "5432"),  # Default PostgreSQL port
            user=os.getenv("PG_USER"),  # e.g., "your_username"
            password=os.getenv("PG_PASSWORD"),  # e.g., "your_password"
            database="linkedin",
            sslmode="require"  # Neon requires SSL
        )
        c = conn.cursor()
        print("Connected to PostgreSQL database.")  # Debug
        
        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id VARCHAR(255) PRIMARY KEY, 
                     password VARCHAR(255), 
                     profile_data TEXT, 
                     job_data TEXT, 
                     career_goals TEXT)''')
        print("Checked/created 'users' table.")  # Debug
        
        # Ensure columns exist in users table (PostgreSQL doesn’t need this check as often, but included for compatibility)
        for column, col_type in [
            ('password', 'VARCHAR(255)'),
            ('profile_data', 'TEXT'),
            ('job_data', 'TEXT'),
            ('career_goals', 'TEXT')
        ]:
            c.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='{column}'")
            if not c.fetchone():
                c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
                print(f"Added '{column}' to 'users'.")  # Debug
        
        # Create session_history table
        c.execute('''CREATE TABLE IF NOT EXISTS session_history (
                     user_id VARCHAR(255), 
                     session_group VARCHAR(255), 
                     session_id SERIAL PRIMARY KEY, 
                     query TEXT, 
                     response TEXT, 
                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        print("Checked/created 'session_history' table.")  # Debug
        
        # Ensure session_group column exists in session_history
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='session_history' AND column_name='session_group'")
        if not c.fetchone():
            c.execute("ALTER TABLE session_history ADD COLUMN session_group VARCHAR(255)")
            print("Added 'session_group' to 'session_history'.")  # Debug
            c.execute("UPDATE session_history SET session_group = 'legacy_session' WHERE session_group IS NULL")
            print("Updated existing rows with 'legacy_session'.")  # Debug
        
        conn.commit()
        print("Database initialized successfully.")  # Debug only
        return conn, c
    except psycopg2.Error as err:
        st.error(f"Failed to connect to PostgreSQL: {err}")
        print(f"Database connection failed: {err}")  # Debug only
        return None, None

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

# Initialize database connection
conn, c = init_db()
if conn is None or c is None:
    st.error("Failed to connect to the database. Please check your credentials or try again later.")
    st.stop()

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
      - If the query contains "career guidance" or "counseling," provide career advice based on the profile ({profile_context}) and career_goals ({career_goals}), identifying missing skills and suggesting resources.
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

# Authentication
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
            hashed_password = hash_password(login_password)
            c.execute("SELECT profile_data, job_data, career_goals FROM users WHERE user_id=%s AND password=%s", (login_email, hashed_password))
            result = c.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.user_id = login_email
                st.session_state.profile_context = result[0] if result[0] else ""
                st.session_state.job_context = result[1] if result[1] else ""
                st.session_state.career_goals = result[2] if result[2] else ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Logged in successfully!")
                print(f"User {login_email} logged in. New session: {st.session_state.current_session}")
            else:
                st.error("Invalid email or password.")
        else:
            st.error("Please enter both email and password.")

    st.subheader("Sign Up")
    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    
    if st.button("Sign Up"):
        if signup_email and signup_password:
            hashed_password = hash_password(signup_password)
            try:
                c.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", (signup_email, hashed_password))
                conn.commit()
                st.session_state.logged_in = True
                st.session_state.user_id = signup_email
                st.session_state.profile_context = ""
                st.session_state.job_context = ""
                st.session_state.career_goals = ""
                st.session_state.chat_history = []
                st.session_state.current_session = f"session_{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]}"
                st.session_state.input_value = ""
                st.session_state.last_input = ""
                st.success("Account created and logged in!")
                print(f"User {signup_email} signed up. New session: {st.session_state.current_session}")
            except psycopg2.IntegrityError:
                st.error("Email already exists. Please log in.")
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
            c.execute("UPDATE users SET profile_data=%s WHERE user_id=%s", (profile_context, user_id))
            conn.commit()
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
            c.execute("UPDATE users SET job_data=%s WHERE user_id=%s", (job_context, user_id))
            conn.commit()
            st.success("Job details saved successfully!")
            print(f"Job saved for {user_id}: {job_context}")

        # Career Goals
        st.subheader("Career Goals")
        career_goals = st.text_area("Enter your career goals:", value=st.session_state.career_goals, key="goals")
        if st.button("Save Goals", key="save_goals"):
            if career_goals:
                st.session_state.career_goals = career_goals
                c.execute("UPDATE users SET career_goals=%s WHERE user_id=%s", (career_goals, user_id))
                conn.commit()
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

        st.subheader("Session History")
        try:
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
            st.warning(f"Could not load session history: {e}. Using basic session display.")
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
            try:
                c.execute("INSERT INTO session_history (user_id, session_group, query, response) VALUES (%s, %s, %s, %s)", 
                          (user_id, st.session_state.current_session, user_input, response_text))
                conn.commit()
            except psycopg2.Error as e:
                st.warning(f"Failed to save chat to history: {e}. Continuing without saving.")
                print(f"Insert into session_history failed: {e}")
            
            st.session_state.last_input = user_input
            st.session_state.input_value = ""
            st.rerun()

# Close database connection
conn.close()