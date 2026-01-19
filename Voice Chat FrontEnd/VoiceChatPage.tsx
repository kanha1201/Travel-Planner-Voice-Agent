import { Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export interface TranscriptMessage {
  type: 'user' | 'assistant';
  text: string;
}

interface VoiceChatPageProps {
  isListening: boolean;
  onToggleListening: () => void;
  transcript: TranscriptMessage[];
}

export function VoiceChatPage({ isListening, onToggleListening, transcript }: VoiceChatPageProps) {
  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Transcript Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-xs">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mic size={32} className="text-blue-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Voice Assistant</h2>
              <p className="text-sm text-gray-600">
                Tap the microphone button below to start a conversation about your Jaipur trip
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
                  <p className="text-sm leading-relaxed">{message.text}</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Voice Button Area */}
      <div className="bg-white border-t border-gray-200 p-6">
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
            className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all ${
              isListening
                ? 'bg-red-500 hover:bg-red-600 scale-110'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
          >
            <Mic size={28} className="text-white" />
          </button>

          <p className="text-xs text-gray-500">
            {isListening ? 'Tap to stop' : 'Tap to speak'}
          </p>
        </div>
      </div>
    </div>
  );
}
