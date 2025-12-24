"""
FRED (Federal Reserve Economic Data) Data Source Module
========================================================

Fetches macroeconomic indicators from the Federal Reserve Bank of St. Louis.

Author: Rajesh Kumar Gupta
"""

import os
import logging
from typing import Dict, List, Any, Generator, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import requests

from .base_source import (
    BaseDataSource, DataSourceType, DataSourceRegistry,
    FetchedDocument, DocumentMetadata, EconomicDataPoint
)

logger = logging.getLogger(__name__)


# FRED Series Definitions
FRED_SERIES = {
    "GDP": {
        "name": "Gross Domestic Product",
        "description": "US GDP in billions of dollars",
        "unit": "Billions of Dollars",
        "frequency": "Quarterly",
        "category": "Output and Income",
    },
    "UNRATE": {
        "name": "Unemployment Rate",
        "description": "US civilian unemployment rate",
        "unit": "Percent",
        "frequency": "Monthly",
        "category": "Employment",
    },
    "CPIAUCSL": {
        "name": "Consumer Price Index",
        "description": "Consumer Price Index for All Urban Consumers",
        "unit": "Index 1982-1984=100",
        "frequency": "Monthly",
        "category": "Prices",
    },
    "FEDFUNDS": {
        "name": "Federal Funds Rate",
        "description": "Federal Funds Effective Rate",
        "unit": "Percent",
        "frequency": "Monthly",
        "category": "Interest Rates",
    },
    "UMCSENT": {
        "name": "Consumer Sentiment",
        "description": "University of Michigan Consumer Sentiment",
        "unit": "Index 1966:Q1=100",
        "frequency": "Monthly",
        "category": "Consumer",
    },
    "T10Y2Y": {
        "name": "10-Year/2-Year Treasury Spread",
        "description": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity",
        "unit": "Percent",
        "frequency": "Daily",
        "category": "Interest Rates",
    },
    "VIXCLS": {
        "name": "VIX Index",
        "description": "CBOE Volatility Index: VIX",
        "unit": "Index",
        "frequency": "Daily",
        "category": "Financial",
    },
    "DGS10": {
        "name": "10-Year Treasury Rate",
        "description": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
        "unit": "Percent",
        "frequency": "Daily",
        "category": "Interest Rates",
    },
    "HOUST": {
        "name": "Housing Starts",
        "description": "Housing Starts: Total: New Privately Owned Housing Units Started",
        "unit": "Thousands of Units",
        "frequency": "Monthly",
        "category": "Housing",
    },
    "INDPRO": {
        "name": "Industrial Production Index",
        "description": "Industrial Production: Total Index",
        "unit": "Index 2017=100",
        "frequency": "Monthly",
        "category": "Production",
    },
}


@DataSourceRegistry.register(DataSourceType.FRED)
class FREDDataSource(BaseDataSource):
    """
    Data source for Federal Reserve Economic Data (FRED).
    
    Fetches macroeconomic indicators including GDP, unemployment,
    inflation, interest rates, and more.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.stlouisfed.org/fred")
        self.api_key = config.get("api_key") or os.environ.get("FRED_API_KEY", "")
        self.default_series = config.get("series", list(FRED_SERIES.keys())[:6])
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate configuration"""
        if not self.api_key:
            logger.warning("FRED API key not provided. Some functionality may be limited.")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """Make API request to FRED"""
        url = f"{self.base_url}/{endpoint}"
        params["api_key"] = self.api_key
        params["file_type"] = "json"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"FRED API request failed: {e}")
            return {}
    
    def get_series_info(self, series_id: str) -> Optional[Dict]:
        """Get information about a FRED series"""
        if series_id in FRED_SERIES:
            return FRED_SERIES[series_id]
        
        # Fetch from API if not in local definitions
        data = self._make_request("series", {"series_id": series_id})
        if data.get("seriess"):
            series = data["seriess"][0]
            return {
                "name": series.get("title", series_id),
                "description": series.get("notes", ""),
                "unit": series.get("units", ""),
                "frequency": series.get("frequency", ""),
                "category": "",
            }
        return None
    
    def get_series_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[EconomicDataPoint]:
        """
        Get observations for a FRED series.
        
        Args:
            series_id: FRED series identifier
            start_date: Start date for observations
            end_date: End date for observations
            limit: Maximum number of observations
            
        Returns:
            List of EconomicDataPoint objects
        """
        observations = []
        
        # Default date range: last 5 years
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=5*365)
        
        params = {
            "series_id": series_id,
            "observation_start": start_date.strftime("%Y-%m-%d"),
            "observation_end": end_date.strftime("%Y-%m-%d"),
            "sort_order": "desc",
            "limit": limit,
        }
        
        data = self._make_request("series/observations", params)
        
        series_info = self.get_series_info(series_id) or {}
        
        for obs in data.get("observations", []):
            try:
                value = float(obs["value"]) if obs["value"] != "." else None
                if value is not None:
                    data_point = EconomicDataPoint(
                        series_id=series_id,
                        series_name=series_info.get("name", series_id),
                        date=datetime.strptime(obs["date"], "%Y-%m-%d"),
                        value=value,
                        unit=series_info.get("unit", ""),
                        source="FRED",
                        frequency=series_info.get("frequency", ""),
                        extra={
                            "category": series_info.get("category", ""),
                            "realtime_start": obs.get("realtime_start"),
                            "realtime_end": obs.get("realtime_end"),
                        }
                    )
                    observations.append(data_point)
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing observation: {e}")
                continue
        
        logger.info(f"Fetched {len(observations)} observations for {series_id}")
        return observations
    
    def fetch(
        self,
        series_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        observations_per_series: int = 50,
        **kwargs
    ) -> Generator[FetchedDocument, None, None]:
        """
        Fetch economic data from FRED.
        
        Args:
            series_ids: List of FRED series to fetch
            start_date: Start date for observations
            end_date: End date for observations
            observations_per_series: Number of observations per series
            
        Yields:
            FetchedDocument instances (one per series)
        """
        series_ids = series_ids or self.default_series
        
        for series_id in series_ids:
            logger.info(f"Fetching FRED series: {series_id}")
            
            observations = self.get_series_observations(
                series_id, start_date, end_date, observations_per_series
            )
            
            if observations:
                series_info = self.get_series_info(series_id) or {}
                
                # Create content from observations
                content_lines = [
                    f"FRED Economic Data Series: {series_id}",
                    f"Series Name: {series_info.get('name', series_id)}",
                    f"Description: {series_info.get('description', '')}",
                    f"Unit: {series_info.get('unit', '')}",
                    f"Frequency: {series_info.get('frequency', '')}",
                    "",
                    "Observations:",
                ]
                
                for obs in observations:
                    content_lines.append(
                        f"  {obs.date.strftime('%Y-%m-%d')}: {obs.value} {obs.unit}"
                    )
                
                content = "\n".join(content_lines)
                
                # Create metadata
                metadata = DocumentMetadata(
                    source_id=f"fred_{series_id}",
                    source_type=DataSourceType.FRED,
                    document_type="economic_data",
                    url=f"https://fred.stlouisfed.org/series/{series_id}",
                    extra={
                        "series_id": series_id,
                        "series_name": series_info.get("name"),
                        "category": series_info.get("category"),
                        "observations_count": len(observations),
                        "latest_value": observations[0].value if observations else None,
                        "latest_date": observations[0].date.isoformat() if observations else None,
                    }
                )
                
                doc = FetchedDocument(
                    metadata=metadata,
                    content=content,
                    sections={
                        "observations": [obs.to_dict() for obs in observations]
                    }
                )
                
                yield doc
    
    def validate(self, document: FetchedDocument) -> bool:
        """Validate a fetched document"""
        if not document.content:
            return False
        if document.metadata.extra.get("observations_count", 0) == 0:
            return False
        return True
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about this data source"""
        return {
            "name": "Federal Reserve Economic Data (FRED)",
            "type": DataSourceType.FRED.value,
            "base_url": self.base_url,
            "available_series": list(FRED_SERIES.keys()),
            "has_api_key": bool(self.api_key),
        }
    
    def get_latest_indicators(self) -> Dict[str, EconomicDataPoint]:
        """
        Get the latest value for key economic indicators.
        
        Returns:
            Dictionary of series_id to latest EconomicDataPoint
        """
        indicators = {}
        
        for series_id in self.default_series:
            observations = self.get_series_observations(series_id, limit=1)
            if observations:
                indicators[series_id] = observations[0]
        
        return indicators


# =============================================================================
# ECONOMIC ANALYSIS UTILITIES
# =============================================================================

def calculate_yoy_change(
    data_points: List[EconomicDataPoint]
) -> Optional[float]:
    """
    Calculate year-over-year change for a series.
    
    Args:
        data_points: List of observations (sorted by date desc)
        
    Returns:
        YoY percentage change or None
    """
    if len(data_points) < 2:
        return None
    
    # Find current and year-ago values
    current = data_points[0]
    target_date = current.date - timedelta(days=365)
    
    # Find closest observation to year-ago date
    for dp in data_points:
        if abs((dp.date - target_date).days) < 45:  # Within 45 days
            if dp.value != 0:
                return ((current.value - dp.value) / dp.value) * 100
    
    return None


def detect_trend(
    data_points: List[EconomicDataPoint],
    window: int = 3
) -> str:
    """
    Detect trend direction from recent observations.
    
    Args:
        data_points: List of observations (sorted by date desc)
        window: Number of observations to consider
        
    Returns:
        "increasing", "decreasing", or "stable"
    """
    if len(data_points) < window:
        return "insufficient_data"
    
    recent = data_points[:window]
    values = [dp.value for dp in recent]
    
    # Simple trend detection
    increases = sum(1 for i in range(len(values)-1) if values[i] > values[i+1])
    decreases = sum(1 for i in range(len(values)-1) if values[i] < values[i+1])
    
    if increases > decreases:
        return "increasing"
    elif decreases > increases:
        return "decreasing"
    else:
        return "stable"


def get_economic_context(indicators: Dict[str, EconomicDataPoint]) -> Dict[str, Any]:
    """
    Generate economic context from indicators.
    
    Args:
        indicators: Dictionary of series_id to latest EconomicDataPoint
        
    Returns:
        Dictionary with economic context analysis
    """
    context = {
        "timestamp": datetime.now().isoformat(),
        "indicators": {},
        "summary": [],
    }
    
    for series_id, dp in indicators.items():
        series_info = FRED_SERIES.get(series_id, {})
        context["indicators"][series_id] = {
            "name": dp.series_name,
            "value": dp.value,
            "unit": dp.unit,
            "date": dp.date.isoformat(),
            "category": series_info.get("category", ""),
        }
        
        # Add summary observations
        if series_id == "FEDFUNDS":
            if dp.value > 5:
                context["summary"].append("High interest rate environment (Fed Funds > 5%)")
            elif dp.value < 1:
                context["summary"].append("Low interest rate environment (Fed Funds < 1%)")
        
        if series_id == "UNRATE":
            if dp.value < 4:
                context["summary"].append("Strong labor market (Unemployment < 4%)")
            elif dp.value > 6:
                context["summary"].append("Elevated unemployment (> 6%)")
    
    return context
