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
# GUARDRAILS & RAG ENGINE (CODING SPECIALIZATION)
# ---------------------------------------------------------
RED_FLAG_WORDS = ["hack", "exploit", "ddos", "malware", "ransomware", "bypass authentication", "steal passwords"]
OUT_OF_SCOPE_WORDS = ["headache", "doctor", "lawyer", "contract", "soil", "crop", "medicine", "fever", "heart attack"]

def load_offline_db():
    db_path = "./products/promethicc-code/offline_database.json"
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
            return "SECURITY_VIOLATION"
    for flag in OUT_OF_SCOPE_WORDS:
        if flag in query_lower:
            return "OUT_OF_SCOPE"
    return "SAFE"

# ---------------------------------------------------------
# APPLICATION LAYER
# ---------------------------------------------------------
def launch_app():
    base_model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    lora_path = "./products/promethicc-code/checkpoints/final_code_lora"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Booting Promethicc-Code Core Engine...")
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    base_model = AutoModelForCausalLM.from_pretrained(base_model_id, torch_dtype=torch.float16, device_map="auto")
    
    if os.path.exists(lora_path):
        model = PeftModel.from_pretrained(base_model, lora_path)
    else:
        print("⚠️ Warning: LoRA weights not found. Running raw Base Model for testing.")
        model = base_model
        
    model.eval()
    db = load_offline_db()
    
    print("\n" + "="*60)
    print("💻 Promethicc-Code APP: Zero-Failure Edition")
    print("Features Active: [Cybersecurity Guardrails] [Boundary Enforcement] [Offline RAG]")
    print("="*60)

    while True:
        user_input = input("\nDeveloper Query: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # PHASE B: GUARDRAIL INTERCEPTION
        status = check_guardrails(user_input)
        if status == "SECURITY_VIOLATION":
            print("\n🚨 SYSTEM OVERRIDE 🚨")
            print("MALICIOUS INTENT DETECTED.")
            print("Promethicc-Code is strictly bound by cybersecurity ethics and will not assist in generating exploits or malicious code.")
            continue
        elif status == "OUT_OF_SCOPE":
            print("\nPromethicc-Code: I am a specialized software engineering AI. I am strictly programmed to deny requests regarding medical, legal, or non-technical subjects. Please ask a programming question.")
            continue
            
        # PHASE C: OFFLINE RAG RETRIEVAL
        context = retrieve_context(user_input, db)
        
        # IRONCLAD SYSTEM PROMPT
        sys_prompt = "You are Promethicc-Code, a senior software engineer and strict AI coding assistant. You ONLY answer programming, scripting, and software architecture questions. You are forbidden from discussing medical, legal, or non-technical topics. Provide clean, efficient, and well-documented code. "
        if context:
            sys_prompt += f"Use ONLY the following verified textbook context to answer the user: {context} "
        else:
            sys_prompt += "If the user asks for non-programming topics, you MUST reply: 'I am a coding AI. I cannot assist with that.'"

        prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        print("Promethicc-Code: \n", end="", flush=True)
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=300, temperature=0.2, do_sample=True, pad_token_id=tokenizer.eos_token_id)
            
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(response)

if __name__ == "__main__":
    launch_app()