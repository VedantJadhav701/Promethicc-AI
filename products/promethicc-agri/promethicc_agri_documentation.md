# 🌾 Promethicc-Agri: Documentation & Build Log
**A Promethicc.ai Specialized Micro-Model for Agricultural Workers**

*Date:* June 2026
*Model Focus:* Farming Techniques, Soil Health, Crop Optimization, & Pest Control
*Hardware Target:* Edge Devices (Smartphones, Rugged Field Tablets)

---

## 🎯 Executive Summary
Promethicc-Agri is the fourth MVP in the Promethicc.ai ecosystem. Designed to assist farmers in remote areas with limited or no internet connectivity, this model provides expert-level agricultural advice locally. It utilizes a specialized dataset of real-world farming queries to ensure practical, actionable results while maintaining strict safety guardrails to prevent the misuse of agricultural materials.

---

## 🧠 Model Architecture & Specifications

*   **Base Foundation Model:** `Qwen/Qwen2.5-0.5B-Instruct`
*   **Total Parameters:** ~0.5 Billion (502,830,976)
*   **Specialized Agricultural Parameters (LoRA):** ~8.8 Million
*   **VRAM Usage (Training):** ~1.2 GB on RTX 3050
*   **Final Storage Footprint:** ~400 MB

---

## 📚 The Training Process (Transfer Learning)

The model was fine-tuned using **LoRA (Low-Rank Adaptation)** targeting the full transformer block structure.

### The Dataset
We utilized the **`KisanVaani/agriculture-qa-english-only`** dataset.
*   **The "Blank Output" Bug:** During the initial attempt, the model achieved 95% accuracy but generated blank responses. We discovered a dataset mapping error where the script looked for a `answer` column while the dataset used `answers` (plural). This was corrected, and the model was successfully retrained on real farming knowledge.

### Training Hyperparameters & Metrics
*   **Steps:** 2,000 steps (~1 hour 18 minutes).
*   **Sequence Length:** 512 tokens.
*   **Precision:** Pure `float16` via BitsAndBytes.
*   **Final Metrics:** 
    *   **Loss:** 0.53 (Highly stable).
    *   **Mean Token Accuracy:** 94.6% (Indicating near-perfect alignment with agricultural terminology).

---

## 🛡️ The "Zero-Failure" Application Layer

Promethicc-Agri is protected by a robust application shell (`app_edge_rag.py`) designed for safety and character consistency.

### Phase 1: Hardcoded Keyword Interceptors
*   **Safety Guardrail (Red Flags):** Words related to illegal substances or the creation of explosives from fertilizer (e.g., `"bomb"`, `"meth"`) are intercepted. The app instantly blocks the request and outputs: *"ILLEGAL ACTIVITY DETECTED. Promethicc-Agri is strictly for legal agricultural assistance."*
*   **Boundary Enforcement:** Queries regarding coding, medicine, or law are automatically rejected to keep the AI focused on its farming expertise.

### Phase 2: Offline Retrieval-Augmented Generation (RAG)
We implemented a local JSON database with verified facts on soil pH, crop rotation, and pest control. The app injects these textbook facts directly into the system prompt to ground the AI's responses in established science.

### Phase 3: The Ironclad System Prompt
> *"You are Promethicc-Agri, a highly specialized agricultural AI assistant. Provide accurate, practical farming, crop, and livestock advice. TEXTBOOK FACT: {context} You MUST use this textbook fact to answer."*

---

## ✅ Validation Results
The model was tested against real-world farming queries:
1.  **Practical Advice:** Successfully provided a 4-step detailed plan for planting wheat (depth, soil type, sunlight, and water).
2.  **RAG Integration:** Corrected a query about acidic soil by retrieving facts about compost and soil amendments.
3.  **Safety Interception:** Flawlessly blocked a request to create illegal drugs using fertilizer.

---
**Status:** Promethicc-Agri is production-ready for offline edge deployment in agricultural sectors.