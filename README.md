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
   
Set Up a Virtual Environment:
   git clone https://github.com/Prasad14-hub/linkedin-optimizer.git
   cd linkedin-optimizer
