# RecruitAI backend

## Live India vacancies

The job board supports authorized Adzuna India results. Set these environment
variables before starting Flask:

```text
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

The board keeps the employer name, listing details, and Adzuna redirect URL so
the candidate applies on the original vacancy page. Arbeitnow and Remotive are
also used for additional live listings when available.

## Setup

Install the backend dependencies and start Flask from this directory:

```bash
pip install -r requirements.txt
python app.py
```

RecruitAI is available at `http://127.0.0.1:5000`. Flask serves the HTML, CSS,
and JavaScript frontend from the backend project, so no separate frontend
server is required.

## Environment variables

Create `backend/.env` locally and add the values needed for your environment:

```text
GEMINI_KEY=your_gemini_api_key
SECRET_KEY=replace_with_a_random_secret
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

The chat assistant sends messages from the landing page to `POST /api/ai/chat`.
Gemini generates conversational answers when `GEMINI_KEY` is configured; the
application uses local fallback responses if the AI service is unavailable.

Never commit `.env` or real API keys. Use placeholder values in documentation
or a `.env.example` file instead.