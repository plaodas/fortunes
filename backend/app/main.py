from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fortunes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_hour: int  # 0-23


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    # Return the dummy result structure specified in the prompt
    result = {
        "year": "乙卯",
        "month": "戊寅",
        "day": "辛巳",
        "hour": "乙卯",
        "nameAnalysis": {
            "tenkaku": 26,
            "jinkaku": 15,
            "chikaku": 11,
            "gaikaku": 22,
            "soukaku": 37,
            "summary": "努力家で晩年安定",
        },
    }
    return {"input": req.dict(), "result": result}
