# LinkedIn Optimizer Chat

Welcome to the LinkedIn Optimizer Chat—an AI-powered application I developed to assist users in optimizing their LinkedIn profiles, assessing job fit, and gaining career insights. Designed as part of an assignment, this tool offers a straightforward chat interface with memory capabilities to maintain conversation context. I’m pleased with its functionality and hope it proves valuable to you as well.

Built with Streamlit for the frontend, Groq’s LLM for processing, and Neon PostgreSQL for data persistence, it’s a practical solution for career enhancement. Below, I’ll outline its features, architecture, setup process, and potential improvements.

## Features

- **Chat Interface**: Engage via text input, with responses delivered as text or audio for flexibility.
- **Profile Optimization**: Input your profile details (e.g., skills, experience) to receive analysis or enhancements.
- **Job Fit Analysis**: Enter job specifics to get a match score (0-100) and tailored suggestions.
- **Career Guidance**: Share goals for personalized advice on skill gaps and next steps.
- **Cover Letter Generation**: Request custom cover letters based on your profile and job data.
- **Memory**: Retains chat history within sessions and across logins via database storage.

Note: This tool relies on manual data entry rather than direct LinkedIn URL fetching due to integration constraints.

## Tech Stack

- **Streamlit**: Drives the user interface for quick deployment and simplicity.
- **LangChain + Groq**: Employs `llama3-70b-8192` for efficient, intelligent responses.
- **Neon PostgreSQL**: Manages user data and chat history in a cloud-hosted database.
- **gTTS**: Converts text to audio for optional voice output.
- **Python**: Integrates all components effectively.

See `requirements.txt` for the complete dependency list.

## Architecture (High Level)

The application is structured for usability and reliability:
- **Frontend**: Streamlit provides a chat window and sidebar. Users input queries in the chat and manage profile, job, and goal data via forms, with responses styled for readability.
- **Backend**: Groq’s LLM, integrated through LangChain’s `RunnableSequence`, processes queries using a detailed prompt that leverages user data and history for context-aware answers.
- **Storage**: Neon PostgreSQL stores user profiles (`users` table) and chat logs (`session_history` table with session grouping), while Streamlit’s `session_state` handles in-session context.
- **Flow**: Users log in, enter data, ask questions, and receive text or audio responses, with all interactions saved for continuity.

## Local Setup

Here’s how to run it on your machine.

### Prerequisites
- Python 3.8+
- Git
- Groq API Key ([Groq signup](https://groq.com))
- Neon PostgreSQL database ([Neon signup](https://neon.tech))

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Prasad14-hub/linkedin-optimizer.git
   cd linkedin-optimizer
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   - Create a `.env` file in the root:
     ```
     GROQ_API_KEY=your-groq-api-key
     PG_HOST=your-neon-host
     PG_PORT=5432
     PG_USER=your-neon-username
     PG_PASSWORD=your-neon-password
     ```
   - Obtain these from Groq and Neon dashboards.

5. **Launch the App**:
   ```bash
   streamlit run ask.py
   ```
   Access it at `http://localhost:8501`. Check the terminal for errors if it fails to load.

### Troubleshooting
- **Database Issues**: Verify Neon credentials and connectivity.
- **API Failures**: Ensure the Groq key is correct.
- **Port Conflicts**: Adjust if 8501 is in use.

## Deployment on Streamlit Cloud

To host it online:
1. **Push to GitHub**:
   ```bash
   git add ask.py requirements.txt
   git commit -m "Prepared for Streamlit Cloud"
   git push origin main
   ```

2. **Deploy**:
   - Log into [Streamlit Cloud](https://streamlit.io/cloud).
   - New app > Select `Prasad14-hub/linkedin-optimizer`, branch `main`, file `ask.py`.
   - Add secrets in “Advanced settings”:
     ```
     GROQ_API_KEY=your-groq-api-key
     PG_HOST=your-neon-host
     PG_PORT=5432
     PG_USER=your-neon-username
     PG_PASSWORD=your-neon-password
     ```
   - Deploy and test the generated URL.

## Usage

- **Login/Signup**: Use an email and password to access the app.
- **Data Entry**: Input profile, job, and goal details in the sidebar and save.
- **Queries**: Ask questions like “analyze my profile,” “job fit,” or “cover letter.”
- **Output**: Choose text or audio responses.
- **Sessions**: Manage conversations via new or existing sessions in the sidebar.

## Future Enhancements

- **LinkedIn Integration**: Add URL parsing with API access.
- **Voice Input**: Reimplement with a stable library.
- **Dynamic Data**: Incorporate real-time job trends.
- **Multi-Agent**: Split tasks across specialized agents.

Feel free to explore or contribute—feedback is welcome via GitHub issues.

Thank you,  
Prasad Gavhane
