from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Docker Template",
    description="FastAPI project with Docker and CI/CD",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def health():
    return {"status": "ok"}
