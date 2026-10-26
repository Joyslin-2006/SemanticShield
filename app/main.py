from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="SemanticShield")
app.include_router(router)
