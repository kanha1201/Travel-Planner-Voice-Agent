import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const sources = [
  { id: 1, name: 'OpenStreetMap Data', type: 'Mapping' },
  { id: 2, name: 'Wikivoyage: Jaipur Guide', type: 'Travel Guide' },
  { id: 3, name: 'Google Places API', type: 'Business Data' },
  { id: 4, name: 'TripAdvisor Reviews', type: 'User Reviews' },
  { id: 5, name: 'Local Tourism Board', type: 'Official Info' },
];

export function SourcesModal({ isOpen, onClose }: SourcesModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 z-50"
          />

          {/* Bottom Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 max-w-[393px] mx-auto"
          >
            <div className="bg-white rounded-t-3xl shadow-2xl max-h-[50vh] overflow-hidden">
              {/* Header */}
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <h2 className="text-lg text-gray-900">Data Sources</h2>
                <button
                  onClick={onClose}
                  className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-900 transition-colors"
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Sources List */}
              <div className="overflow-y-auto max-h-[calc(50vh-65px)] px-6 py-4">
                <ul className="space-y-3">
                  {sources.map((source) => (
                    <li
                      key={source.id}
                      className="py-3 border-b border-gray-100 last:border-0"
                    >
                      <div className="text-gray-900">{source.name}</div>
                      <div className="text-sm text-gray-500 mt-1">{source.type}</div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
