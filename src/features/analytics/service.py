import numpy as np
from src.features.analytics.schemas import TimeSeriesAnalysisRequest, TimeSeriesAnalysisResponse

class TimeSeriesAnalyzer:
    
    @staticmethod
    def analyze_klines(request: TimeSeriesAnalysisRequest) -> TimeSeriesAnalysisResponse:
        if not request.klines:
            return TimeSeriesAnalysisResponse(
                symbol=request.symbol,
                interval=request.interval,
                dataPointsCount=0,
                meanPrice=0.0,
                priceVolatility=0.0,
                trendDirection="NEUTRAL",
                forecastPrices=[]
            )
        
        close_prices = [k.close for k in request.klines]
        prices_arr = np.array(close_prices)
        
        mean_price = float(np.mean(prices_arr))
        volatility = float(np.std(prices_arr) / mean_price) if mean_price > 0 else 0.0
        
        # Simple Linear Regression / Trend Estimation
        x = np.arange(len(prices_arr))
        slope, _ = np.polyfit(x, prices_arr, 1)
        
        if slope > 0.05:
            trend = "BULLISH"
        elif slope < -0.05:
            trend = "BEARISH"
        else:
            trend = "SIDEWAYS"
            
        # Exponential Smoothing Forecast Model (Simulating Google TimeSeries)
        alpha = 0.3
        last_price = prices_arr[-1]
        forecast = []
        current = last_price
        
        for i in range(1, request.forecastHorizon + 1):
            current = alpha * (last_price + slope * i) + (1 - alpha) * current
            forecast.append(round(float(current), 4))
            
        return TimeSeriesAnalysisResponse(
            symbol=request.symbol,
            interval=request.interval,
            dataPointsCount=len(request.klines),
            meanPrice=round(mean_price, 4),
            priceVolatility=round(volatility, 4),
            trendDirection=trend,
            forecastPrices=forecast
        )
