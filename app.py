from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI(title="QwQ-32B API", description="API for Qwen QwQ-32B-Preview model")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = "You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step."

class ChatResponse(BaseModel):
    response: str

# Load model function (to be called at startup)
@app.on_event("startup")
async def startup_event():
    global model, tokenizer
    model_name = "Qwen/QwQ-32B-Preview"
    
    # Load the model and tokenizer
    print("Loading model and tokenizer...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("Model and tokenizer loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        # Continue without model to allow container to start
        # We'll handle this in the endpoints

@app.get("/")
async def root():
    return {"status": "ok", "model": "QwQ-32B-Preview"}

@app.get("/health")
async def health():
    if model is None or tokenizer is None:
        return {"status": "initializing"}
    return {"status": "ready"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model is still initializing")
    
    try:
        # Prepare messages with system prompt
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        # Add user messages
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Apply chat template
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize inputs
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # Generate response
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=request.temperature > 0
        )
        
        # Extract only the newly generated tokens
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
        
        # Decode response
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)