import { useState } from 'react';
import { Clock, MapPin, ArrowDown } from 'lucide-react';
import { Itinerary, Activity } from '../types';

interface ItineraryDisplayProps {
  itinerary: Itinerary | null;
}

export default function ItineraryDisplay({ itinerary }: ItineraryDisplayProps) {
  const [selectedDay, setSelectedDay] = useState<'day_1' | 'day_2' | 'day_3'>('day_1');

  if (!itinerary) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium">No Itinerary Yet</p>
          <p className="text-sm mt-2">Start a conversation to generate your travel plan</p>
        </div>
      </div>
    );
  }

  const days = [
    { key: 'day_1' as const, label: 'Day 1' },
    { key: 'day_2' as const, label: 'Day 2' },
    { key: 'day_3' as const, label: 'Day 3' },
  ].filter(day => itinerary[day.key]);

  const currentDay = itinerary[selectedDay];
  
  // Ensure all time slots exist (even if empty arrays)
  // This is important for displaying edits correctly
  if (currentDay) {
    currentDay.morning = Array.isArray(currentDay.morning) ? currentDay.morning : [];
    currentDay.afternoon = Array.isArray(currentDay.afternoon) ? currentDay.afternoon : [];
    currentDay.evening = Array.isArray(currentDay.evening) ? currentDay.evening : [];
    
    // Debug log for Day 2 morning (common edit target)
    if (selectedDay === 'day_2') {
      console.log('🔍 Day 2 itinerary:', {
        morning: currentDay.morning.length,
        afternoon: currentDay.afternoon.length,
        evening: currentDay.evening.length
      });
    }
  }

  const renderActivityCard = (activity: Activity, index: number, timeSlot: 'morning' | 'afternoon' | 'evening') => {
    const timeSlotIndex = timeSlot === 'morning' ? 0 : timeSlot === 'afternoon' ? 1 : 2;
    const isFirstInSlot = index === 0;
    const showTravelTime = !isFirstInSlot || (timeSlot === 'afternoon' && itinerary[selectedDay]?.morning.length > 0) || (timeSlot === 'evening' && (itinerary[selectedDay]?.afternoon.length > 0 || itinerary[selectedDay]?.morning.length > 0));

    return (
      <div key={activity.activity_id || index} className="relative">
        {showTravelTime && activity.travel_from_previous !== undefined && activity.travel_from_previous > 0 && (
          <div className="flex items-center justify-center my-2 text-gray-500 text-sm">
            <ArrowDown className="w-4 h-4 mr-1" />
            <span>{activity.travel_from_previous} min travel</span>
          </div>
        )}
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{activity.name}</h3>
            {activity.type && (
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                {activity.type}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
            {activity.start_time && activity.end_time && (
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{activity.start_time} - {activity.end_time}</span>
              </div>
            )}
            {activity.duration_minutes && (
              <span className="text-gray-500">
                ({Math.floor(activity.duration_minutes / 60)}h {activity.duration_minutes % 60}m)
              </span>
            )}
          </div>
          
          {activity.description && (
            <p className="text-sm text-gray-700 line-clamp-2 mt-2">
              {activity.description}
            </p>
          )}
          
          {activity.location && (
            <div className="flex items-center space-x-1 text-xs text-gray-500 mt-2">
              <MapPin className="w-3 h-3" />
              <span>{activity.location.lat.toFixed(4)}, {activity.location.lon.toFixed(4)}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderTimeSlot = (slot: 'morning' | 'afternoon' | 'evening', activities: Activity[]) => {
    if (activities.length === 0) return null;

    const slotLabels = {
      morning: 'Morning',
      afternoon: 'Afternoon',
      evening: 'Evening',
    };

    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
          <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
          {slotLabels[slot]}
        </h3>
        <div className="space-y-4">
          {activities.map((activity, index) => renderActivityCard(activity, index, slot))}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Day Selector */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex space-x-2">
          {days.map((day) => (
            <button
              key={day.key}
              onClick={() => setSelectedDay(day.key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedDay === day.key
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {day.label}
              {itinerary[day.key]?.date && (
                <span className="text-xs ml-1 opacity-75">
                  ({new Date(itinerary[day.key]!.date!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline View */}
      <div className="flex-1 overflow-y-auto p-6">
        {currentDay ? (
          <div className="max-w-2xl mx-auto">
            {renderTimeSlot('morning', currentDay.morning)}
            {renderTimeSlot('afternoon', currentDay.afternoon)}
            {renderTimeSlot('evening', currentDay.evening)}
            
            {currentDay.morning.length === 0 && 
             currentDay.afternoon.length === 0 && 
             currentDay.evening.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <p>No activities planned for this day</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            <p>No itinerary available for this day</p>
          </div>
        )}
      </div>
    </div>
  );
}



