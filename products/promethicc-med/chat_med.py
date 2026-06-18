import os
import sys

# FORCE UTF-8 ENCODING FOR WINDOWS
os.environ["PYTHONUTF8"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def chat():
    base_model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    lora_path = "./products/promethicc-med/checkpoints/final_med_lora"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading Promethicc-Med onto {device}...")
    
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(lora_path)
    
    # 2. Load Base Model (in 16-bit to fit easily in VRAM)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # 3. Merge Specialized Medical Brain (LoRA) into Base Brain
    print("Fusing medical expertise into base brain...")
    model = PeftModel.from_pretrained(base_model, lora_path)
    model.eval()
    
    print("\n" + "="*50)
    print("🩺 Promethicc-Med is Online (Type 'quit' to exit)")
    print("="*50)

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # Format exactly like training
        prompt = f"<|im_start|>system\nYou are Promethicc-Med, a specialized medical AI assistant. Give precise, professional medical advice.<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        print("Promethicc-Med: ", end="", flush=True)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=250,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
        # Cut off the prompt from the output
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(response)

if __name__ == "__main__":
    chat()
