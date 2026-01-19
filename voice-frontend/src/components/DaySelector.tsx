interface DaySelectorProps {
  selectedDay: number;
  onSelectDay: (day: number) => void;
  availableDays?: number[];
}

export function DaySelector({ selectedDay, onSelectDay, availableDays }: DaySelectorProps) {
  const days = availableDays || [1, 2, 3];

  return (
    <div className="sticky top-[57px] z-30 bg-white border-b border-gray-100 px-4 py-3">
      <div className="flex gap-2">
        {days.map((day) => (
          <button
            key={day}
            onClick={() => onSelectDay(day)}
            className={`flex-1 py-2 px-4 rounded-full text-sm transition-all ${
              selectedDay === day
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Day {day}
          </button>
        ))}
      </div>
    </div>
  );
}







