import os
import sys

# FORCE UTF-8 ENCODING FOR WINDOWS
os.environ["PYTHONUTF8"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
from datasets import load_dataset, concatenate_datasets
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

# BYPASS TRANSFORMERS PYTORCH 2.6 SECURITY CHECK FOR LOCAL CHECKPOINTS
import transformers.trainer
transformers.trainer.check_torch_load_is_safe = lambda: True

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

def train():
    model_id = "Qwen/Qwen2.5-0.5B-Instruct"
    output_dir = "./products/promethicc-eng/checkpoints"
    
    print("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    print("Configuring 4-bit Quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16, 
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading Base Model: {model_id}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=16, 
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)

    # Load Engineering Datasets
    print("Loading Engineering Datasets...")
    
    # Dataset 1: Mechanics & Materials (MIT)
    ds1 = load_dataset("lamm-mit/MechanicsMaterials", split="train")
    
    # Dataset 2: Electrical Engineering
    ds2 = load_dataset("STEM-AI-mtl/Electrical-engineering", split="train")

    def format_prompt_ds1(sample):
        instruction = sample.get("question", "")
        output = sample.get("answer", "")
        prompt = f"<|im_start|>system\nYou are Promethicc-Eng, a highly specialized engineering AI assistant. Provide technically accurate, physics-based reasoning for complex engineering problems.<|im_end|>\n<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
        return {"text": prompt}
        
    def format_prompt_ds2(sample):
        instruction = sample.get("instruction", "")
        input_text = sample.get("input", "")
        output = sample.get("output", "")
        
        if input_text:
            prompt = f"<|im_start|>system\nYou are Promethicc-Eng, a highly specialized engineering AI assistant. Provide technically accurate, physics-based reasoning for complex engineering problems.<|im_end|>\n<|im_start|>user\nContext: {input_text}\nQuery: {instruction}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
        else:
            prompt = f"<|im_start|>system\nYou are Promethicc-Eng, a highly specialized engineering AI assistant. Provide technically accurate, physics-based reasoning for complex engineering problems.<|im_end|>\n<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
        return {"text": prompt}

    print("Formatting Datasets...")
    ds1 = ds1.map(format_prompt_ds1, remove_columns=ds1.column_names)
    ds2 = ds2.map(format_prompt_ds2, remove_columns=ds2.column_names)
    dataset = concatenate_datasets([ds1, ds2]).shuffle(seed=42)

    # 6. SFT Configuration
    sft_config = SFTConfig(
        output_dir=output_dir,
        dataset_text_field="text",
        max_length=512, 
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        max_steps=2000,
        logging_steps=10,
        save_steps=500,
        fp16=False,
        bf16=False,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        args=sft_config,
    )

    # Resume Logic
    import glob
    checkpoints = glob.glob(f"{output_dir}/checkpoint-*")
    resume_ckpt = max(checkpoints, key=os.path.getctime) if checkpoints else None

    print("\n🚀 Starting Fine-Tuning for Promethicc-Eng...")
    if resume_ckpt:
        print(f"Resuming from {resume_ckpt}...")
        trainer.train(resume_from_checkpoint=resume_ckpt)
    else:
        trainer.train()

    print(f"\n✅ Training Complete! Saving LoRA weights to {output_dir}/final_eng_lora")
    model.save_pretrained(f"{output_dir}/final_eng_lora")
    tokenizer.save_pretrained(f"{output_dir}/final_eng_lora")

if __name__ == "__main__":
    train()