from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  
from src.routes.chat_route import router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1",port = 8000)