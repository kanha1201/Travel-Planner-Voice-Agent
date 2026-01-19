import { useState, useEffect } from 'react';
import { MessageCircle, Calendar } from 'lucide-react';
import ChatPanel from './components/ChatPanel';
import ItineraryDisplay from './components/ItineraryDisplay';
import DebugPanel from './components/DebugPanel';
import { Message, Itinerary, Source, ApiResponse } from './types';
import { mockItinerary, mockSources } from './mockData';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'plan'>('chat');
  const [useMockData, setUseMockData] = useState(false);

  // Check if we're on mobile
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (useMockData) {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 1500));
        
        const mockResponse: Message = {
          role: 'assistant',
          content: "I've created your 2-day cultural trip to Jaipur! Here's your itinerary.",
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, mockResponse]);
        setItinerary(mockItinerary);
        setSources(mockSources);
      } else {
        const response = await fetch('/api/trip/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: content,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: ApiResponse = await response.json();

        if (data.status === 'success') {
          const assistantMessage: Message = {
            role: 'assistant',
            content: data.response,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, assistantMessage]);

          // Always update itinerary if present, even if it's the same structure
          // This ensures edits are reflected in the UI
          if (data.itinerary) {
            // Deep clone to ensure React detects the change
            const updatedItinerary = JSON.parse(JSON.stringify(data.itinerary));
            console.log('📋 Received itinerary from API:', updatedItinerary);
            console.log('📋 Day 2 morning activities:', updatedItinerary?.day_2?.morning);
            setItinerary(updatedItinerary);
          } else {
            // If no itinerary in response, keep existing one (for edit requests that don't rebuild)
            console.log('⚠️ No itinerary in response, keeping existing');
          }

          if (data.sources) {
            setSources(data.sources);
          }

          if (data.session_id) {
            setSessionId(data.session_id);
          }
        } else {
          throw new Error(data.error || 'Unknown error occurred');
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}. ${useMockData ? '' : 'You can enable mock data mode to test the UI.'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Calendar className="w-6 h-6 text-blue-500" />
          <h1 className="text-xl font-bold text-gray-900">Jaipur Travel Planner</h1>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Testing Interface</span>
        </div>
        <label className="flex items-center space-x-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={useMockData}
            onChange={(e) => setUseMockData(e.target.checked)}
            className="rounded"
          />
          <span>Use Mock Data</span>
        </label>
      </header>

      {/* Main Content */}
      {isMobile ? (
        // Mobile: Tabbed View
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'chat' ? (
            <div className="flex-1 overflow-hidden">
              <ChatPanel
                messages={messages}
                onSendMessage={sendMessage}
                isLoading={isLoading}
              />
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex-1 overflow-hidden">
                <ItineraryDisplay itinerary={itinerary} />
              </div>
              <div className="border-t border-gray-200">
                <DebugPanel sources={sources} itinerary={itinerary} />
              </div>
            </div>
          )}

          {/* Bottom Navigation */}
          <div className="bg-white border-t border-gray-200 flex">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 flex flex-col items-center justify-center py-3 space-y-1 transition-colors ${
                activeTab === 'chat'
                  ? 'text-blue-500 bg-blue-50'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <MessageCircle className="w-5 h-5" />
              <span className="text-xs font-medium">Chat</span>
            </button>
            <button
              onClick={() => setActiveTab('plan')}
              className={`flex-1 flex flex-col items-center justify-center py-3 space-y-1 transition-colors ${
                activeTab === 'plan'
                  ? 'text-blue-500 bg-blue-50'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Calendar className="w-5 h-5" />
              <span className="text-xs font-medium">Plan</span>
            </button>
          </div>
        </div>
      ) : (
        // Desktop: Split Screen
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel: Chat (40%) */}
          <div className="w-[40%] border-r border-gray-200 flex flex-col">
            <ChatPanel
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* Right Panel: Itinerary & Debug (60%) */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-hidden">
              <ItineraryDisplay itinerary={itinerary} />
            </div>
            <div className="border-t border-gray-200">
              <DebugPanel sources={sources} itinerary={itinerary} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;



