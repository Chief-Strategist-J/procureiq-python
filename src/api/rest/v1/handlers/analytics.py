from fastapi import APIRouter, HTTPException, status
from src.features.analytics.schemas import TimeSeriesAnalysisRequest, TimeSeriesAnalysisResponse
from src.features.analytics.service import TimeSeriesAnalyzer

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.post("/time-series", response_model=TimeSeriesAnalysisResponse)
def analyze_time_series(request: TimeSeriesAnalysisRequest):
    try:
        return TimeSeriesAnalyzer.analyze_klines(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Time Series Analytics Error: {str(e)}"
        )
