export interface TranscriptMessage {
  type: 'user' | 'assistant';
  text: string;
  timestamp?: Date;
}

export interface Activity {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  category?: string;
  location?: {
    lat?: number;
    lng?: number;
    address?: string;
  };
}

export interface DayItinerary {
  date?: string;
  morning: Activity[];
  afternoon: Activity[];
  evening: Activity[];
}

export interface Itinerary {
  day_1?: DayItinerary;
  day_2?: DayItinerary;
  day_3?: DayItinerary;
}

export interface Source {
  id: string;
  name: string;
  type: string;
  url?: string;
}

export interface ApiResponse {
  status: string;
  response: string;
  session_id: string;
  itinerary?: Itinerary;
  sources?: Source[];
}







