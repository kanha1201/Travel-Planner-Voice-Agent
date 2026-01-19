export interface Activity {
  activity_id?: string;
  name: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  travel_from_previous?: number;
  category?: string;
  type?: string;
  description?: string;
  location?: {
    lat: number;
    lon: number;
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
  url?: string;
  source?: string;
  section?: string;
  activities?: string[];
  title?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface ApiResponse {
  status: 'success' | 'error';
  response: string;
  itinerary?: Itinerary;
  sources?: Source[];
  session_id?: string;
  tool_calls?: Array<{
    function: string;
    arguments: Record<string, any>;
  }>;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  error?: string;
}










