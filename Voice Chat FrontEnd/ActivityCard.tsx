import { Pencil } from 'lucide-react';

interface ActivityCardProps {
  title: string;
  duration: string;
  image: string;
}

export function ActivityCard({ title, duration, image }: ActivityCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-3 flex items-center gap-3 mb-4 hover:shadow-md transition-shadow">
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="text-gray-900 truncate">{title}</h3>
        <p className="text-sm text-gray-500">{duration}</p>
      </div>
    </div>
  );
}