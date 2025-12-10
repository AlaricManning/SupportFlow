# SupportFlow - Quick Start Guide

Get SupportFlow running locally in under 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/SupportFlow.git
cd SupportFlow
```

## Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Create virtual environment (Mac/Linux)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
copy .env.example .env    # Windows
# OR
cp .env.example .env      # Mac/Linux

# IMPORTANT: Edit .env and add your OpenAI API key
# Open .env in your text editor and set:
# OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 3: Start Backend

```bash
# Make sure you're in the backend directory with venv activated
cd backend
python -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✓ Knowledge base loaded successfully
```

Leave this terminal running and open a new one for the frontend.

## Step 4: Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

You should see:
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

## Step 5: Test the Application

1. **Open your browser** to http://localhost:3000

2. **Submit a test ticket:**
   - Name: John Doe
   - Email: john@example.com
   - Order ID: ORD-001 (optional)
   - Subject: Request refund for defective product
   - Message: I received a keyboard that doesn't work. I'd like a refund please.

3. **Watch the magic happen:**
   - Click "Submit Ticket"
   - Wait ~5 seconds for AI processing
   - You'll see your ticket number

4. **View the results:**
   - Click "View All Tickets"
   - See your ticket in the admin dashboard
   - Click "View" to see detailed agent traces

## What Just Happened?

Your ticket went through 5 AI agents:

1. **Triage Agent** - Classified it as a "refund_request" with "high" priority
2. **Research Agent** - Searched the knowledge base for refund policies
3. **Policy Agent** - Checked order ORD-001 for refund eligibility
4. **Response Agent** - Drafted a professional response
5. **Escalation Agent** - Decided if human review was needed

All of this happened in ~5 seconds!

## Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
- **Solution:** Make sure your virtual environment is activated and dependencies are installed:
  ```bash
  pip install -r requirements.txt
  ```

**Error:** `openai.AuthenticationError: Invalid API key`
- **Solution:** Check your `.env` file has the correct `OPENAI_API_KEY`

### Frontend won't start

**Error:** `Cannot find module 'react'`
- **Solution:** Install dependencies:
  ```bash
  cd frontend
  npm install
  ```

**Error:** `Port 3000 is already in use`
- **Solution:** Either stop the other process using port 3000, or change the port in `vite.config.js`

### Knowledge base not loading

**Error:** `✗ Failed to load knowledge base`
- **Solution:** This is usually fine for testing. The knowledge base loads from `knowledge_base/*.md` files. Make sure these files exist.

## Next Steps

### Customize the Knowledge Base

Edit the markdown files in `knowledge_base/` to match your business:
- `refund_policy.md`
- `shipping_policy.md`
- `product_warranty.md`
- `account_help.md`

Restart the backend to reload the knowledge base.

### Test Different Scenarios

Try tickets with different intents:

**Shipping Inquiry:**
```
Subject: Where is my order?
Message: I ordered a product 5 days ago and haven't received tracking info yet.
```

**Product Question:**
```
Subject: Does the keyboard have RGB lighting?
Message: I'm interested in buying the mechanical keyboard but need to know if it has customizable RGB.
```

**Account Issue:**
```
Subject: Can't reset my password
Message: The password reset email isn't arriving. I've checked spam folder.
```

### Explore the API

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

Try the endpoints:
- `GET /api/tickets` - List all tickets
- `GET /api/stats` - View system statistics
- `POST /api/tickets` - Create a ticket via API

### View Agent Traces

In the admin dashboard:
1. Click any ticket's "View" button
2. Scroll down to "Agent Execution Traces"
3. Click on each agent to see:
   - Input/output data
   - Reasoning
   - Tools used
   - Execution time
   - Confidence scores

This transparency is what makes SupportFlow special!

## What's Next?

- Read the full [README.md](README.md) for architecture details
- Explore the code in `backend/app/agents/`
- Customize the frontend in `frontend/src/pages/`
- Deploy to production (see [Deployment](#deployment) section in README)

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Contact: your.email@example.com

---

Happy building! 🚀
