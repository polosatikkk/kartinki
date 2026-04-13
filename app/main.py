from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routes import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Нить API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
