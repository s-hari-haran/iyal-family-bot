import json
import os
import httpx
import sys
import copy
from dotenv import load_dotenv

# Load backend .env containing BOLNA_API_KEY
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

API_KEY = os.getenv("BOLNA_API_KEY")
if not API_KEY:
    print("Error: BOLNA_API_KEY is missing in backend/.env!")
    exit(1)

# Read tunnel URL from argument or default to active localtunnel
if len(sys.argv) > 1:
    NGROK_URL = sys.argv[1].strip()
else:
    NGROK_URL = "https://tired-bikes-shout.loca.lt"

print(f"Loaded Bolna API Key: {API_KEY[:6]}...{API_KEY[-4:]}")
print(f"Target Tunnel URL:    {NGROK_URL}")

if not NGROK_URL:
    print("Error: Tunnel URL is required!")
    exit(1)

# Clean trailing slash
if NGROK_URL.endswith("/"):
    NGROK_URL = NGROK_URL[:-1]

# Load working agent template downloaded from API
template_path = os.path.join(os.path.dirname(__file__), "existing_agent.json")
prompts_path = os.path.join(os.path.dirname(__file__), "..", "bolna", "system_prompts.json")

if not os.path.exists(template_path):
    print(f"Error: working agent template {template_path} not found!")
    exit(1)

with open(template_path, "r", encoding="utf-8") as f:
    template = json.load(f)

with open(prompts_path, "r", encoding="utf-8") as f:
    prompts = json.load(f)

# Update basic fields
template["agent_name"] = "Family Financial Memory OS Assistant"
template["agent_welcome_message"] = "Hello! Welcome back to your family money memory. Who is speaking today, and how can I help you?"
template["webhook_url"] = f"{NGROK_URL}/api/webhook/bolna"

# Update prompts
template["agent_prompts"] = {
    "task_1": {
        "system_prompt": prompts["en"]["system_prompt"]
    }
}

task = template["tasks"][0]

# =============================================================================
# API TOOLS CONFIGURATION — All 9 tools registered
#
# Key design decisions:
# 1. call_id uses %(call_sid)s — system-injected by Bolna, NOT LLM-generated
# 2. phone_number removed from LLM params — identity resolved by member_name
#    (voice confirmation: "Who is speaking today?")
# 3. member_name is used by the backend to resolve family_id via the members table
# =============================================================================

# A default phone number is hardcoded in the param template for tools that need it
# for family resolution. The LLM provides member_name for identity confirmation.
DEFAULT_FAMILY_PHONE = "%(user_number)s"

task["tools_config"]["api_tools"] = {
    "tools": [
        # ====== LOGGING TOOLS (write to database) ======
        {
            "name": "record_expense",
            "key": "custom_task",
            "description": "Logs a family expense. Use when the caller says they spent money on groceries, rent, utilities, fuel, tuition, or anything else. You must confirm the speaker's name first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Confirmed speaker name (Ramesh, Sunita, Hari, or Prakash)" },
                    "amount": { "type": "number", "description": "Amount spent in INR" },
                    "category": { "type": "string", "description": "Category: groceries, utilities, rent, fuel, tuition, misc" },
                    "description": { "type": "string", "description": "Brief note about the expense" },
                    "date": { "type": "string", "description": "Date of expense in YYYY-MM-DD format. Use today if not specified." },
                    "confidence": { "type": "number", "description": "Your confidence in the extraction accuracy (0.0 to 1.0). Default 0.9." }
                },
                "required": ["member_name", "amount", "category"]
            }
        },
        {
            "name": "record_debt",
            "key": "custom_task",
            "description": "Logs a borrowing or lending transaction. Use when someone says they borrowed from or lent money to someone. Extract lender and borrower names carefully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Confirmed speaker name" },
                    "lender_name": { "type": "string", "description": "Person who lent money" },
                    "borrower_name": { "type": "string", "description": "Person who borrowed money" },
                    "amount": { "type": "number", "description": "Loan amount in INR" },
                    "due_date": { "type": "string", "description": "Repayment due date YYYY-MM-DD" },
                    "note": { "type": "string", "description": "Notes on the loan" },
                    "confidence": { "type": "number", "description": "Extraction confidence (0.0 to 1.0)" }
                },
                "required": ["member_name", "lender_name", "borrower_name", "amount"]
            }
        },
        {
            "name": "goal_update",
            "key": "custom_task",
            "description": "Adds money to a savings goal. Use when the caller says 'Add 2000 to the emergency fund' or 'Put 5000 towards vacation savings'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Confirmed speaker name" },
                    "goal_name": { "type": "string", "description": "Name of the savings goal (vacation savings, emergency fund, education fund, vehicle goal)" },
                    "amount": { "type": "number", "description": "Amount to contribute in INR" },
                    "confidence": { "type": "number", "description": "Extraction confidence (0.0 to 1.0)" }
                },
                "required": ["member_name", "goal_name", "amount"]
            }
        },
        # ====== RETRIEVAL TOOLS (read-only queries) ======
        {
            "name": "budget_status",
            "key": "custom_task",
            "description": "Checks remaining budget for a category. Use when the caller asks 'How much is left for groceries?' or 'Have we exceeded the fuel budget?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Speaker name for family identification" },
                    "category": { "type": "string", "description": "Budget category: groceries, utilities, fuel, tuition" }
                },
                "required": ["member_name", "category"]
            }
        },
        {
            "name": "spending_summary",
            "key": "custom_task",
            "description": "Gets spending summary by category or member. Use when caller asks 'How much did we spend on groceries this month?', 'What was our largest expense?', or 'How much did Ramesh spend this week?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Speaker name for family identification" },
                    "category": { "type": "string", "description": "Optional: filter by category (groceries, fuel, etc.)" },
                    "timeframe": { "type": "string", "description": "Time period: 'week' or 'month'. Default is 'month'." },
                    "largest_only": { "type": "boolean", "description": "Set true if asking for the single largest expense" }
                },
                "required": ["member_name"]
            }
        },
        {
            "name": "financial_summary",
            "key": "custom_task",
            "description": "Gets a holistic family financial overview including total spending, top categories, outstanding debts, and savings goal progress. Use when caller asks 'Give me a family financial update' or 'How are we doing financially?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Speaker name for family identification" }
                },
                "required": ["member_name"]
            }
        },
        {
            "name": "goal_status",
            "key": "custom_task",
            "description": "Checks progress on a specific savings goal. Use when caller asks 'How is the vacation savings going?' or 'How much do we have in the emergency fund?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Speaker name for family identification" },
                    "goal_name": { "type": "string", "description": "Name of the savings goal (vacation savings, emergency fund, education fund, vehicle goal)" }
                },
                "required": ["member_name", "goal_name"]
            }
        },
        {
            "name": "debt_guidance",
            "key": "custom_task",
            "description": "Provides advice on debt priorities and repayment strategy. Use when caller asks 'Which debts should we pay first?' or 'What is our debt situation?'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_name": { "type": "string", "description": "Speaker name for family identification" }
                },
                "required": ["member_name"]
            }
        },
        # ====== GUIDANCE TOOL ======
        {
            "name": "get_financial_literacy",
            "key": "custom_task",
            "description": "Explains safe Indian financial products: PPF, FD, RD, Sukanya Samriddhi Yojana, compound interest, emergency funds. Use when caller asks educational questions. NEVER give stock, crypto, or trading advice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": { "type": "string", "description": "Topic or concept to explain (PPF, FD, compound interest, etc.)" }
                },
                "required": ["query"]
            }
        }
    ],
    "tools_params": {
        # --- LOGGING TOOLS: include call_id via %(call_sid)s ---
        "record_expense": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/record-expense",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s",
                "amount": "%(amount)s",
                "category": "%(category)s",
                "description": "%(description)s",
                "date": "%(date)s",
                "call_id": "%(call_sid)s",
                "confidence": "%(confidence)s"
            })
        },
        "record_debt": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/record-debt",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s",
                "lender_name": "%(lender_name)s",
                "borrower_name": "%(borrower_name)s",
                "amount": "%(amount)s",
                "due_date": "%(due_date)s",
                "note": "%(note)s",
                "call_id": "%(call_sid)s",
                "confidence": "%(confidence)s"
            })
        },
        "goal_update": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/goal-update",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s",
                "goal_name": "%(goal_name)s",
                "amount": "%(amount)s",
                "call_id": "%(call_sid)s",
                "confidence": "%(confidence)s"
            })
        },
        # --- RETRIEVAL TOOLS: read-only, no call_id needed ---
        "budget_status": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/budget-status",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s",
                "category": "%(category)s"
            })
        },
        "spending_summary": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/spending-summary",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "category": "%(category)s",
                "member_name": "%(member_name)s",
                "timeframe": "%(timeframe)s",
                "largest_only": "%(largest_only)s"
            })
        },
        "financial_summary": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/financial-summary",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s"
            })
        },
        "goal_status": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/goal-status",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s",
                "goal_name": "%(goal_name)s"
            })
        },
        "debt_guidance": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/debt-guidance",
            "api_token": None,
            "param": json.dumps({
                "phone_number": DEFAULT_FAMILY_PHONE,
                "member_name": "%(member_name)s"
            })
        },
        "get_financial_literacy": {
            "method": "POST",
            "url": f"{NGROK_URL}/api/tools/get-financial-literacy",
            "api_token": None,
            "param": json.dumps({
                "query": "%(query)s"
            })
        }
    }
}

# Configure multilingual system prompts
multilingual = task["tools_config"]["multilingual_config"]
languages = multilingual["languages"]

languages["en"]["system_prompt"] = prompts["en"]["system_prompt"]
languages["en"]["agent_name"] = "Ananya"
languages["en"]["handoff_message"] = "Sure, let's continue in English."

languages["hi"]["system_prompt"] = prompts["hi"]["system_prompt"]
languages["hi"]["agent_name"] = "Ananya"
languages["hi"]["handoff_message"] = "ठीक है, अब हम हिंदी में बात करेंगे।"

# Tamil block cloned from English, updated prompt, name, and handoff
languages["ta"] = copy.deepcopy(languages["en"])
languages["ta"]["transcriber"]["language"] = "ta"
languages["ta"]["system_prompt"] = prompts["ta"]["system_prompt"]
languages["ta"]["agent_name"] = "Ananya"
languages["ta"]["handoff_message"] = "சரி, நாம் தமிழில் பேசலாம்."

# Malayalam block cloned from English, updated prompt, name, and handoff
languages["ml"] = copy.deepcopy(languages["en"])
languages["ml"]["transcriber"]["language"] = "ml"
languages["ml"]["system_prompt"] = prompts["ml"]["system_prompt"]
languages["ml"]["agent_name"] = "Ananya"
languages["ml"]["handoff_message"] = "ശരി, നമുക്ക് മലയാളത്തിൽ സംസാരിക്കാം."

# Telugu block cloned from English, updated prompt, name, and handoff
languages["te"] = copy.deepcopy(languages["en"])
languages["te"]["transcriber"]["language"] = "te"
languages["te"]["system_prompt"] = prompts["te"]["system_prompt"]
languages["te"]["agent_name"] = "Ananya"
languages["te"]["handoff_message"] = "సరే, మనం తెలుగులో మాట్లాడుకుందాం."

# Default active language and primary transcriber language
multilingual["active_language"] = "en"
task["tools_config"]["transcriber"]["language"] = "en"

# Build payload
agent_config = {}
for k, v in template.items():
    if k not in ["id", "created_at", "updated_at", "agent_prompts"]:
        agent_config[k] = v

payload = {
    "agent_config": agent_config,
    "agent_prompts": template["agent_prompts"]
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("Uploading configuration to Bolna v2 API...")
print(f"Tools registered: {len(task['tools_config']['api_tools']['tools'])}")
for tool in task['tools_config']['api_tools']['tools']:
    print(f"  - {tool['name']}: {tool['description'][:60]}...")

try:
    response = httpx.post("https://api.bolna.ai/v2/agent", json=payload, headers=headers, timeout=30.0)
    
    if response.status_code in [200, 201]:
        data = response.json()
        agent_id = data.get('agent_id') or data.get('id')
        print("\n=== DEPLOYMENT SUCCESSFUL ===")
        print(f"Agent Name: {agent_config['agent_name']}")
        print(f"Agent ID:   {agent_id}")
        print(f"Status:     {data.get('status', 'created')}")
        print("=============================")
        
        # Link agent to inbound phone number +919262171465
        inbound_payload = {
            "agent_id": agent_id,
            "phone_number_id": "14bfd1e1-b355-4f84-8db1-40859bb19ca9"
        }
        print(f"Linking agent {agent_id} to inbound phone number +919262171465 (ID: 14bfd1e1-b355-4f84-8db1-40859bb19ca9)...")
        try:
            inbound_response = httpx.post("https://api.bolna.ai/inbound/setup", json=inbound_payload, headers=headers, timeout=30.0)
            if inbound_response.status_code == 200:
                print("Inbound phone number linked successfully!")
                print(json.dumps(inbound_response.json(), indent=2))
            else:
                print(f"Failed to link inbound phone number. Status: {inbound_response.status_code}, Response: {inbound_response.text}")
        except Exception as inbound_err:
            print(f"Error linking inbound phone number: {inbound_err}")
            
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            current_data["id"] = agent_id
            current_data["agent_name"] = agent_config["agent_name"]
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(current_data, f, indent=2)
            print(f"Successfully updated agent ID to {agent_id} in {template_path}")
        except Exception as file_err:
            print(f"Error saving agent ID to template: {file_err}")
    else:
        print(f"\n=== DEPLOYMENT FAILED ===")
        print(f"HTTP Status: {response.status_code}")
        print(f"Response:    {response.text}")
        print("=========================")
except Exception as e:
    print(f"\nError contacting Bolna API: {e}")
