"""
Itinerary Builder Tool - Builds structured day-wise itineraries from POIs
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class ItineraryBuilder:
    """
    Build structured day-wise itineraries from POIs
    """
    
    def __init__(self):
        # Default time windows
        self.default_start = "09:00"
        self.default_end = "20:00"
        self.lunch_time = "13:00"
        self.dinner_time = "19:00"
    
    def time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight"""
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    
    def minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to time string"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def calculate_travel_time(self, poi1: Dict, poi2: Dict) -> int:
        """
        Calculate travel time between two POIs (simplified)
        Uses distance-based estimation
        """
        # Get locations
        loc1 = poi1.get("location", {})
        loc2 = poi2.get("location", {})
        
        if not loc1 or not loc2:
            return 15  # Default 15 minutes
        
        # Calculate distance (simplified - assumes straight line)
        # In production, use routing API
        distance_km = abs(poi2.get("distance_km", 0) - poi1.get("distance_km", 0))
        
        # Estimate travel time (assuming 30 km/h average in city)
        travel_time_minutes = int((distance_km / 30) * 60)
        
        # Add buffer
        travel_time_minutes += 5
        
        # Cap at reasonable limits
        return min(max(travel_time_minutes, 5), 60)
    
    def build_itinerary(self, candidate_pois: List[Dict], duration_days: int,
                       pace: str = "moderate", date_range: Optional[Dict] = None,
                       daily_start_time: str = "09:00", daily_end_time: str = "20:00",
                       edit_mode: bool = False, edit_constraints: Optional[Dict] = None) -> Dict:
        """
        Build day-wise itinerary
        
        Args:
            candidate_pois: List of POI objects
            duration_days: Number of days (1-3)
            pace: "relaxed", "moderate", or "packed"
            date_range: Optional start/end dates
            daily_start_time: Daily start time
            daily_end_time: Daily end time
            edit_mode: Whether editing existing itinerary
            edit_constraints: Constraints for editing
        
        Returns:
            Structured itinerary dict
        """
        # Pace settings with distribution requirements
        # User requirements:
        # - Relaxed: 1 morning + 1 afternoon + 1 evening = 3 total
        # - Moderate: 1-2 morning + 1-2 afternoon + 1-2 evening = 3-6 total
        # - Packed: 1-2 morning + 1-2 afternoon + 2-3 evening = 4-7 total
        pace_settings = {
            "relaxed": {
                "max_activities_per_day": 3,  # Exactly 3: 1 morning + 1 afternoon + 1 evening
                "min_per_slot": 1,  # At least 1 per time slot
                "max_per_slot": 1,  # Maximum 1 per time slot
                "buffer_minutes": 30,
                "min_activity_duration": 90
            },
            "moderate": {
                "max_activities_per_day": 6,  # Up to 6: 1-2 morning + 1-2 afternoon + 1-2 evening
                "min_per_slot": 1,  # At least 1 per time slot
                "max_per_slot": 2,  # Maximum 2 per time slot
                "buffer_minutes": 15,
                "min_activity_duration": 60
            },
            "packed": {
                "max_activities_per_day": 7,  # Up to 7: 1-2 morning + 1-2 afternoon + 2-3 evening
                "min_per_slot": 1,  # At least 1 per time slot (morning/afternoon), 2 for evening
                "max_per_slot": {"morning": 2, "afternoon": 2, "evening": 3},  # Evening can have more
                "buffer_minutes": 10,
                "min_activity_duration": 45
            }
        }
        
        settings = pace_settings.get(pace, pace_settings["moderate"])
        
        # Ensure duration_days is an integer (defensive check)
        if not isinstance(duration_days, int):
            try:
                duration_days = int(float(duration_days))
            except (ValueError, TypeError):
                logger.error(f"Invalid duration_days: {duration_days}, defaulting to 2")
                duration_days = 2
        
        # Validate duration_days range
        if duration_days < 1:
            duration_days = 1
        elif duration_days > 3:
            duration_days = 3
        
        # Calculate time windows
        start_minutes = self.time_to_minutes(daily_start_time)
        end_minutes = self.time_to_minutes(daily_end_time)
        available_minutes = end_minutes - start_minutes
        
        # Split day into blocks
        # Morning: 09:00 - 13:00 (4 hours)
        # Afternoon: 13:00 - 18:00 (5 hours)  
        # Evening: 18:00 - 20:00 or later (2+ hours)
        morning_end = self.time_to_minutes("13:00")
        afternoon_end = self.time_to_minutes("18:00")
        # Ensure evening has enough time - extend if needed
        if end_minutes < self.time_to_minutes("20:00"):
            logger.warning(f"Evening time window is short ({self.minutes_to_time(end_minutes)}). Consider extending daily_end_time for better evening activity scheduling.")
        
        itinerary = {}
        
        logger.info(f"Building itinerary: {len(candidate_pois)} POIs, {duration_days} days, pace={pace}")
        logger.info(f"Pace settings: max_activities_per_day={settings['max_activities_per_day']}, buffer={settings['buffer_minutes']}min")
        
        for day in range(1, duration_days + 1):
            day_key = f"day_{day}"
            
            # Select POIs for this day (distribute evenly, but ensure we use enough)
            # We need enough POIs to fill morning, afternoon, AND evening slots
            # For relaxed pace (4 max), we want at least 5-6 POIs per day to choose from
            # For moderate (5 max), we want 6-7 POIs per day
            # For packed (7 max), we want 8-9 POIs per day
            min_pois_per_day = settings["max_activities_per_day"] + 2  # Give buffer for selection across all time slots
            total_needed = min_pois_per_day * duration_days
            
            # If we have enough POIs, distribute them
            if len(candidate_pois) >= total_needed:
                pois_per_day = len(candidate_pois) // duration_days
                start_idx = (day - 1) * pois_per_day
                end_idx = start_idx + pois_per_day if day < duration_days else len(candidate_pois)
                day_pois = candidate_pois[start_idx:end_idx]
            else:
                # If we don't have enough, try to distribute what we have more intelligently
                # For 2-day trip with relaxed pace, we need at least 6 POIs (3 per day)
                # But if we only have 2-3 POIs, distribute them and use all
                pois_per_day = max(1, len(candidate_pois) // duration_days)
                start_idx = (day - 1) * pois_per_day
                end_idx = start_idx + pois_per_day if day < duration_days else len(candidate_pois)
                day_pois = candidate_pois[start_idx:end_idx]
                logger.warning(f"Day {day}: Only {len(day_pois)} POI(s) available (need {min_pois_per_day} for optimal scheduling)")
            
            # Don't limit POIs upfront - we'll schedule intelligently across time slots
            # We need enough POIs to fill all time slots based on pace requirements
            logger.info(f"Day {day}: Available {len(day_pois)} POI(s) for scheduling: {[p.get('name', 'Unknown') for p in day_pois]}")
            
            # Build schedule with intelligent distribution across time slots
            morning_activities = []
            afternoon_activities = []
            evening_activities = []
            
            # Track time for each slot separately
            morning_time = start_minutes
            afternoon_time = morning_end  # Start afternoon at 13:00
            evening_time = afternoon_end  # Start evening at 18:00
            
            # Get max per slot based on pace
            if pace == "packed":
                max_morning = settings["max_per_slot"]["morning"]
                max_afternoon = settings["max_per_slot"]["afternoon"]
                max_evening = settings["max_per_slot"]["evening"]
            else:
                max_morning = settings["max_per_slot"]
                max_afternoon = settings["max_per_slot"]
                max_evening = settings["max_per_slot"] if pace == "relaxed" else settings["max_per_slot"]
            
            min_per_slot = settings.get("min_per_slot", 1)
            
            scheduled_count = 0
            poi_index = 0
            
            # First pass: Ensure minimum activities per slot (for relaxed/moderate)
            # For relaxed: schedule exactly 1 per slot
            # For moderate: schedule at least 1 per slot, up to 2
            # For packed: schedule at least 1 per slot (morning/afternoon), 2 for evening
            
            # Schedule morning activities (at least min_per_slot)
            morning_scheduled = 0
            while morning_scheduled < min_per_slot and poi_index < len(day_pois) and scheduled_count < settings["max_activities_per_day"]:
                poi = day_pois[poi_index]
                duration = poi.get("visit_duration_minutes", 60)
                
                # Calculate travel time
                travel_time = 0
                if morning_scheduled > 0:
                    prev_poi = morning_activities[-1]
                    travel_time = self.calculate_travel_time(
                        {"location": prev_poi.get("location", {})},
                        poi
                    )
                
                if morning_time + travel_time + duration <= morning_end:
                    start_time = self.minutes_to_time(morning_time + travel_time)
                    end_time = self.minutes_to_time(morning_time + travel_time + duration)
                    
                    morning_activities.append({
                        "activity_id": poi["id"],
                        "name": poi["name"],
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_minutes": duration,
                        "travel_from_previous": travel_time,
                        "category": poi.get("category", "other"),
                        "location": poi.get("location", {})
                    })
                    
                    morning_time += travel_time + duration + settings["buffer_minutes"]
                    morning_scheduled += 1
                    scheduled_count += 1
                    poi_index += 1
                    logger.debug(f"Day {day}: Scheduled {poi.get('name')} in morning ({start_time}-{end_time})")
                else:
                    # Doesn't fit in morning, skip to next POI
                    poi_index += 1
            
            # Schedule afternoon activities (at least min_per_slot)
            afternoon_scheduled = 0
            while afternoon_scheduled < min_per_slot and poi_index < len(day_pois) and scheduled_count < settings["max_activities_per_day"]:
                poi = day_pois[poi_index]
                duration = poi.get("visit_duration_minutes", 60)
                
                # Calculate travel time from last morning activity or previous afternoon
                travel_time = 0
                if afternoon_scheduled > 0:
                    # Travel from previous afternoon activity
                    prev_act = afternoon_activities[-1]
                    prev_poi_dict = {"location": prev_act.get("location", {})}
                    travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    # Use the current afternoon time
                    current_slot_time = afternoon_time
                elif morning_activities:
                    # Travel from last morning activity to afternoon
                    prev_act = morning_activities[-1]
                    prev_poi_dict = {"location": prev_act.get("location", {})}
                    travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    # Start afternoon right after morning ends (account for travel)
                    current_slot_time = morning_end + travel_time
                else:
                    # No previous activities, start at afternoon start time
                    current_slot_time = morning_end
                
                if current_slot_time + duration <= afternoon_end:
                    start_time = self.minutes_to_time(current_slot_time)
                    end_time = self.minutes_to_time(current_slot_time + duration)
                    
                    afternoon_activities.append({
                        "activity_id": poi["id"],
                        "name": poi["name"],
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_minutes": duration,
                        "travel_from_previous": travel_time,
                        "category": poi.get("category", "other"),
                        "location": poi.get("location", {})
                    })
                    
                    afternoon_time = current_slot_time + duration + settings["buffer_minutes"]
                    afternoon_scheduled += 1
                    scheduled_count += 1
                    poi_index += 1
                    logger.debug(f"Day {day}: Scheduled {poi.get('name')} in afternoon ({start_time}-{end_time})")
                else:
                    poi_index += 1
            
            # Schedule evening activities (at least min_per_slot, or 2 for packed)
            evening_min = 2 if pace == "packed" else min_per_slot
            evening_scheduled = 0
            while evening_scheduled < evening_min and poi_index < len(day_pois) and scheduled_count < settings["max_activities_per_day"]:
                poi = day_pois[poi_index]
                duration = poi.get("visit_duration_minutes", 60)
                
                # Calculate travel time from last afternoon or previous evening
                travel_time = 0
                if evening_scheduled > 0:
                    # Travel from previous evening activity
                    prev_act = evening_activities[-1]
                    prev_poi_dict = {"location": prev_act.get("location", {})}
                    travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    current_slot_time = evening_time
                elif afternoon_activities:
                    # Travel from last afternoon activity to evening
                    prev_act = afternoon_activities[-1]
                    prev_poi_dict = {"location": prev_act.get("location", {})}
                    travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    # Start evening right after afternoon ends (account for travel)
                    current_slot_time = afternoon_end + travel_time
                elif morning_activities:
                    # Travel from last morning activity to evening (skip afternoon)
                    prev_act = morning_activities[-1]
                    prev_poi_dict = {"location": prev_act.get("location", {})}
                    travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    current_slot_time = afternoon_end + travel_time
                else:
                    # No previous activities, start at evening start time
                    current_slot_time = afternoon_end
                
                if current_slot_time + duration <= end_minutes:
                    start_time = self.minutes_to_time(current_slot_time)
                    end_time = self.minutes_to_time(current_slot_time + duration)
                    
                    evening_activities.append({
                        "activity_id": poi["id"],
                        "name": poi["name"],
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_minutes": duration,
                        "travel_from_previous": travel_time,
                        "category": poi.get("category", "other"),
                        "location": poi.get("location", {})
                    })
                    
                    evening_time = current_slot_time + duration + settings["buffer_minutes"]
                    evening_scheduled += 1
                    scheduled_count += 1
                    poi_index += 1
                    logger.debug(f"Day {day}: Scheduled {poi.get('name')} in evening ({start_time}-{end_time})")
                else:
                    poi_index += 1
            
            # Second pass: Fill remaining slots up to max_per_slot (for moderate/packed)
            # Distribute remaining POIs across slots that haven't reached max
            while poi_index < len(day_pois) and scheduled_count < settings["max_activities_per_day"]:
                poi = day_pois[poi_index]
                duration = poi.get("visit_duration_minutes", 60)
                scheduled = False
                
                # Try to schedule in a slot that hasn't reached max
                # Priority: morning < afternoon < evening (to fill evenly)
                
                # Try morning if not at max
                if not scheduled and len(morning_activities) < max_morning:
                    prev_act = morning_activities[-1] if morning_activities else None
                    travel_time = 0
                    if prev_act:
                        prev_poi_dict = {"location": prev_act.get("location", {})}
                        travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    
                    current_slot_time = morning_time
                    if current_slot_time + travel_time + duration <= morning_end:
                        start_time = self.minutes_to_time(current_slot_time + travel_time)
                        end_time = self.minutes_to_time(current_slot_time + travel_time + duration)
                        
                        morning_activities.append({
                            "activity_id": poi["id"],
                            "name": poi["name"],
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_minutes": duration,
                            "travel_from_previous": travel_time,
                            "category": poi.get("category", "other"),
                            "location": poi.get("location", {})
                        })
                        
                        morning_time = current_slot_time + travel_time + duration + settings["buffer_minutes"]
                        scheduled_count += 1
                        scheduled = True
                        logger.debug(f"Day {day}: Scheduled {poi.get('name')} in morning (fill pass)")
                
                # Try afternoon if not at max and morning didn't work
                if not scheduled and len(afternoon_activities) < max_afternoon:
                    prev_act = afternoon_activities[-1] if afternoon_activities else (morning_activities[-1] if morning_activities else None)
                    travel_time = 0
                    if prev_act:
                        prev_poi_dict = {"location": prev_act.get("location", {})}
                        travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    
                    if afternoon_activities:
                        current_slot_time = afternoon_time
                    elif morning_activities:
                        current_slot_time = morning_end + travel_time
                    else:
                        current_slot_time = morning_end
                    
                    if current_slot_time + duration <= afternoon_end:
                        start_time = self.minutes_to_time(current_slot_time)
                        end_time = self.minutes_to_time(current_slot_time + duration)
                        
                        afternoon_activities.append({
                            "activity_id": poi["id"],
                            "name": poi["name"],
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_minutes": duration,
                            "travel_from_previous": travel_time,
                            "category": poi.get("category", "other"),
                            "location": poi.get("location", {})
                        })
                        
                        afternoon_time = current_slot_time + duration + settings["buffer_minutes"]
                        scheduled_count += 1
                        scheduled = True
                        logger.debug(f"Day {day}: Scheduled {poi.get('name')} in afternoon (fill pass)")
                
                # Try evening if not at max and others didn't work
                if not scheduled and len(evening_activities) < max_evening:
                    prev_act = evening_activities[-1] if evening_activities else (afternoon_activities[-1] if afternoon_activities else (morning_activities[-1] if morning_activities else None))
                    travel_time = 0
                    if prev_act:
                        prev_poi_dict = {"location": prev_act.get("location", {})}
                        travel_time = self.calculate_travel_time(prev_poi_dict, poi)
                    
                    if evening_activities:
                        current_slot_time = evening_time
                    elif afternoon_activities:
                        current_slot_time = afternoon_end + travel_time
                    elif morning_activities:
                        current_slot_time = afternoon_end + travel_time
                    else:
                        current_slot_time = afternoon_end
                    
                    if current_slot_time + duration <= end_minutes:
                        start_time = self.minutes_to_time(current_slot_time)
                        end_time = self.minutes_to_time(current_slot_time + duration)
                        
                        evening_activities.append({
                            "activity_id": poi["id"],
                            "name": poi["name"],
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_minutes": duration,
                            "travel_from_previous": travel_time,
                            "category": poi.get("category", "other"),
                            "location": poi.get("location", {})
                        })
                        
                        evening_time = current_slot_time + duration + settings["buffer_minutes"]
                        scheduled_count += 1
                        scheduled = True
                        logger.debug(f"Day {day}: Scheduled {poi.get('name')} in evening (fill pass)")
                
                if not scheduled:
                    # Couldn't fit this POI, skip it
                    logger.debug(f"Day {day}: Could not fit {poi.get('name')} in any available slot")
                
                poi_index += 1
            
            logger.info(f"Day {day}: Scheduled {scheduled_count} activities (morning: {len(morning_activities)}, afternoon: {len(afternoon_activities)}, evening: {len(evening_activities)})")
            
            # Validate distribution meets pace requirements
            if len(morning_activities) < min_per_slot:
                logger.warning(f"Day {day}: Only {len(morning_activities)} morning activity(ies) scheduled, need at least {min_per_slot} for {pace} pace")
            if len(afternoon_activities) < min_per_slot:
                logger.warning(f"Day {day}: Only {len(afternoon_activities)} afternoon activity(ies) scheduled, need at least {min_per_slot} for {pace} pace")
            evening_min_required = 2 if pace == "packed" else min_per_slot
            if len(evening_activities) < evening_min_required:
                logger.warning(f"Day {day}: Only {len(evening_activities)} evening activity(ies) scheduled, need at least {evening_min_required} for {pace} pace")
            
            # Warn if we didn't use all available POIs
            if poi_index < len(day_pois):
                logger.info(f"Day {day}: {len(day_pois) - poi_index} POI(s) not scheduled (reached max activities or couldn't fit)")
            
            itinerary[day_key] = {
                "date": date_range.get("start_date") if date_range else None,
                "morning": morning_activities,
                "afternoon": afternoon_activities,
                "evening": evening_activities
            }
        
        # Calculate total travel time
        total_travel = sum(
            sum(act.get("travel_from_previous", 0) for act in day.get("morning", [])) +
            sum(act.get("travel_from_previous", 0) for act in day.get("afternoon", [])) +
            sum(act.get("travel_from_previous", 0) for act in day.get("evening", []))
            for day in itinerary.values()
        )
        
        return {
            "itinerary": itinerary,
            "total_travel_time_minutes": total_travel,
            "feasibility_score": 0.85,  # Simplified
            "warnings": []
        }


# Function handler for Groq
def build_itinerary_handler(candidate_pois: List[Dict], duration_days: int,
                           pace: str = "moderate", **kwargs) -> Dict:
    """
    Handler function for Groq function calling
    
    Args:
        candidate_pois: List of POI objects
        duration_days: Number of days (1-3)
        pace: Travel pace
        **kwargs: Additional parameters (date_range, daily_start_time, etc.)
    
    Returns:
        Structured itinerary dict
    """
    # Validate candidate_pois - check if it's actually a list of dictionaries
    # Sometimes LLMs pass placeholder strings like ["result1", "result2"] 
    # or try to pass search_pois results incorrectly
    if not isinstance(candidate_pois, list):
        return {
            "error": "candidate_pois must be a list",
            "itinerary": {},
            "total_travel_time_minutes": 0,
            "feasibility_score": 0.0,
            "warnings": ["Invalid candidate_pois format: not a list"]
        }
    
    # Filter out invalid entries (strings, None, etc.) and keep only dictionaries
    valid_pois = []
    for poi in candidate_pois:
        if isinstance(poi, dict):
            # Check if it has required fields (at minimum, should have 'id' or 'name')
            if poi.get("id") or poi.get("name"):
                valid_pois.append(poi)
        elif isinstance(poi, str):
            # Skip placeholder strings like "result1", "result2", etc.
            logger.warning(f"Skipping invalid POI entry (string): {poi}")
            continue
    
    if not valid_pois:
        return {
            "error": "No valid POIs provided. candidate_pois must contain POI dictionaries with 'id' or 'name' fields.",
            "itinerary": {},
            "total_travel_time_minutes": 0,
            "feasibility_score": 0.0,
            "warnings": [
                "No valid POIs found in candidate_pois",
                "Please call search_pois first to get actual POI data",
                f"Received {len(candidate_pois)} entries, but none were valid POI dictionaries"
            ]
        }
    
    # Log if we filtered out invalid entries
    if len(valid_pois) < len(candidate_pois):
        logger.warning(f"Filtered out {len(candidate_pois) - len(valid_pois)} invalid POI entries. Using {len(valid_pois)} valid POIs.")
    
    # Ensure duration_days is an integer (Gemini may pass float)
    if isinstance(duration_days, float):
        duration_days = int(duration_days)
    elif not isinstance(duration_days, int):
        try:
            duration_days = int(float(duration_days))
        except (ValueError, TypeError):
            logger.error(f"Invalid duration_days type: {type(duration_days)}, value: {duration_days}")
            duration_days = 2  # Default fallback
    
    # Validate duration_days range
    if duration_days < 1:
        duration_days = 1
    elif duration_days > 3:
        duration_days = 3
    
    builder = ItineraryBuilder()
    return builder.build_itinerary(valid_pois, duration_days, pace, **kwargs)


if __name__ == "__main__":
    # Test itinerary builder
    logging.basicConfig(level=logging.INFO)
    test_pois = [
        {"id": "1", "name": "City Palace", "location": {"lat": 26.9, "lon": 75.8},
         "visit_duration_minutes": 120, "distance_km": 0.5, "category": "tourism"},
        {"id": "2", "name": "Jantar Mantar", "location": {"lat": 26.9, "lon": 75.8},
         "visit_duration_minutes": 90, "distance_km": 0.6, "category": "tourism"},
    ]
    
    builder = ItineraryBuilder()
    result = builder.build_itinerary(test_pois, duration_days=2, pace="relaxed")
    
    logger.info(json.dumps(result, indent=2))



