import os
import sys
import json
import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

os.environ["PYTHONUTF8"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ---------------------------------------------------------
# GUARDRAILS & RAG ENGINE
# ---------------------------------------------------------
RED_FLAG_WORDS = ["suicide", "kill myself", "heart attack", "stroke", "bleeding out", "overdose", "911"]
OUT_OF_SCOPE_WORDS = ["python", "script", "code", "java", "html", "c++", "write a program", "scrape", "beautifulsoup"]

def load_offline_db():
    db_path = "./products/promethicc-med/offline_database.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def retrieve_context(user_query, db):
    """Simple offline BM25/Jaccard approximation retriever."""
    query_words = set(re.findall(r'\w+', user_query.lower()))
    best_match = None
    highest_score = 0
    
    for concept, text in db.items():
        concept_words = set(re.findall(r'\w+', concept.lower()))
        # Check if concept is heavily mentioned in query
        overlap = len(query_words.intersection(concept_words))
        if overlap > highest_score:
            highest_score = overlap
            best_match = text
            
    if highest_score > 0:
        return best_match
    return None

def check_guardrails(user_query):
    query_lower = user_query.lower()
    for flag in RED_FLAG_WORDS:
        if flag in query_lower:
            return "EMERGENCY"
    for flag in OUT_OF_SCOPE_WORDS:
        if flag in query_lower:
            return "OUT_OF_SCOPE"
    return "SAFE"

# ---------------------------------------------------------
# APPLICATION LAYER
# ---------------------------------------------------------
def launch_app():
    base_model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    lora_path = "./products/promethicc-med/checkpoints/final_med_lora"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Booting Promethicc-Med Core Engine...")
    
    tokenizer = AutoTokenizer.from_pretrained(lora_path)
    base_model = AutoModelForCausalLM.from_pretrained(base_model_id, torch_dtype=torch.float16, device_map="auto")
    model = PeftModel.from_pretrained(base_model, lora_path)
    model.eval()
    
    db = load_offline_db()
    
    print("\n" + "="*60)
    print("🛡️ Promethicc-Med APP: Zero-Failure Edition")
    print("Features Active: [Emergency Guardrails] [Boundary Enforcement] [Offline RAG]")
    print("="*60)

    while True:
        user_input = input("\nPatient Query: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # PHASE B: GUARDRAIL INTERCEPTION
        status = check_guardrails(user_input)
        if status == "EMERGENCY":
            print("\n🚨 SYSTEM OVERRIDE 🚨")
            print("CRITICAL MEDICAL EMERGENCY DETECTED.")
            print("Please call 911 (or your local emergency number) or go to the nearest emergency room IMMEDIATELY.")
            continue
        elif status == "OUT_OF_SCOPE":
            print("\nPromethicc-Med: I am a specialized medical AI assistant. I am strictly programmed to deny requests regarding programming, coding, or non-medical subjects. Please ask a health-related question.")
            continue
            
        # PHASE C: OFFLINE RAG RETRIEVAL
        context = retrieve_context(user_input, db)
        
        # IRONCLAD SYSTEM PROMPT
        sys_prompt = "You are Promethicc-Med, a strict, specialized medical AI assistant. You ONLY answer medical questions. You are forbidden from writing code, scripts, or discussing non-medical topics. "
        if context:
            sys_prompt += f"Use ONLY the following verified textbook context to answer the user: {context} "
        else:
            sys_prompt += "If the user asks for programming or non-medical topics, you MUST reply: 'I am a medical AI. I cannot assist with that.'"

        prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        print("Promethicc-Med: ", end="", flush=True)
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.1, do_sample=True, pad_token_id=tokenizer.eos_token_id)
            
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(response)

if __name__ == "__main__":
    launch_app()