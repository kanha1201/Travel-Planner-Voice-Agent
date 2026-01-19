import { X, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Source } from '../types';

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
  sources?: Source[];
}

export function SourcesModal({ isOpen, onClose, sources = [] }: SourcesModalProps) {
  // Debug logging
  console.log('📋 SourcesModal render - isOpen:', isOpen, 'sources:', sources.length, sources);
  
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
                {(() => {
                  console.log('🔍 SourcesModal - Rendering sources list:', {
                    sourcesLength: sources.length,
                    sources: sources,
                    isOpen: isOpen
                  });
                  return null;
                })()}
                {sources.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <p className="text-sm">No sources available yet.</p>
                    <p className="text-xs text-gray-400 mt-2">
                      Sources will appear here after generating an itinerary or asking questions.
                    </p>
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {sources.map((source, index) => {
                      console.log(`📄 Rendering source ${index} in modal:`, source);
                      return (
                        <li
                          key={source.id || `source-${index}-${source.name}-${source.url}`}
                          className="py-3 border-b border-gray-100 last:border-0"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="text-gray-900 font-medium">{source.name || 'Unknown Source'}</div>
                              {source.type && (
                                <div className="text-sm text-gray-500 mt-1">{source.type}</div>
                              )}
                              {source.url && (
                                <div className="text-xs text-gray-400 mt-1 truncate">
                                  {source.url}
                                </div>
                              )}
                            </div>
                            {source.url && (
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-shrink-0 text-blue-600 hover:text-blue-800 transition-colors"
                                aria-label={`Open ${source.name}`}
                                title={source.url}
                              >
                                <ExternalLink size={16} />
                              </a>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}







