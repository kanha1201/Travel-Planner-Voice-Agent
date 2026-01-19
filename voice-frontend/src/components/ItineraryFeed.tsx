import { ActivityCard } from './ActivityCard';
import { TravelConnector } from './TravelConnector';
import { DayItinerary } from '../types';

interface ItineraryFeedProps {
  selectedDay: number;
  itinerary?: DayItinerary;
}

function formatDuration(minutes: number): string {
  const hours = minutes / 60;
  if (hours >= 1) {
    const wholeHours = Math.floor(hours);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) {
      return `${wholeHours} ${wholeHours === 1 ? 'hr' : 'hrs'}`;
    } else if (remainingMinutes === 30) {
      return `${wholeHours}.5 hrs`;
    } else {
      return `${wholeHours} ${wholeHours === 1 ? 'hr' : 'hrs'}`;
    }
  } else {
    return `${minutes} min`;
  }
}

export function ItineraryFeed({ selectedDay, itinerary }: ItineraryFeedProps) {
  if (!itinerary) {
    return (
      <div className="flex-1 overflow-y-auto pb-32 px-4 flex items-center justify-center">
        <div className="text-center max-w-xs">
          <p className="text-gray-500 text-sm">No itinerary available yet.</p>
          <p className="text-gray-400 text-xs mt-2">Start a voice conversation to create your travel plan!</p>
        </div>
      </div>
    );
  }

  const morning = itinerary.morning || [];
  const afternoon = itinerary.afternoon || [];
  const evening = itinerary.evening || [];

  return (
    <div className="flex-1 overflow-y-auto pb-32 px-4">
      {/* Morning */}
      {morning.length > 0 && (
        <section className="mt-6">
          <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">MORNING</h2>
          <div className="space-y-0">
            {morning.map((activity, idx) => (
              <div key={activity.id || idx}>
                <ActivityCard 
                  name={activity.name}
                  duration={formatDuration(activity.duration_minutes)}
                />
                {idx < morning.length - 1 && (
                  <TravelConnector time="10 min" />
                )}
              </div>
            ))}
          </div>
          {afternoon.length > 0 && <TravelConnector time="15 min" />}
        </section>
      )}

      {/* Afternoon */}
      {afternoon.length > 0 && (
        <section className="mt-0">
          <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">AFTERNOON</h2>
          <div className="space-y-0">
            {afternoon.map((activity, idx) => (
              <div key={activity.id || idx}>
                <ActivityCard 
                  name={activity.name}
                  duration={formatDuration(activity.duration_minutes)}
                />
                {idx < afternoon.length - 1 && (
                  <TravelConnector time="12 min" />
                )}
              </div>
            ))}
          </div>
          {evening.length > 0 && <TravelConnector time="20 min" />}
        </section>
      )}

      {/* Evening */}
      {evening.length > 0 && (
        <section className="mt-0">
          <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">EVENING</h2>
          <div className="space-y-0">
            {evening.map((activity, idx) => (
              <div key={activity.id || idx}>
                <ActivityCard 
                  name={activity.name}
                  duration={formatDuration(activity.duration_minutes)}
                />
                {idx < evening.length - 1 && (
                  <TravelConnector minutes={15} />
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {morning.length === 0 && afternoon.length === 0 && evening.length === 0 && (
        <div className="mt-6 text-center text-gray-500 text-sm">
          No activities scheduled for this day.
        </div>
      )}
    </div>
  );
}

