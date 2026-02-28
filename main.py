import uvicorn
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Reviews Analyzer API")
app.include_router(router)




if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
