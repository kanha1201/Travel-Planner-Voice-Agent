"""
POI Search Tool - Searches for Points of Interest in Jaipur using OpenStreetMap
"""

import requests
from typing import List, Dict, Optional
import json
import logging
import time
from math import radians, cos, sin, asin, sqrt
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class POISearch:
    """
    Search for Points of Interest in Jaipur using OpenStreetMap
    """
    
    def __init__(self):
        # Jaipur coordinates (center)
        self.jaipur_lat = 26.9124
        self.jaipur_lon = 75.7873
        self.radius_meters = 20000  # 20km radius
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", 3))
        self.max_retry_timeout = int(os.getenv("MAX_RETRY_TIMEOUT_SECONDS", 45))
    
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth radius in km
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def query_overpass_with_retry(self, query: str) -> List[Dict]:
        """Query Overpass API with exponential backoff retry"""
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.max_retry_attempts):
            try:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.max_retry_timeout:
                    logger.warning(f"Retry timeout reached ({self.max_retry_timeout}s)")
                    break
                
                # Overpass API expects query in request body with proper content type
                response = requests.post(
                    self.overpass_url,
                    data=query,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Check for Overpass API errors in response
                if "remark" in result and "error" in result.get("remark", "").lower():
                    raise Exception(f"Overpass API error: {result.get('remark')}")
                
                return result
                
            except requests.exceptions.HTTPError as e:
                # Try to get error details
                try:
                    error_detail = e.response.text[:200] if hasattr(e, 'response') else str(e)
                    logger.warning(f"HTTP Error details: {error_detail}")
                except:
                    pass
                last_exception = e
                wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                logger.warning(f"Overpass API attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                if attempt < self.max_retry_attempts - 1:
                    time.sleep(wait_time)
            except Exception as e:
                last_exception = e
                wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                logger.warning(f"Overpass API attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                if attempt < self.max_retry_attempts - 1:
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"All {self.max_retry_attempts} attempts failed. Last error: {last_exception}")
        return {"elements": []}
    
    def search_pois(self, interests: List[str], constraints: Optional[Dict] = None,
                   max_results: int = 30) -> Dict:
        """
        Search for POIs based on interests
        
        Args:
            interests: List of interests (e.g., ['culture', 'food', 'history'])
            constraints: Optional constraints (budget, pace, etc.)
            max_results: Maximum number of results
        
        Returns:
            Dict with 'pois' list and metadata
        """
        # Map interests to OSM tag combinations
        # Simplified approach: use specific tag combinations that work well
        interest_queries = {
            "culture": [
                ('node["tourism"="attraction"](around:{radius},{lat},{lon});'),
                ('node["tourism"="museum"](around:{radius},{lat},{lon});'),
                ('node["historic"](around:{radius},{lat},{lon});')
            ],
            "food": [
                ('node["amenity"="restaurant"](around:{radius},{lat},{lon});'),
                ('node["amenity"="cafe"](around:{radius},{lat},{lon});')
            ],
            "history": [
                ('node["historic"](around:{radius},{lat},{lon});'),
                ('node["tourism"="museum"](around:{radius},{lat},{lon});')
            ],
            "shopping": [
                ('node["shop"](around:{radius},{lat},{lon});')
            ],
            "nature": [
                ('node["leisure"="park"](around:{radius},{lat},{lon});')
            ],
            "religion": [
                ('node["amenity"="place_of_worship"](around:{radius},{lat},{lon});')
            ],
            "entertainment": [
                ('node["amenity"="cinema"](around:{radius},{lat},{lon});'),
                ('node["leisure"](around:{radius},{lat},{lon});')
            ]
        }
        
        # Build query parts based on interests
        query_parts = []
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in interest_queries:
                for query_template in interest_queries[interest_lower][:2]:  # Limit to 2 per interest
                    query_parts.append(query_template.format(
                        radius=self.radius_meters,
                        lat=self.jaipur_lat,
                        lon=self.jaipur_lon
                    ))
        
        # Default query if no interests match
        if not query_parts:
            query_parts = [
                f'node["tourism"](around:{self.radius_meters},{self.jaipur_lat},{self.jaipur_lon});'
            ]
        
        # Limit total query parts to avoid timeout
        query_parts = query_parts[:10]
        
        # Build complete Overpass query
        overpass_query = f"""[out:json][timeout:25];
(
{''.join(query_parts)}
);
out body;"""
        
        # Log query for debugging
        logger.debug(f"Overpass query (first 300 chars): {overpass_query[:300]}")
        
        # Query Overpass with retry
        logger.info(f"Searching for POIs with interests: {interests}")
        data = self.query_overpass_with_retry(overpass_query)
        
        # Process results
        pois = []
        seen_names = set()
        
        for element in data.get("elements", []):
            if element.get("type") not in ["node", "way"]:
                continue
            
            tags = element.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or "Unnamed"
            
            # Skip duplicates
            if name in seen_names or name == "Unnamed":
                continue
            seen_names.add(name)
            
            # Get coordinates
            if element.get("type") == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            else:
                # For ways, use center (simplified)
                center = element.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")
            
            if not lat or not lon:
                continue
            
            # Calculate distance from center
            distance = self.haversine_distance(
                self.jaipur_lat, self.jaipur_lon, lat, lon
            )
            
            # Determine category
            category = "other"
            if "tourism" in tags:
                category = tags.get("tourism", "other")
            elif "amenity" in tags:
                category = tags.get("amenity", "other")
            elif "historic" in tags:
                category = "historic"
            elif "shop" in tags:
                category = "shopping"
            
            # Estimate visit duration (simplified)
            visit_duration = 60  # Default 1 hour
            if category in ["museum", "attraction"]:
                visit_duration = 120
            elif category == "restaurant":
                visit_duration = 60
            elif category == "cafe":
                visit_duration = 30
            
            # Build POI object
            poi = {
                "id": f"osm_{element.get('id')}",
                "name": name,
                "category": category,
                "location": {"lat": lat, "lon": lon},
                "distance_km": round(distance, 2),
                "visit_duration_minutes": visit_duration,
                "source": "openstreetmap",
                "source_url": f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}",
                "tags": tags,
                "relevance_score": 0.8  # Default, can be improved
            }
            
            # Add opening hours if available
            if "opening_hours" in tags:
                poi["opening_hours"] = tags["opening_hours"]
            
            # Add rating if available
            if "rating" in tags:
                try:
                    poi["rating"] = float(tags["rating"])
                except:
                    pass
            
            pois.append(poi)
        
        # Sort by distance and relevance
        pois.sort(key=lambda x: (x["distance_km"], -x["relevance_score"]))
        
        # Limit results
        pois = pois[:max_results]
        
        logger.info(f"Found {len(pois)} POIs")
        
        return {
            "pois": pois,
            "total_count": len(pois),
            "data_quality": "complete" if len(pois) > 0 else "limited"
        }


# Function handler for Groq
def search_pois_handler(interests: List[str], constraints: Optional[Dict] = None,
                       max_results: int = 30) -> Dict:
    """
    Handler function for Groq function calling
    
    Args:
        interests: List of interest strings
        constraints: Optional constraints dict
        max_results: Maximum number of results
    
    Returns:
        Dict with POIs
    """
    searcher = POISearch()
    return searcher.search_pois(interests, constraints, max_results)


if __name__ == "__main__":
    # Test POI search
    logging.basicConfig(level=logging.INFO)
    searcher = POISearch()
    results = searcher.search_pois(["culture", "food"], max_results=10)
    
    logger.info(f"Found {results['total_count']} POIs")
    for poi in results['pois'][:5]:
        logger.info(f"- {poi['name']} ({poi['category']}) - {poi['distance_km']}km")

