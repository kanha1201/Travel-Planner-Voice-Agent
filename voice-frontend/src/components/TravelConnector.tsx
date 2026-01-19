import { Car } from 'lucide-react';

interface TravelConnectorProps {
  time?: string;
  minutes?: number;
}

export function TravelConnector({ time, minutes }: TravelConnectorProps) {
  // Prefer time string, fallback to minutes
  const displayTime = time || (minutes ? `${minutes} min` : '15 min');

  return (
    <div className="flex items-center justify-center my-2 relative">
      {/* Dotted line */}
      <div className="absolute left-[35px] top-0 bottom-0 w-px border-l-2 border-dotted border-gray-300" />
      
      {/* Travel time badge */}
      <div className="relative z-10 bg-gray-100 rounded-full px-3 py-1.5 flex items-center gap-1.5 text-xs text-gray-600">
        <Car size={14} />
        <span>{displayTime}</span>
      </div>
    </div>
  );
}

