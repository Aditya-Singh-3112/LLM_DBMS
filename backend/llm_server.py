from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from fastapi import FastAPI, Request
import torch
import uvicorn

app = FastAPI()

token = "token"
model_name = "AdityaSingh312/sql-finetuned-model"
use_hf = True

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_use_double_quant=True,
    bnb_8bit_quant_type="nf4",
    bnb_8bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(model_name, token = token)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, device_map={"":0}, token=token)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    return_full_text=False,
    clean_up_tokenization_spaces=True
)

@app.post("/generate")
async def generate(req: Request):
    body = await req.json()
    prompt = body["inputs"]
    params = body.get("parameters", {"max_new_tokens": 300, "temperature": 0.7})
    if "temperature" in params and params["temperature"] <= 0:
        params["temperature"] = 0.7

    output = pipe(prompt, **params)
    return {"generated_text" : output[0]["generated_text"]}

if __name__ == "__main__":
    uvicorn.run("llm_server:app", port = 8080, reload = True)