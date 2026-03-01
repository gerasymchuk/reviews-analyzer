import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Reviews Analyzer API")
app.include_router(router)

@app.get("/")
async def root():
    return {
        "service": "Reviews Analyzer API",
        "endpoints": {
            "POST /collect": "Scrape and return raw reviews",
            "POST /analyse": "Analyse reviews with LLM",
            "POST /download": "Download reviews as CSV",
        }
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://huggingface.co", "https://*.hf.space"],
    allow_methods=["*"],
    allow_headers=["*"],
)




if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
