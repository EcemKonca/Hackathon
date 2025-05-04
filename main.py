from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import google.generativeai as genai
import os
from models import Base
from database import engine
from routers.auth import router as auth_router

# load keys from .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini model
model = genai.GenerativeModel("gemini-1.5-pro")

# Start the FastAPI
app = FastAPI()

# Add Routers
app.include_router(auth_router)

# Create DB table
Base.metadata.create_all(bind=engine)


@app.post("/find-errors")
async def find_errors(code: str = Form(...)):
    prompt = f"Aşağıdaki Python kodundaki hataları bul ve açıkla:\n\n{code}"
    response = model.generate_content(prompt)
    return JSONResponse(content={"result": response.text})


@app.post("/generate-code")
async def generate_code(prompt: str = Form(...)):
    response = model.generate_content(f"Lütfen şu işlemi yapan bir Python kodu yaz: {prompt}")
    return JSONResponse(content={"result": response.text})


@app.post("/ask-question")
async def ask_question(question: str = Form(...)):
    response = model.generate_content(f"Python hakkında bir sorum var: {question}")
    return JSONResponse(content={"result": response.text})
