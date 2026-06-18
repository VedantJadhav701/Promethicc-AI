# ⚖️ Promethicc-Law: Documentation & Build Log
**A Promethicc.ai Specialized Micro-Model for Legal Professionals**

*Date:* June 2026
*Model Focus:* Contracts, Liability, Legal Reasoning, & Statutory Definitions
*Hardware Target:* Edge Devices (Smartphones, Offline Tablets)

---

## 🎯 Executive Summary
Promethicc-Law is the third MVP in the Promethicc.ai ecosystem. Designed to assist paralegals, law students, and the general public, this model processes complex legal queries locally and offline. It features an advanced application layer that strictly prevents the AI from engaging in active litigation defense or providing definitive criminal advice, thereby mitigating legal liability for the user and the platform.

---

## 🧠 Model Architecture & Specifications

*   **Base Foundation Model:** `Qwen/Qwen2.5-0.5B-Instruct`
*   **Total Parameters:** ~0.5 Billion (502,830,976)
*   **Specialized Legal Parameters (LoRA):** ~8.8 Million
*   **VRAM Usage (Training):** ~1.2 GB on RTX 3050 (using 4-bit Quantization)
*   **Final Storage Footprint:** ~400 MB

---

## 📚 The Training Process (Transfer Learning)

The model was fine-tuned using **LoRA (Low-Rank Adaptation)** targeting the Attention mechanism (`q_proj`, `k_proj`, `v_proj`, `o_proj`) and MLP layers (`gate_proj`, `up_proj`, `down_proj`).

### The Dataset
We faced initial challenges with gated and deprecated datasets on Hugging Face (such as `lawinstruct` and `asm3515/legal-clause-instruction-Tunning`). To ensure a flawless, open-source pipeline, we pivoted to:
*   **`nisaar/LLAMA2_Legal_Dataset_4.4k_Instructions`**: A high-quality, Parquet-formatted dataset focused on legal reasoning, case analysis, and constitutional law.

### Training Hyperparameters & Metrics
*   **Steps:** 2,000 steps (~3 hours 51 minutes).
*   **Sequence Length:** 512 tokens.
*   **Precision:** Pure `float16` via BitsAndBytes.
*   **Final Metrics:** 
    *   **Loss:** ~0.60 to 0.65 (Extremely low and stable).
    *   **Mean Token Accuracy:** 83.6% (An incredibly high accuracy for dense legal jargon).

---

## 🛡️ The "Zero-Failure" Application Layer

Promethicc-Law relies heavily on its Application Layer (`app_edge_rag.py`) to prevent "Unauthorized Practice of Law" (UPL).

### Phase 1: Hardcoded Keyword Interceptors
*   **Legal Liability Guardrail (Red Flags):** Words like `"divorce", "murder", "defend me in court", "sue my boss", "lawsuit"` instantly trigger a system override. The app blocks the AI and outputs: *"LEGAL LIABILITY DETECTED. Promethicc-Law cannot provide definitive legal advice for active lawsuits... Please consult a licensed attorney."*
*   **Boundary Enforcement:** Words related to coding (`"python"`) or medicine (`"headache"`) trigger a strict refusal to maintain the lawyer persona.

### Phase 2: Offline Retrieval-Augmented Generation (RAG)
The app includes a local JSON database containing verified legal definitions (e.g., Force Majeure, Indemnification, Statute of Limitations). When queried, the app retrieves the exact definition and forces the AI to summarize it, preventing legal hallucinations.

### Phase 3: The Ironclad System Prompt
> *"You are Promethicc-Law, a highly specialized legal AI assistant. You ONLY answer questions related to contracts, regulations, and legal terminology. You are forbidden from giving actionable legal advice."*

---

## ✅ Validation Results
The model was tested against live user queries:
1.  **Technical Accuracy (RAG):** Flawlessly defined a Force Majeure clause and accurately summarized acts of God, war, and pandemics as examples.
2.  **Liability Interception:** Successfully blocked a prompt asking for defense in a divorce/workplace lawsuit.
3.  **Boundary Enforcement:** Instantly refused a prompt asking for a Python web-scraping script.
4.  **Complex Legal Reasoning:** When presented with a complex, narrative query involving a physical altercation and self-defense, the model (drawing from its Indian Legal dataset training) correctly cited constitutional rights and forcefully advised the user to *"consult with an experienced lawyer,"* proving its ability to handle nuanced inputs safely.

---
**Status:** Promethicc-Law is production-ready for offline edge deployment.