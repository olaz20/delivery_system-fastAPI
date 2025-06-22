from fastapi import FastAPI
from app.api import user, order
from fastapi.middleware.cors import CORSMiddleware
from app.services.response import RequestIDMiddleware
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

app.add_middleware(RequestIDMiddleware)


app.include_router(user.router)
app.include_router(order.router)

@app.get("/")
def root():
    return {"message": "Hello World pushing out to ubuntu"}

