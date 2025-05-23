# Assessing Medical AI: Evaluating Machine Translation in the Medical Domain with LLM-as-Judges

This repository contains the code of the work:

> **Assessing Medical AI: Evaluating Machine Translation in the Medical Domain with LLM-as-Judges** by Adrián Cuadrón, Aimar Sagasti and Maitane Urruela.

## Overview

This work presents an LLM-as-Judge approach to evaluate machine translation systems in the **medical domain**. We perform **pairwise comparisons** of translation outputs using large language models (LLMs), analyze their performance, and generate rankings based on LLM preferences.

---

## Repository Structure

```
.
├── codigo/
│   ├── llmAsJudge_translations_pairwise_evaluation.py
│   ├── parse_outputs_pairwise.py
├── data_outdomain/
│   ├── outputs/
│   ├── ranking/
|   ├── script/
│   └── data_full.json
├── prompts/
│   ├── guidelines_prompt.json
│   └── baseline_prompt_evaluation.json
├── outputs/
├── rankings/
```
## Brief Description
- `codigo/`: Contains the code we have used to perform the experiments.
- `data_outdomain/`: Includes sample data and adapted scripts for evaluating translation in a **non-medical domain**.
- `prompts/`: Contains the prompt templates used with the LLMs to perform the LLM-as-Judge with pairwise comparison.
- `outputs` and `ranking` include the results we have obtained with our experiments.
---

## How to get the LLM evaluation rankings

### 1. Pairwise Evaluation with LLM-as-Judge

Use the following script to evaluate translation outputs using an LLM. This performs **pairwise evaluation** on a JSON dataset using a specified prompt.

```bash
python codigo/llmAsJudge_translations_pairwise_evaluation.py \
    data/all_instances.json \
    prompts/baseline_prompt_evaluation.json \
    <model_name> \
    --batch=1 \
    --output_file="outputs/all_instances_evaluation_<model_name>_output.json"
```

- `<model_name>`: Name or identifier of the LLM (e.g., `aloe`, `latxa`).
- `--batch`: Batch size for processing (default: 1).
- `--output_file`: Path to save model's evaluation outputs.

The output will be a JSON file listing each comparison and the winner.

### 2. Parsing the Evaluation Outputs

To generate a **ranking CSV** from the LLM evaluation outputs:

```bash
python codigo/parse_outputs_pairwise.py outputs/all_instances_evaluation_<model_name>_output.json
```

This script generates a ranking CSV and saves it in the `rankings/` directory.

---



