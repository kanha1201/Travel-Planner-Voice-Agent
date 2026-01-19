import { useState } from 'react';
import { Header } from './components/Header';
import { DaySelector } from './components/DaySelector';
import { ItineraryFeed } from './components/ItineraryFeed';
import { VoiceChatPage, TranscriptMessage } from './components/VoiceChatPage';
import { SourcesModal } from './components/SourcesModal';

export default function App() {
  const [activeTab, setActiveTab] = useState<'plan' | 'voice'>('plan');
  const [selectedDay, setSelectedDay] = useState(1);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);

  const handleToggleListening = () => {
    setIsListening(!isListening);
    
    // Demo: Add a user message when starting to listen
    if (!isListening) {
      setTimeout(() => {
        setTranscript([
          { type: 'user', text: 'What should I do in the afternoon?' }
        ]);
        
        // Demo: Add assistant response after user speaks
        setTimeout(() => {
          setTranscript(prev => [
            ...prev,
            { type: 'assistant', text: 'I recommend visiting Jal Mahal around 3 PM. The palace looks stunning in the afternoon light, and it\'s a great spot for photography.' }
          ]);
        }, 1500);
      }, 1000);
    }
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
          <DaySelector selectedDay={selectedDay} onSelectDay={setSelectedDay} />
          
          {/* Scrollable Itinerary */}
          <ItineraryFeed selectedDay={selectedDay} />
        </>
      ) : (
        <VoiceChatPage
          isListening={isListening}
          onToggleListening={handleToggleListening}
          transcript={transcript}
        />
      )}
      
      {/* Sources Modal */}
      <SourcesModal isOpen={isSourcesOpen} onClose={() => setIsSourcesOpen(false)} />
    </div>
  );
}