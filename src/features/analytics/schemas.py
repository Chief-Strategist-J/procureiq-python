from pydantic import BaseModel
from typing import List, Optional

class KlineItem(BaseModel):
    openTime: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    closeTime: int

class TimeSeriesAnalysisRequest(BaseModel):
    symbol: str
    interval: str
    forecastHorizon: int = 12
    klines: List[KlineItem]

class TimeSeriesAnalysisResponse(BaseModel):
    symbol: str
    interval: str
    dataPointsCount: int
    meanPrice: float
    priceVolatility: float
    trendDirection: str
    forecastPrices: List[float]
