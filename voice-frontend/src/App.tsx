import { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { DaySelector } from './components/DaySelector';
import { ItineraryFeed } from './components/ItineraryFeed';
import { VoiceChatPage } from './components/VoiceChatPage';
import { SourcesModal } from './components/SourcesModal';
import { TranscriptMessage, Itinerary, DayItinerary } from './types';
import { VoiceRecorder } from './utils/voiceRecorder';
import { sendVoiceMessage, getItinerary, getSources } from './utils/api';
import { Source } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'plan' | 'voice'>('voice');
  const [selectedDay, setSelectedDay] = useState(1);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const voiceRecorderRef = useRef<VoiceRecorder | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Initialize voice recorder
  useEffect(() => {
    voiceRecorderRef.current = new VoiceRecorder();
    audioPlayerRef.current = new Audio();
    
    return () => {
      if (voiceRecorderRef.current) {
        voiceRecorderRef.current.cancelRecording();
      }
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
    };
  }, []);

  // Load itinerary when session changes
  // Note: We don't load sources here because they come from the voice response
  // Sources are loaded in handleToggleListening after the response
  useEffect(() => {
    if (sessionId) {
      loadItinerary();
      // Only load sources if we don't have any yet (initial load)
      // Otherwise, sources come from the voice response
      if (sources.length === 0) {
        loadSources().then(sessionSources => {
          if (sessionSources && sessionSources.length > 0) {
            setSources(sessionSources);
          }
        });
      }
    }
  }, [sessionId]);

  const loadItinerary = async () => {
    if (!sessionId) return;
    
    try {
      const sessionData = await getItinerary(sessionId);
      if (sessionData.current_itinerary) {
        setItinerary(sessionData.current_itinerary);
      }
    } catch (error) {
      console.error('Error loading itinerary:', error);
    }
  };

  const loadSources = async (): Promise<any[]> => {
    if (!sessionId) return [];
    
    try {
      const sourcesData = await getSources(sessionId);
      return sourcesData || [];
    } catch (error) {
      console.error('Error loading sources:', error);
      return [];
    }
  };

  const handleToggleListening = async () => {
    if (!voiceRecorderRef.current) return;

    if (isListening) {
      // Stop recording and process
      try {
        setIsListening(false);
        setIsProcessing(true);

        const audioBlob = await voiceRecorderRef.current.stopRecording();
        
        // Send to backend
        const response = await sendVoiceMessage(audioBlob, sessionId);
        
        // Update session ID
        if (response.sessionId) {
          setSessionId(response.sessionId);
        }

        // Update sources from response (if available)
        if (response.sources && response.sources.length > 0) {
          setSources(response.sources);
        }

        // Add user message to transcript
        if (response.transcribedText) {
          setTranscript(prev => [
            ...prev,
            { type: 'user', text: response.transcribedText, timestamp: new Date() }
          ]);
        }

        // Add assistant message to transcript
        if (response.aiResponse) {
          setTranscript(prev => [
            ...prev,
            { type: 'assistant', text: response.aiResponse, timestamp: new Date() }
          ]);
        }

        // Play audio response
        if (response.audioBlob) {
          const audioUrl = URL.createObjectURL(response.audioBlob);
          if (audioPlayerRef.current) {
            audioPlayerRef.current.src = audioUrl;
            audioPlayerRef.current.play().catch(error => {
              console.error('Error playing audio:', error);
            });
          }
        }

        // Reload itinerary and sources (fallback if not in response)
        await loadItinerary();
        // Only load sources from session if we didn't get them in the response
        if (!response.sources || response.sources.length === 0) {
          const sessionSources = await loadSources();
          // Only update if we got sources from session
          if (sessionSources && sessionSources.length > 0) {
            setSources(sessionSources);
          }
        }

      } catch (error) {
        console.error('Error processing voice message:', error);
        setTranscript(prev => [
          ...prev,
          { 
            type: 'assistant', 
            text: 'Sorry, I encountered an error processing your request. Please try again.', 
            timestamp: new Date() 
          }
        ]);
      } finally {
        setIsProcessing(false);
      }
    } else {
      // Start recording
      try {
        await voiceRecorderRef.current.startRecording();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting recording:', error);
        alert('Failed to start recording. Please check microphone permissions.');
      }
    }
  };

  // Get available days from itinerary
  const getAvailableDays = (): number[] => {
    if (!itinerary) return [1, 2, 3];
    
    const days: number[] = [];
    if (itinerary.day_1) days.push(1);
    if (itinerary.day_2) days.push(2);
    if (itinerary.day_3) days.push(3);
    
    return days.length > 0 ? days : [1, 2, 3];
  };

  // Get day itinerary
  const getDayItinerary = (): DayItinerary | undefined => {
    if (!itinerary) return undefined;
    
    const dayKey = `day_${selectedDay}` as keyof Itinerary;
    return itinerary[dayKey] as DayItinerary | undefined;
  };

  return (
    <div className="relative h-screen w-full max-w-[393px] mx-auto bg-white overflow-hidden flex flex-col">
      {/* Header with Tabs */}
      <Header 
        onInfoClick={() => setIsSourcesOpen(true)} 
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      
      {/* Conditional Content Based on Active Tab */}
      {activeTab === 'plan' ? (
        <>
          {/* Day Selector */}
          <DaySelector 
            selectedDay={selectedDay} 
            onSelectDay={setSelectedDay}
            availableDays={getAvailableDays()}
          />
          
          {/* Scrollable Itinerary */}
          <ItineraryFeed 
            selectedDay={selectedDay}
            itinerary={getDayItinerary()}
          />
        </>
      ) : (
        <VoiceChatPage
          isListening={isListening}
          onToggleListening={handleToggleListening}
          transcript={transcript}
          isProcessing={isProcessing}
          sources={sources}
        />
      )}
      
      {/* Sources Modal */}
      <SourcesModal 
        isOpen={isSourcesOpen} 
        onClose={() => setIsSourcesOpen(false)}
        sources={sources}
      />
    </div>
  );
}







