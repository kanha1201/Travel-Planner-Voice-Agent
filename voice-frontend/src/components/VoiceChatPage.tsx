import { Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { TranscriptMessage } from '../types';
import { formatMessage } from '../utils/formatMessage';

function FormattedMessage({ text }: { text: string }) {
  const formatted = formatMessage(text);
  const lines = formatted.split('\n');
  
  return (
    <div className="text-sm leading-relaxed">
      {lines.map((line, index) => {
        const trimmedLine = line.trim();
        
        // Day headers (bold, larger, with spacing)
        if (trimmedLine.match(/^\*\*Day \d+\*\*$/)) {
          return (
            <div key={index} className="font-semibold text-base mt-4 mb-2 first:mt-0">
              {trimmedLine.replace(/\*\*/g, '')}
            </div>
          );
        }
        
        // Period headers (italic, slightly indented, with spacing)
        if (trimmedLine.match(/^\*(Morning|Afternoon|Evening|Night)\*$/i)) {
          return (
            <div key={index} className="italic text-gray-600 mt-3 mb-1.5 ml-2 font-medium">
              {trimmedLine.replace(/\*/g, '')}
            </div>
          );
        }
        
        // Bullet points (indented, with proper spacing)
        if (trimmedLine.startsWith('•')) {
          return (
            <div key={index} className="ml-4 mb-1">
              {trimmedLine}
            </div>
          );
        }
        
        // Empty lines (for spacing)
        if (!trimmedLine) {
          return <div key={index} className="h-2" />;
        }
        
        // Regular text (descriptions, summaries)
        return (
          <div key={index} className={index === 0 ? '' : 'mt-2'}>
            {trimmedLine}
          </div>
        );
      })}
    </div>
  );
}

interface VoiceChatPageProps {
  isListening: boolean;
  onToggleListening: () => void;
  transcript: TranscriptMessage[];
  isProcessing?: boolean;
  sources?: any[]; // Sources are handled by SourcesModal, not displayed here
}

export function VoiceChatPage({ 
  isListening, 
  onToggleListening, 
  transcript,
  isProcessing = false,
  sources = []
}: VoiceChatPageProps) {
  return (
    <div className="flex-1 flex flex-col bg-gray-50 relative overflow-hidden">
      {/* Scrollable Transcript Area */}
      <div className="flex-1 overflow-y-auto p-4 pb-32 min-h-0">
        {transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-xs">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mic size={32} className="text-blue-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Voice Assistant</h2>
              <p className="text-sm text-gray-600">
                Tap the microphone button below to start a conversation about your trip
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-full">
            {transcript.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 border border-gray-200'
                  }`}
                >
                  {message.type === 'assistant' ? (
                    <FormattedMessage text={message.text} />
                  ) : (
                    <p className="text-sm leading-relaxed">{message.text}</p>
                  )}
                </div>
              </motion.div>
            ))}
            {isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="max-w-[85%] px-4 py-3 rounded-2xl bg-white text-gray-900 border border-gray-200">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </motion.div>
            )}
            
          </div>
        )}
      </div>

      {/* Fixed Voice Button Area at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-6 z-10">
        <div className="flex flex-col items-center gap-3">
          {/* Listening Indicator */}
          <AnimatePresence>
            {isListening && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="bg-red-100 text-red-600 px-4 py-2 rounded-full text-sm font-medium"
              >
                Listening...
              </motion.div>
            )}
          </AnimatePresence>

          {/* Microphone Button */}
          <button
            onClick={onToggleListening}
            disabled={isProcessing}
            className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all ${
              isListening
                ? 'bg-red-500 hover:bg-red-600 scale-110'
                : isProcessing
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
          >
            <Mic size={28} className="text-white" />
          </button>

          <p className="text-xs text-gray-500">
            {isProcessing ? 'Processing...' : isListening ? 'Tap to stop' : 'Tap to speak'}
          </p>
        </div>
      </div>
    </div>
  );
}





