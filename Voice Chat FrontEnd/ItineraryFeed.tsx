import { ActivityCard } from './ActivityCard';
import { TravelConnector } from './TravelConnector';

interface ItineraryFeedProps {
  selectedDay: number;
}

const itineraryData = {
  1: {
    morning: [
      {
        id: 1,
        title: 'City Palace',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1716534133704-5a5c2a9c7512?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxDaXR5JTIwUGFsYWNlJTIwSmFpcHVyfGVufDF8fHx8MTc2ODM5NjAyNHww&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    afternoon: [
      {
        id: 2,
        title: 'Hawa Mahal',
        duration: '1 hr',
        image: 'https://images.unsplash.com/photo-1707793044127-bf3b560353e2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxIYXdhJTIwTWFoYWwlMjBKYWlwdXJ8ZW58MXx8fHwxNzY4NTAxNDg4fDA&ixlib=rb-4.1.0&q=80&w=1080',
      },
      {
        id: 3,
        title: 'Jantar Mantar',
        duration: '1.5 hrs',
        image: 'https://images.unsplash.com/photo-1765734319376-21a84129cb65?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxKYW50YXIlMjBNYW50YXIlMjBvYnNlcnZhdG9yeXxlbnwxfHx8fDE3Njg1MDA4Nzh8MA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    evening: [
      {
        id: 4,
        title: 'Local Cuisine Dinner',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1728910758653-7e990e489cac?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxJbmRpYW4lMjByZXN0YXVyYW50JTIwZm9vZHxlbnwxfHx8fDE3Njg0Nzk4NDN8MA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
  },
  2: {
    morning: [
      {
        id: 5,
        title: 'Amber Fort',
        duration: '3 hrs',
        image: 'https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxBbWJlciUyMEZvcnQlMjBKYWlwdXJ8ZW58MXx8fHwxNzY4NTAwODc2fDA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    afternoon: [
      {
        id: 6,
        title: 'Jaigarh Fort',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxBbWJlciUyMEZvcnQlMjBKYWlwdXJ8ZW58MXx8fHwxNzY4NTAwODc2fDA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    evening: [
      {
        id: 7,
        title: 'Shopping at Johari Bazaar',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1743501948037-595a518f2aca?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxKYWlwdXIlMjBiYXphYXIlMjBtYXJrZXR8ZW58MXx8fHwxNzY4NTAxNDg5fDA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
  },
  3: {
    morning: [
      {
        id: 8,
        title: 'Albert Hall Museum',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1716534133704-5a5c2a9c7512?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxDaXR5JTIwUGFsYWNlJTIwSmFpcHVyfGVufDF8fHx8MTc2ODM5NjAyNHww&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    afternoon: [
      {
        id: 9,
        title: 'Nahargarh Fort',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxBbWJlciUyMEZvcnQlMjBKYWlwdXJ8ZW58MXx8fHwxNzY4NTAwODc2fDA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
    evening: [
      {
        id: 10,
        title: 'Farewell Dinner',
        duration: '2 hrs',
        image: 'https://images.unsplash.com/photo-1728910758653-7e990e489cac?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxJbmRpYW4lMjByZXN0YXVyYW50JTIwZm9vZHxlbnwxfHx8fDE3Njg0Nzk4NDN8MA&ixlib=rb-4.1.0&q=80&w=1080',
      },
    ],
  },
};

export function ItineraryFeed({ selectedDay }: ItineraryFeedProps) {
  const dayData = itineraryData[selectedDay as keyof typeof itineraryData];

  return (
    <div className="flex-1 overflow-y-auto pb-32 px-4">
      {/* Morning */}
      <section className="mt-6">
        <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">MORNING</h2>
        <div className="space-y-0">
          {dayData.morning.map((activity, idx) => (
            <div key={activity.id}>
              <ActivityCard {...activity} />
              {idx < dayData.morning.length - 1 && <TravelConnector time="10 min" />}
            </div>
          ))}
        </div>
        <TravelConnector time="15 min" />
      </section>

      {/* Afternoon */}
      <section className="mt-0">
        <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">AFTERNOON</h2>
        <div className="space-y-0">
          {dayData.afternoon.map((activity, idx) => (
            <div key={activity.id}>
              <ActivityCard {...activity} />
              {idx < dayData.afternoon.length - 1 && <TravelConnector time="12 min" />}
            </div>
          ))}
        </div>
        <TravelConnector time="20 min" />
      </section>

      {/* Evening */}
      <section className="mt-0">
        <h2 className="text-xs tracking-widest text-gray-500 mb-3 px-1">EVENING</h2>
        <div className="space-y-0">
          {dayData.evening.map((activity) => (
            <ActivityCard key={activity.id} {...activity} />
          ))}
        </div>
      </section>
    </div>
  );
}
