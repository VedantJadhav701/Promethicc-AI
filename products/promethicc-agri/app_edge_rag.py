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
# GUARDRAILS & RAG ENGINE (AGRICULTURE SPECIALIZATION)
# ---------------------------------------------------------
RED_FLAG_WORDS = ["bomb", "poison people", "meth", "cocaine", "illegal drugs"]
OUT_OF_SCOPE_WORDS = ["python", "code", "doctor", "headache", "sue my boss", "lawyer", "divorce", "contract", "website"]

def load_offline_db():
    db_path = "./products/promethicc-agri/offline_database.json"
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
    lora_path = "./products/promethicc-agri/checkpoints/final_agri_lora"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Booting Promethicc-Agri Core Engine...")
    
    base_model = AutoModelForCausalLM.from_pretrained(base_model_id, torch_dtype=torch.float16, device_map="auto")
    
    if os.path.exists(lora_path):
        tokenizer = AutoTokenizer.from_pretrained(lora_path)
        model = PeftModel.from_pretrained(base_model, lora_path)
    else:
        print("⚠️ Warning: LoRA weights not found. Running raw Base Model for testing.")
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        model = base_model
        
    model.eval()
    db = load_offline_db()
    
    print("\n" + "="*60)
    print("🌾 Promethicc-Agri APP: Zero-Failure Edition")
    print("Features Active: [Safety Guardrails] [Boundary Enforcement] [Offline RAG]")
    print("="*60)

    while True:
        user_input = input("\nFarmer Query: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # PHASE B: GUARDRAIL INTERCEPTION
        status = check_guardrails(user_input)
        if status == "SECURITY_VIOLATION":
            print("\n🚨 SYSTEM OVERRIDE 🚨")
            print("ILLEGAL ACTIVITY DETECTED.")
            print("Promethicc-Agri is strictly for legal agricultural and farming assistance.")
            continue
        elif status == "OUT_OF_SCOPE":
            print("\nPromethicc-Agri: I am a specialized agricultural AI assistant. I am strictly programmed to deny requests regarding medical, legal, or software programming subjects. Please ask a farming-related question.")
            continue
            
        # PHASE C: OFFLINE RAG RETRIEVAL
        context = retrieve_context(user_input, db)
        
        # IRONCLAD SYSTEM PROMPT
        if context:
            sys_prompt = f"You are Promethicc-Agri, a highly specialized agricultural AI assistant. Provide accurate, practical farming, crop, and livestock advice. TEXTBOOK FACT: {context} You MUST use this textbook fact to answer."
        else:
            sys_prompt = "You are Promethicc-Agri, a highly specialized agricultural AI assistant. Provide accurate, practical farming, crop, and livestock advice."
            
        prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        print("Promethicc-Agri: \n", end="", flush=True)
        
        # Qwen uses <|im_end|> as the stop token
        im_end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=150, 
                temperature=0.1, # Drop temperature back down to prevent Chinese hallucinations
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True, 
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=[tokenizer.eos_token_id, im_end_id]
            )
            
        generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
        
        response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        print(response)

if __name__ == "__main__":
    launch_app()