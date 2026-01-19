interface ActivityCardProps {
  name: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  duration?: string; // For display format like "2 hrs", "1 hr", "1.5 hrs"
  category?: string;
  location?: {
    lat?: number;
    lng?: number;
    address?: string;
  };
}

export function ActivityCard({ name, duration, duration_minutes, start_time, end_time }: ActivityCardProps) {
  // Format duration - prefer the display format if available, otherwise calculate from minutes
  const displayDuration = duration || (duration_minutes ? formatDurationFromMinutes(duration_minutes) : '');

  function formatDurationFromMinutes(minutes: number): string {
    const hours = minutes / 60;
    if (hours >= 1) {
      const wholeHours = Math.floor(hours);
      const remainingMinutes = minutes % 60;
      if (remainingMinutes === 0) {
        return `${wholeHours} ${wholeHours === 1 ? 'hr' : 'hrs'}`;
      } else if (remainingMinutes === 30) {
        return `${wholeHours}.5 hrs`;
      } else {
        return `${wholeHours} ${wholeHours === 1 ? 'hr' : 'hrs'} ${remainingMinutes}m`;
      }
    } else {
      return `${minutes} min`;
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-3 flex items-center gap-3 mb-4 hover:shadow-md transition-shadow">
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="text-gray-900 truncate">{name}</h3>
        {displayDuration && (
          <p className="text-sm text-gray-500">{displayDuration}</p>
        )}
      </div>
    </div>
  );
}

