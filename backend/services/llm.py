import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

COMPANY_CONTEXT = """
You are Riya, an AI voice assistant for Synvolve Intellis.

Company: Synvolve Intellis
Products & Services:
1. Riya Voice Bot - AI-powered voice assistant for businesses
2. Website Development - Custom websites for companies
3. Synvoira - AI solutions platform
4. Fitviora - Fitness solutions platform

Your Task:
Collect user information in this exact order:
1. Name - if unclear, ask to spell it
2. Phone Number - ask digit by digit, then confirm
3. Company Name
4. Requirements - what they need

Rules:
- Be direct and natural. Keep responses under 20 words.
- Ask ONE question at a time.
- Don't say "thank you" or "got it" repeatedly.
- Don't ask users what products they offer - YOU provide the products.

Handling Product Questions:
If user asks "What products do you have?" or "What services?"
- List all 4 products briefly
- Then ask: "Would you like details on any of these?"

If user asks for details on a specific product:
- Explain that product in 2-3 sentences
- Ask: "Any other questions?"

If user says "no" or "not interested" or "don't want":
- Say: "No problem. Feel free to reach out to Synvolve Intellis if you need anything. Goodbye!"
- End conversation

If user says "no more questions" but is interested:
- Say: "Alright. May I have your name to proceed?"
- Then continue collecting info (name, phone, company, requirements)

Once all info collected:
- Confirm the details briefly
- Say: "Thank you. We'll contact you soon."
- End conversation

Be efficient. Be clear. Don't waste words.
"""

def extract_info(prompt, stage, current_data):
    """Extract user info based on conversation stage"""
    prompt_lower = prompt.lower()
    
    if stage == "name" and not current_data.get('name'):
        
        if any(keyword in prompt_lower for keyword in ['my name', 'naam', 'i am', 'this is', 'call me']):
            words = prompt.split()
            
            if len(words) >= 3 and all(len(w) <= 2 for w in words[-5:]):
                current_data['name'] = ''.join(words[-5:]).upper()
            else:
                
                for keyword in ['my name is', 'naam hai', 'i am', 'this is', 'call me']:
                    if keyword in prompt_lower:
                        name_part = prompt_lower.split(keyword)[-1].strip()
                        name_words = [w for w in name_part.split() if len(w) > 1 and w not in ['is', 'hai']]
                        if name_words:
                            current_data['name'] = ' '.join(name_words[:2]).title()
                            break
       
        elif len(prompt.split()) <= 6 and all(len(w) <= 2 for w in prompt.split()):
            current_data['name'] = ''.join(prompt.split()).upper()
    
    elif stage == "phone" and not current_data.get('phone'):
     
        digits = ''.join(c for c in prompt if c.isdigit())
        if len(digits) >= 10:
            current_data['phone'] = digits
    
    elif stage == "company" and not current_data.get('company'):
        # company name
        current_data['company'] = prompt.strip()
    
    elif stage == "requirements" and not current_data.get('requirements'):
        # requirements
        current_data['requirements'] = prompt.strip()
    
    return current_data

def ask_llm(prompt, lang='en', user_data=None):
    collected = user_data or {}
    
    # Detect if user is not interested
    not_interested_keywords = ['not interested', 'don\'t want', 'no thanks', 'not now', 'maybe later']
    if any(keyword in prompt.lower() for keyword in not_interested_keywords):
        if lang == 'ta':
            return "பரவாயில்லை. உங்களுக்கு ஏதேனும் தேவைப்பட்டால் Synvolve Intellis ஐ தொடர்பு கொள்ளுங்கள். நன்றி!", collected
        elif lang == 'hi':
            return "कोई बात नहीं। जरूरत हो तो Synvolve Intellis से संपर्क करें। धन्यवाद!", collected
        else:
            return "No problem. Feel free to reach out to Synvolve Intellis if you need anything. Goodbye!", collected
    
    # Determine stage and extract info
    if not collected.get('name'):
        stage = "name"
        collected = extract_info(prompt, stage, collected)
    elif not collected.get('phone'):
        stage = "phone"
        collected = extract_info(prompt, stage, collected)
    elif not collected.get('company'):
        stage = "company"
        collected = extract_info(prompt, stage, collected)
    elif not collected.get('requirements'):
        stage = "requirements"
        collected = extract_info(prompt, stage, collected)
    else:
        stage = "complete"
    
    context = f"Data collected: {json.dumps(collected)}\nStage: {stage}"
    full_prompt = f"{COMPANY_CONTEXT}\n\n{context}\nUser ({lang}): {prompt}\n\nRiya ({lang}):"
    
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama2",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 100
            }
        }
    )
    return response.json()["response"].strip(), collected
