# LinkedIn Optimizer Chat

Hey there! Welcome to my LinkedIn Optimizer Chat—a neat little AI-powered tool I built to help folks like you polish up their LinkedIn profiles, figure out how well they match jobs, and get some solid career advice. It’s all wrapped up in a chat interface that’s easy to use and remembers what you’ve talked about. I made this as part of an assignment, and I’m pretty stoked with how it turned out—hope you find it useful too!

I went with Streamlit for the frontend because it’s quick to spin up, hooked it up to Groq’s LLM for the brains, and tied it all together with a Neon PostgreSQL database for keeping track of things. Let’s dive into what it can do and how you can get it running.

## What It Does

Here’s the rundown of what this app brings to the table:

- **Chat Interface**: You type in your questions, and it chats back with answers—either as text or audio if you’re feeling fancy. It’s all conversational, like talking to a career coach.
- **Profile Optimization**: Feed it your profile details (think name, skills, experience), and ask it to analyze or spruce them up. It’ll tell you what’s missing or how to make it pop.
- **Job Fit Analysis**: Got a job in mind? Enter its details, and it’ll compare your profile to the gig, give you a match score (0-100), and suggest tweaks to close the gap.
- **Career Guidance**: Share your career goals, and it’ll dish out advice—think skill gaps or next steps to level up.
- **Cover Letters**: Need a cover letter? It’ll whip one up tailored to your profile and the job you’re eyeing.
- **Memory**: It keeps track of your chats in-session and saves them to a database, so you can pick up where you left off anytime.

Fair warning: it doesn’t fetch LinkedIn URLs directly (that’s a whole other beast), so you’ll need to paste in your details manually. Still gets the job done, though!

## Tech Stack

- **Streamlit**: Powers the UI—simple, clean, and gets us a chat window fast.
- **LangChain + Groq**: The AI magic happens here with `llama3-70b-8192`—fast responses and solid reasoning.
- **Neon PostgreSQL**: Stores user data and chat history—reliable and cloud-hosted.
- **gTTS**: Turns text responses into audio when you want to hear it out loud.
- **Python**: Ties it all together—because who doesn’t love Python?

Check `requirements.txt` for the full list of goodies you’ll need.

## Getting It Running Locally

Alright, let’s get this thing up and running on your machine. It’s pretty straightforward—just follow these steps.

### What You’ll Need
- **Python 3.8+**: Make sure you’ve got a recent version installed.
- **Git**: To grab the code from GitHub.
- **Groq API Key**: Sign up at [Groq](https://groq.com) to get one—it’s free for basic use.
- **Neon PostgreSQL**: Head to [Neon](https://neon.tech), set up a free database, and grab the connection details.

### Step-by-Step Setup
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/Prasad14-hub/linkedin-optimizer.git
   cd linkedin-optimizer
   ```
   Boom, you’ve got the code on your machine!

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
   Keeps things tidy—don’t skip this!

3. **Install the Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   This pulls in Streamlit, LangChain, and everything else listed in `requirements.txt`.

4. **Configure Environment Variables**:
   - Create a `.env` file in the project root (it’s ignored by Git, so no worries about secrets leaking).
   - Add these lines with your own details:
     ```
     GROQ_API_KEY=your-groq-api-key-here
     PG_HOST=your-neon-host
     PG_PORT=5432
     PG_USER=your-neon-username
     PG_PASSWORD=your-neon-password
     ```
   - You’ll find these in your Groq dashboard and Neon console. Double-check them—typos will trip you up.

5. **Fire It Up**:
   ```bash
   streamlit run ask.py
   ```
   Open your browser to `http://localhost:8501`, and you’re in! If it doesn’t load, check your terminal for error messages—usually a missing key or DB issue.

### Troubleshooting
- **DB Connection Fails**: Make sure your Neon credentials are spot-on and the database is live.
- **API Errors**: Verify your Groq key—copy-paste can sometimes add sneaky spaces.
- **Port Issues**: If 8501 is busy, Streamlit will suggest another—just roll with it.

## Deploying to Streamlit Cloud

Want it live on the web? Here’s how to host it on Streamlit Cloud—it’s free and takes about 5 minutes.

1. **Push to GitHub**:
   - Make sure `ask.py` and `requirements.txt` are in your repo.
   ```bash
   git add ask.py requirements.txt
   git commit -m "Ready for Streamlit Cloud"
   git push origin main
   ```

2. **Set Up on Streamlit Cloud**:
   - Log into [Streamlit Cloud](https://streamlit.io/cloud) with your GitHub account.
   - Click “New app” and pick `Prasad14-hub/linkedin-optimizer`.
   - Set:
     - Branch: `main`
     - Main file: `ask.py`
   - Go to “Advanced settings” and add your secrets (same as the `.env` file):
     ```
     GROQ_API_KEY=your-groq-api-key-here
     PG_HOST=your-neon-host
     PG_PORT=5432
     PG_USER=your-neon-username
     PG_PASSWORD=your-neon-password
     ```
   - Hit “Deploy!” and wait a minute or two. You’ll get a URL like `https://linkedin-optimizer-prasad.streamlit.app`.

3. **Test It**: Visit the URL, log in, and play around. Check the logs in Streamlit Cloud if anything goes wonky.

## How to Use It

- **Login/Sign Up**: Use an email and password—first time, sign up; after that, log in.
- **Fill in Details**: Hit the sidebar to add your profile (name, skills, etc.), job details, and career goals. Save each section.
- **Chat Away**: Type stuff like:
  - “Analyze my profile” (checks what you’ve got).
  - “Job fit” (compares profile to job).
  - “Improve profile” (rewrites your sections).
  - “Career guidance” (tips based on goals).
  - “Cover letter” (custom letter for your job).
- **Output Choice**: Pick “Text” or “Audio” before hitting “Ask”—audio’s neat if you’re multitasking!
- **Sessions**: Create new sessions or load old ones from the sidebar—history’s saved for you.

## What’s Next?

This is a solid start, but there’s room to grow:
- **LinkedIn Integration**: Parsing profile/job URLs would be slick—needs an API or scraping setup.
- **Voice Input**: I tried mic and file uploads but hit UI snags—could revisit with a better library.
- **Dynamic Data**: Fetching live job postings or trends would make it next-level—maybe a job board API?
- **Multi-Agent**: Right now, it’s one LLM doing everything—splitting tasks across agents could sharpen it up.

Feel free to fork this and add your own spin—I’d love to see where it goes! Hit me up with questions or feedback at [your-email-if-you-want] or just open an issue here.

Happy optimizing!
—Prasad

### How to Use It
1. **Copy**: Click and drag from the start (`# LinkedIn Optimizer Chat`) to the end (`—Prasad`), or triple-click anywhere in the block to select it all. Then `Ctrl+C` or right-click > Copy.
2. **Paste**: In VS Code, open `README.md`, click inside, and `Ctrl+V` or right-click > Paste. Save with `Ctrl+S`.
3. **Push**:
   ```bash
   git add README.md
   git commit -m "Added detailed README for submission"
   git push origin main
   ```

Let me know once it’s in your repo, and we’ll move to the next step (e.g., `.gitignore`)! How’s it looking so far?
