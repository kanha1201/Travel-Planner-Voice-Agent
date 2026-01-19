/**
 * API client for backend communication
 */

const API_BASE_URL = '/api';

export interface VoiceChatResponse {
  session_id: string;
  transcribed_text: string;
  ai_response: string;
  audio_url?: string;
}

export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId: string | null
): Promise<{ audioBlob: Blob; sessionId: string; transcribedText: string; aiResponse: string; sources: any[] }> {
  const formData = new FormData();
  // Use the actual blob type to determine filename extension
  const extension = audioBlob.type.includes('webm') ? 'webm' : 
                    audioBlob.type.includes('wav') ? 'wav' :
                    audioBlob.type.includes('ogg') ? 'ogg' : 'webm';
  formData.append('audio', audioBlob, `recording.${extension}`);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  formData.append('language', 'en');
  formData.append('voice', 'default');
  formData.append('speed', '1.0');

  const response = await fetch(`${API_BASE_URL}/voice/chat`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  // Get session ID from headers
  const newSessionId = response.headers.get('X-Session-Id') || sessionId || '';
  
  // Get text headers (may be base64 encoded)
  const encoding = response.headers.get('X-Encoding');
  let transcribedText = response.headers.get('X-Transcribed-Text') || '';
  let aiResponse = response.headers.get('X-AI-Response') || '';
  let sources: any[] = [];
  
  // Decode base64 if encoding is specified
  if (encoding === 'base64') {
    try {
      if (transcribedText) {
        transcribedText = atob(transcribedText);
      }
      if (aiResponse) {
        aiResponse = atob(aiResponse);
      }
      
      // Decode sources if present
      const encodedSources = response.headers.get('X-Sources');
      if (encodedSources) {
        try {
          const sourcesJson = atob(encodedSources);
          sources = JSON.parse(sourcesJson);
        } catch (error) {
          console.error('Error decoding sources:', error);
        }
      }
    } catch (error) {
      console.error('Error decoding base64 headers:', error);
      // If decoding fails, use the raw values (might be plain text)
    }
  }

  // Get audio response
  const responseAudioBlob = await response.blob();

  return {
    audioBlob: responseAudioBlob,
    sessionId: newSessionId,
    transcribedText,
    aiResponse,
    sources,
  };
}

export async function getItinerary(sessionId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/trip/session/${sessionId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch itinerary: ${response.status}`);
  }

  return response.json();
}

export async function getSources(sessionId: string): Promise<any[]> {
  try {
    const sessionData = await getItinerary(sessionId);
    return sessionData.sources || [];
  } catch (error) {
    console.error('Error fetching sources:', error);
    return [];
  }
}

