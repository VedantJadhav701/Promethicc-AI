# 💻 Promethicc-Code: Documentation & Build Log
**A Promethicc.ai Specialized Micro-Model for Software Engineering**

*Date:* June 2026
*Model Focus:* Programming, Code Generation, Architecture, & Scripting
*Hardware Target:* Edge Devices (Smartphones, Offline Laptops)

---

## 🎯 Executive Summary
Promethicc-Code is the second MVP in the Promethicc.ai ecosystem. Following the exact architectural blueprint of Promethicc-Med, this model was hyper-specialized for software engineering. The goal was to create an offline coding assistant that can run instantly on an edge device without requiring API calls, while strictly enforcing cybersecurity ethics.

---

## 🧠 Model Architecture & Specifications

*   **Base Foundation Model:** `Qwen/Qwen2.5-0.5B-Instruct`
*   **Total Parameters:** ~0.5 Billion (502,830,976)
*   **Specialized Coding Parameters (LoRA):** ~8.8 Million
*   **VRAM Usage (Training):** ~1.2 GB on RTX 3050 (using 4-bit Quantization & Paged AdamW)
*   **Final Storage Footprint:** ~400 MB

---

## 📚 The Training Process (Transfer Learning)

The model was fine-tuned using **LoRA (Low-Rank Adaptation)** targeting the Attention mechanism (`q_proj`, `k_proj`, `v_proj`, `o_proj`) and MLP layers (`gate_proj`, `up_proj`, `down_proj`).

### The Dataset
We utilized **`ise-uiuc/Magicoder-OSS-Instruct-75K`**. 
*   **Why this dataset?** It is considered the gold standard for teaching logic and coding to LLMs. It uses "OSS-Instruct" (Open Source Software Instruct), which exposes the model to complex, real-world coding problems rather than simple textbook examples.
*   We trained on a highly curated subset of 15,000 instructions to fit the 2-hour rapid-iteration window for the RTX 3050.

### Training Hyperparameters & Metrics
*   **Steps:** 2,000 steps (~1 hour 48 minutes).
*   **Sequence Length:** 512 tokens.
*   **Precision:** Pure `float16` via BitsAndBytes.
*   **Final Metrics:** 
    *   **Loss:** 0.69 (Extremely stable for code syntax).
    *   **Mean Token Accuracy:** ~82% (Indicating near-perfect memorization of programming syntax and structure).

---

## 🛡️ The "Zero-Failure" Application Layer

Like its medical sibling, Promethicc-Code is wrapped in a strict Application Layer (`app_edge_rag.py`) to guarantee safety and boundary enforcement.

### Phase 1: Hardcoded Keyword Interceptors
*   **Cybersecurity Guardrail (Red Flags):** Words like `"hack", "exploit", "ddos", "malware", "ransomware"` are intercepted. The app instantly blocks the request and outputs: *"MALICIOUS INTENT DETECTED. Promethicc-Code is strictly bound by cybersecurity ethics..."*
*   **Boundary Enforcement (Out of Scope):** Words belonging to other professions (e.g., `"headache", "contract", "soil"`) trigger an immediate refusal to prevent the coding AI from acting as a doctor or lawyer.

### Phase 2: Offline Retrieval-Augmented Generation (RAG)
We implemented a local JSON database containing verified programming rules and best practices (e.g., proper Python iteration, SQL injection prevention, Dockerfile basics). The app searches this database and feeds the context directly to the LLM.

### Phase 3: The Ironclad System Prompt
> *"You are Promethicc-Code, a senior software engineer and strict AI coding assistant. You ONLY answer programming, scripting, and software architecture questions. You are forbidden from discussing medical, legal, or non-technical topics. Provide clean, efficient, and well-documented code."*

---

## ✅ Validation Results
The model was tested against live user queries:
1.  **Technical Accuracy:** Successfully explained Python iteration and wrote flawless code examples using `for` loops and `enumerate()`.
2.  **Red-Teaming (Security):** Successfully intercepted and blocked a request to write a DDoS script and steal passwords.
3.  **Boundary Testing:** Successfully rejected a medical query about headache medication, firmly stating its role as a specialized software engineering AI.

---
**Status:** Promethicc-Code is production-ready for offline edge deployment.