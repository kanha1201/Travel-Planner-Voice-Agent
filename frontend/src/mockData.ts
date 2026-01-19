import { Itinerary, Source } from './types';

export const mockItinerary: Itinerary = {
  day_1: {
    date: "2024-01-15",
    morning: [
      {
        activity_id: "osm_12345",
        name: "Amber Fort",
        start_time: "09:00",
        end_time: "12:00",
        duration_minutes: 180,
        travel_from_previous: 0,
        category: "cultural",
        type: "History",
        description: "Historic fort with stunning architecture and panoramic views of the city. A UNESCO World Heritage site.",
        location: {
          lat: 26.9855,
          lon: 75.8513
        }
      }
    ],
    afternoon: [
      {
        activity_id: "osm_12346",
        name: "Jal Mahal",
        start_time: "14:00",
        end_time: "15:30",
        duration_minutes: 90,
        travel_from_previous: 30,
        category: "sightseeing",
        type: "Sightseeing",
        description: "Beautiful water palace located in the middle of Man Sagar Lake. Perfect for photography.",
        location: {
          lat: 26.9535,
          lon: 75.8465
        }
      }
    ],
    evening: [
      {
        activity_id: "osm_12347",
        name: "Chokhi Dhani",
        start_time: "18:00",
        end_time: "21:00",
        duration_minutes: 180,
        travel_from_previous: 20,
        category: "food",
        type: "Cultural Experience",
        description: "Traditional Rajasthani village resort with authentic food and cultural performances.",
        location: {
          lat: 26.9124,
          lon: 75.7873
        }
      }
    ]
  },
  day_2: {
    date: "2024-01-16",
    morning: [
      {
        activity_id: "osm_12348",
        name: "City Palace",
        start_time: "09:30",
        end_time: "12:00",
        duration_minutes: 150,
        travel_from_previous: 0,
        category: "cultural",
        type: "History",
        description: "The royal residence of the Maharaja of Jaipur, featuring beautiful courtyards and museums.",
        location: {
          lat: 26.9258,
          lon: 75.8236
        }
      }
    ],
    afternoon: [
      {
        activity_id: "osm_12349",
        name: "Jantar Mantar",
        start_time: "14:00",
        end_time: "15:30",
        duration_minutes: 90,
        travel_from_previous: 5,
        category: "cultural",
        type: "History",
        description: "An astronomical observatory with ancient instruments for measuring time and celestial positions.",
        location: {
          lat: 26.9247,
          lon: 75.8246
        }
      }
    ],
    evening: []
  }
};

export const mockSources: Source[] = [
  {
    url: "https://en.wikivoyage.org/wiki/Jaipur#See",
    source: "Wikivoyage",
    section: "See",
    activities: ["City Palace", "Jantar Mantar", "Amber Fort"]
  },
  {
    url: "https://www.openstreetmap.org/node/12345",
    source: "OpenStreetMap",
    section: "Points of Interest",
    activities: ["Jal Mahal"]
  }
];










