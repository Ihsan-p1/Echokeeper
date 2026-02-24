"""
LoRA Fine-Tuning script for NLLB-200
====================================
This script provides a scaffold to fine-tune NLLB-200 using LoRA (Low-Rank Adaptation)
to improve translation of slang and informal expressions.

Requirements:
    pip install transformers datasets peft accelerate bitsandbytes

Usage:
    python scripts/finetune_nllb.py --data data/slang_parallel.jsonl --epochs 3
"""

import argparse
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
)
from peft import LoraConfig, get_peft_model, TaskType

def finetune(data_path, model_id, output_dir, epochs, batch_size, lr):
    print(f"Loading model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_id,
        device_map="auto",
        # Use 8-bit quantization to save memory if needed (requires bitsandbytes)
        # load_in_8bit=True, 
    )

    # 1. Define LoRA Config
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"]
    )

    # 2. Wrap model with PEFT
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 3. Load and preprocess dataset
    dataset = load_dataset("json", data_files=data_path, split="train")

    def preprocess_function(examples):
        inputs = examples["src"]
        targets = examples["tgt"]
        
        # NLLB requires source/target language prefixes
        model_inputs = tokenizer(inputs, max_length=128, truncation=True)

        with tokenizer.as_target_tokenizer():
            labels = tokenizer(targets, max_length=128, truncation=True)

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    # 4. Define Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        learning_rate=lr,
        num_train_epochs=epochs,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="no",
        predict_with_generate=True,
        fp16=torch.cuda.is_available(),
        push_to_hub=False,
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # 5. Initialize Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # 6. Start Training
    print("Starting training...")
    trainer.train()

    # 7. Save the LoRA adapters
    final_output = os.path.join(output_dir, "lora_final")
    model.save_pretrained(final_output)
    print(f"Fine-tuning complete. LoRA adapters saved to {final_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRA Fine-tune NLLB-200")
    parser.add_argument("--data", default="data/slang_parallel.jsonl", help="Path to JSONL data")
    parser.add_argument("--model", default="facebook/nllb-200-distilled-1.3B", help="Base model ID")
    parser.add_argument("--output", default="models/nllb-slang-lora", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    
    args = parser.parse_args()
    
    finetune(args.data, args.model, args.output, args.epochs, args.batch_size, args.lr)
