#---------------------------------------------------
# Import necessary libraries
#---------------------------------------------------

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import logging
from datasets import load_dataset
import pandas as pd
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from huggingface_hub import login, notebook_login

#---------------------------------------------------
# Setting up variables
#---------------------------------------------------

model_name = "meta-llama/Llama-2-7b-hf"
dataset = load_dataset("Clinton/Text-to-sql-v1")
use_hf = True
token = "Your_Token"  # Replace with your Hugging Face token

#---------------------------------------------------
# Bits and Bytes Configuration
#---------------------------------------------------

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_use_double_quant=True,
    bnb_8bit_quant_type="nf4",
    bnb_8bit_compute_dtype=torch.bfloat16
)

#---------------------------------------------------
# Model Loading and Tokenizer
#---------------------------------------------------

if use_hf:
    login(token)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="cuda",
        trust_remote_code=True,
        use_auth_token=token,
        torch_dtype=torch.bfloat16  # Use bfloat16 for better performance
    )
else:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="cuda",
        trust_remote_code=True
    )

#----------------------------------------------------
# Tokenizer Loading
#----------------------------------------------------
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True,
    token=token
)

tokenizer.pad_token = tokenizer.eos_token  # Set pad token to eos token

def tokenize_function(examples):
    
    text = examples["instruction"][0] +  examples["input"][0]

    tokenizer.pad_token = tokenizer.eos_token  # Ensure pad token is set

    tokenized_input = tokenizer(
        text,
        return_tensors = "np",
        padding = True
    )

    max_length = min(
        tokenized_input["input_ids"].shape[1],
        2048
    )

    tokenizer.trucation_side = "left"

    tokenized_input = tokenizer(
        text,
        max_length = max_length,
        return_tensors = "np",
        padding = "max_length",
        truncation = True
    )

    return tokenized_input

finetuning_dataset_loaded = dataset

tokenized_dataset = finetuning_dataset_loaded.map(
    tokenize_function,
    batched=True,
    batch_size=1,
    drop_last_batch=True
)

print(tokenized_dataset)

train_data = tokenized_dataset["train"]
# test_data = tokenized_dataset["test"]

print("Train data size:", len(train_data))
# print("Test data size:", len(test_data))

print(train_data)
# print(test_data)

#---------------------------------------------------
# Setting up Base model and PEFT for training
#---------------------------------------------------

base_model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, 
                                                  device_map={"":0}, token=token)

base_model.gradient_checkpointing_enable()
base_model = prepare_model_for_kbit_training(base_model)

def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
    )

config = LoraConfig(
    r=8, 
    lora_alpha=32, 
    target_modules=["q_proj", "v_proj"], 
    lora_dropout=0.05, 
    bias="none", 
    task_type="CAUSAL_LM"
)

base_model = get_peft_model(base_model, config)
print_trainable_parameters(base_model)

#---------------------------------------------------
# Training the model
#---------------------------------------------------

trainer = transformers.Trainer(
    model=base_model,
    train_dataset=train_data,
    args=transformers.TrainingArguments(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        warmup_steps=2,
        max_steps=200,
        learning_rate=1.5e-4,
        fp16=True,
        logging_steps=10,
        output_dir="outputs",
        optim="adafactor"
    ),
    data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
)
base_model.config.use_cache = False
trainer.train()

# add code to save the model