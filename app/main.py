from fastapi import FastAPI
from app.api import user
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)


@app.get("/")
def root():
    return {"message": "Hello World pushing out to ubuntu"}

