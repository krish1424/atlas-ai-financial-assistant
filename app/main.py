from fastapi import FastAPI

app = FastAPI(
    title="Atlas AI Financial Assistant",
    description="Conversational AI financial assistant",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Atlas AI Financial Assistant",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }