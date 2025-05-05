from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import google.generativeai as genai
import os

# DB ve auth için (kullanıyorsan)
from models import Base
from database import engine
from routers.auth import router as auth_router

# Ortam değişkenlerini yükle
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini AI Modeli
model = genai.GenerativeModel("gemini-1.5-pro")

# FastAPI uygulaması
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="GIZLI_BIR_KEY")
app.include_router(auth_router)  # Auth router ekliyoruz (varsa)

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

# Şablonlar klasörü
templates = Jinja2Templates(directory="templates")


# Ana sayfa
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


# Çıkış
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


# AI: Kod Hata Analizi (Gemini)
@app.post("/analyze_code", response_class=HTMLResponse)
async def analyze_code(request: Request, user_code: str = Form(...)):
    prompt = f"Aşağıdaki Python kodundaki hataları bul ve açıkla:\n\n{user_code}"
    response = model.generate_content(prompt)
    return templates.TemplateResponse("analyze_result.html", {
        "request": request,
        "prompt": user_code,
        "response": response.text
    })


# AI: Kod Üretme (Gemini)
@app.post("/generate_code", response_class=HTMLResponse)
async def generate_code(request: Request, prompt_input: str = Form(...)):
    response = model.generate_content(f"Lütfen şu işlemi yapan bir Python kodu yaz: {prompt_input}")
    return templates.TemplateResponse("generate_result.html", {
        "request": request,
        "prompt": prompt_input,
        "response": response.text
    })


# AI: Python Soru Yanıtlama (Gemini)
@app.post("/ask_python", response_class=HTMLResponse)
async def ask_python(request: Request, question_input: str = Form(...)):
    response = model.generate_content(f"Python hakkında bir sorum var: {question_input}")
    return templates.TemplateResponse("ask_result.html", {
        "request": request,
        "prompt": question_input,
        "response": response.text
    })
