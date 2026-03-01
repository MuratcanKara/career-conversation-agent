import os
import sqlite3
from pydantic import BaseModel  
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
from pypdf import PdfReader
import gradio as gr
from datetime import datetime

load_dotenv(override=True)

def push(message, title="career_conversation bildirimi"):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "title": title,
            "message": message
        }
    )

def record_user_details(email, name="Isim saglanmadi", notes="not yok"):
    push(f"{name} isimli kullanici {email} email adresiyle, {notes} notuyla kaydedildi!")
    return {"Recorded": "Ok"}

def record_unknown_question(question):
    push(f"Su soruyu cevaplayamadim: {question}")
    return {"Recorded": "Ok"}

def request_meeting(email, preferred_time, name="Isim saglanmadi", topic="Genel"):
    record_user_details(email, name, notes=f"Otomatik kayit - Toplanti talebi: {topic}")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"""
    📅 Yeni Toplantı Talebi
    ━━━━━━━━━━━━━━━━
    👤 İsim: {name}
    📧 Email: {email}
    🕐 Talep Edilen Zaman: {preferred_time}
    📝 Konu: {topic}
    ⏰ Talep Zamanı: {current_time}
    """
    push(message, title="📅 Toplanti Istegi")
    return {"Recorded": "Ok"}

def get_resume_link():
    return {"resume_url": "https://drive.google.com/file/d/1_DXZ96gj4pYDCObR3aAyw-D90s--zsRg/view?usp=sharing"}

def search_knowledge_database(query):
    
    conn = sqlite3.connect('my_knowledge.db')
    cursor = conn.cursor()
    sql_query = "select answer from faq where question like ?"
    cursor.execute(sql_query, (f"%{query}%",))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {"found": True, "answer": result[0]}
    else:
        return {"found": False, "answer": "No relevant information found in the database."}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Save user contact info. ONLY use when user explicitly provides email. IF this tool is already called before DO NOT call it again",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of that user"
            },
            "name": {
                "type": "string",
                "description": "The name of that user, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this tool when you couldn't answer the question as you didn't know. USE the email and the name of the user IF they were provided in the chat history before",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The exact question the user asked that you couldn't answer"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

request_meeting_json = {
    "name": "request_meeting",
    "description": "Schedule a meeting. STRICTLY REQUIRED: Name, Email, Preferred Time.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of that user"
            },
            "preferred_time": {
                "type": "string",
                "description": "It is the date and time of that mentioned meeting"
            },
            "name": {
                "type": "string",
                "description": "The name of the user that want to schedule a meeting"
            },
            "topic": {
                "type": "string",
                "description": "The topic of the meeting"
            }
        },
        "required": ["email", "name", "preferred_time"],
        "additionalProperties": False
    }
}

get_resume_link_json = {
    "name": "get_resume_link",
    "description": "Use that tool when the user asks about my CV",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}

search_knowledge_database_json = {
    "name": "search_knowledge_database",
    "description": "Search for Muratcan's specific tech stack, projects, or background info.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The specific keyword or topic to search for (e.g., 'internship', 'skills', 'win-back', 'github')."
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": request_meeting_json},
        {"type": "function", "function": get_resume_link_json},
        {"type": "function", "function": search_knowledge_database_json}]

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Muratcan Kara"
        reader = PdfReader("me/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
    
    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            if tool:
                try:
                    result = tool(**arguments)
                except Exception as e:
                    result = {"error": f"Tool execution failed: {str(e)}"}
            else:
                result = {"error": "Tool not found"}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results
    
    def evaluator_system_prompt(self):
        system_prompt = f"""
You are a Quality Control Bot. Verify the Agent's last action.

### CHECKLIST (Pass/Fail):
1. **Did Agent book a meeting?**
   - IF YES: Did the user explicitly provide an EMAIL in the chat history?
   - IF NO EMAIL in history but meeting booked -> **FAIL** (Reason: Missing Email).

2. **Did Agent invent info?**
   - IF Agent mentioned skills/dates not in source text -> **FAIL**.

3. **Is Date Correct?**
   - Current Year is 2026. If Agent used 2025 -> **FAIL**.

4. **Disrespectful Tone:** 
   - User provided a name (e.g., "Başak") but Agent replied informally (e.g., "Merhaba Başak") instead of formal ("Başak Hanım").

5. **Redundancy:** 
   -The user already gave their Name/Email previously, but the Agent asked for it again.

6. **Gender Assumption:** 
   -Agent used "Beyefendi", "Hanımefendi" without proof.

7. **Apology detected:**
   -Agent said "Özür dilerim" or similar reactive/weak phrases.


Reply with JSON: {{"is_acceptable": bool, "feedback": "string"}}
"""
    
        return system_prompt

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt

    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}, {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = self.openai.beta.chat.completions.parse(model="gpt-4o-mini", messages=messages, response_format=Evaluation)
        return response.choices[0].message.parsed

    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content

    def system_prompt(self):
        system_prompt = f"""
You are the AI Representative for {self.name}. 
Current Date: {datetime.now().strftime("%Y-%m-%d")} (Year is 2026).

### KNOWLEDGE BASE (Source of Truth):
- Summary: {self.summary}
- LinkedIn: {self.linkedin}

### PROTOCOL (Execute in Order):

1. **SMART CONTEXT CHECK (CRITICAL):**
   - **Before asking ANY question:** Scan the entire chat history.
   - **Rule:** IF the user has ALREADY provided their Name or Email in previous messages, **DO NOT ASK AGAIN.** Use the existing info.
   - **Example:** If user said "I'm Ahmet" 3 turns ago, and now wants a meeting, DO NOT say "What is your name?". Instead say: "Ahmet Bey, toplantı için..."

2. **ACTION EFFICIENCY (No Duplicates):**
   - IF you have already called `record_user_details` for this user, **DO NOT call it again** unless the user explicitly changed their info.
   - Just acknowledge: "Bilgileriniz bende mevcut, direkt toplantı aşamasına geçiyorum."

3. **MEETING RULE:**
   - Check: Do I have Name? Do I have Email? Do I have Time?
   - **IF MISSING:** Ask ONLY for the missing piece. (e.g., "Ahmet Bey, saati de belirtirseniz kaydı oluşturacağım.")
   - **IF COMPLETE:** Call `request_meeting` immediately.

4. **DATE AWARENESS:**
   - If user says "tomorrow", calculate date based on {datetime.now().strftime("%Y-%m-%d")}.
   - Never use 2024 or 2025.

5. **TOOL RULES (STRICT):**
   - **Meeting Request:**
     * IF user provides Name + Email + Time -> Call `request_meeting`.
     * IF ANY is missing -> DO NOT call tool. ASK the user for missing info.
     * NEVER invent an email.
   
   - **Knowledge Search:**
     * IF question is about Muratcan's skills/projects -> Call `search_knowledge_database`.
     * IF answer is not in DB -> Call `record_unknown_question` and apologize.

6. **SCOPE:**
   - Answer questions about Muratcan's projects, skills (Python, Agentic AI), and resume.
   - Use `search_knowledge_database` for specific career details.
   - Polite refusal for off-topic (e.g., general coding help, recipes).

7. **TONE & FORMALITY (CRITICAL):**
   - You are PROACTIVE and RESPONSIBLE.
   - You DO NOT give reactive responses.
   - **ZERO APOLOGY POLICY:** Never say "Özür dilerim", "Kusura bakmayın" or "Üzgünüm". If a mistake is pointed out, simply acknowledge it and pivot to the correct professional path.
   - **GENDER NEUTRALITY:** Never assume the user's gender. Never use "Beyefendi", "Hanımefendi" or gender-specific honorifics UNLESS the user provides a name or explicitly states their gender. Use "Siz" and stay neutral.
   - **Turkish:** EXTREMELY FORMAL. Always use honorifics.
     * Wrong: "Merhaba Başak"
     * Right: "Merhaba Başak Hanım" or "Başak Hanım"
   - **English:** Professional and polite.
   - Professional, confident engineering student.
   - Match user's language (TR/EN).

### GOAL:
Represent Muratcan professionally to HRs (like Mercedes, Aselsan). Don't be a chatbot, be a professional assistant.
"""

        return system_prompt

    def chat(self, message, history):
        messages = [{"role": "system","content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            finish_reason = response.choices[0].finish_reason
            if finish_reason=="tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True
        ai_reply = response.choices[0].message.content
        evaluation = self.evaluate(ai_reply, message, history)
        if evaluation.is_acceptable:
            print("Passed evaluation - returning reply")
            return ai_reply
        else:
            print("Failed evaluation - regenerating response")
            return self.rerun(ai_reply, message, history, evaluation.feedback)

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()