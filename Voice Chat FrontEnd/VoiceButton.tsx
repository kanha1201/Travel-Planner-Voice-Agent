import { Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export interface TranscriptMessage {
  type: 'user' | 'assistant';
  text: string;
}

interface VoiceButtonProps {
  isListening: boolean;
  onToggleListening: () => void;
  transcript?: TranscriptMessage[];
}

export function VoiceButton({ isListening, onToggleListening, transcript = [] }: VoiceButtonProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 pointer-events-none">
      <div className="max-w-[393px] mx-auto relative">
        {/* Live Transcript Display */}
        <AnimatePresence>
          {transcript.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-24 left-4 right-4 bg-white rounded-2xl shadow-xl border border-gray-200 pointer-events-auto max-h-[300px] overflow-y-auto"
            >
              <div className="p-4 space-y-3">
                {transcript.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: message.type === 'user' ? 20 : -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] px-4 py-2 rounded-2xl ${
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm leading-relaxed">{message.text}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Listening Indicator */}
        <AnimatePresence>
          {isListening && transcript.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute bottom-24 left-1/2 -translate-x-1/2 bg-gray-900/90 backdrop-blur-sm text-white px-4 py-2 rounded-full text-sm pointer-events-none"
            >
              Listening...
            </motion.div>
          )}
        </AnimatePresence>

        {/* Microphone FAB */}
        <div className="pb-8 flex justify-center">
          <button
            onClick={onToggleListening}
            className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all pointer-events-auto ${
              isListening
                ? 'bg-red-500 hover:bg-red-600 scale-110'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
          >
            <Mic size={28} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}