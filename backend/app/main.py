from fastapi import FastAPI
from app.db.database import engine, Base
from app.api.v1 import auth, files

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini Google Drive")

app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Mini Google Drive API!"}