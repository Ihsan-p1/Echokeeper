# EchoKeeper: High-Performance Local Translation Engine

EchoKeeper is a private, high-performance translation service designed for local execution. It leverages the NLLB-200 (No Language Left Behind) model by Meta AI to provide high-quality translations across 200 languages without requiring external internet access.

This repository specifically focuses on the EchoKeeper Discord Translator Bot and its integration with optimized local inference engines.

## Key Features

- **Privacy-First**: All translations are performed locally on your hardware. No data is sent to external APIs (Google, DeepL, etc.).
- **NLLB-200 Integration**: Supports the 1.3B parameter model for high-precision translations.
- **Slang Normalization**: Internal dictionary for Vietnamese and Indonesian informal registers to ensure natural translation output.
- **Performance Optimized**: Supports FP16 precision for significant speedups on NVIDIA GPUs.
- **Context-Aware**: Maintains conversation history for improved coherence and pronoun resolution.

## Technical Requirements

- **Python**: 3.8 or higher.
- **CUDA (Optional)**: Highly recommended for near-instant inference using the 1.3B model.
- **RAM/VRAM**: 
  - ~6GB for 1.3B model (FP16).
  - ~3GB for 600M model (FP16).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/EchoKeeper.git
   cd EchoKeeper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy the example file and fill in your Discord token:
   ```bash
   cp .env.example .env
   ```

## Configuration Guide

EchoKeeper can be configured via the `.env` file. Key parameters include:

| Variable | Description | Default |
|---|---|---|
| `ECHOKEEPER_BACKEND` | Selection of translation engine (`nllb` or `opus`). | `nllb` |
| `NLLB_MODEL_ID` | The HuggingFace model identifier. | `facebook/nllb-200-distilled-1.3B` |
| `ECHOKEEPER_FP16` | Enables half-precision inference on GPUs. | `true` |
| `DISCORD_TOKEN` | Your Discord Bot token for authentication. | Required |

## Usage

### Launching the CLI
For testing and quick translations, use the Command Line Interface:
```bash
python cli.py --mode vi-en
```

### Launching the Discord Bot
To deploy EchoKeeper on a Discord server:
```bash
python bot.py
```

## Maintenance & Fine-Tuning
The repository includes a fine-tuning scaffold in `scripts/finetune_nllb.py` for users wishing to further specialize the model on specific datasets.

