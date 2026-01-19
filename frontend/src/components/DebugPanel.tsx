import { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, Code } from 'lucide-react';
import { Source, Itinerary } from '../types';

interface DebugPanelProps {
  sources: Source[];
  itinerary: Itinerary | null;
}

export default function DebugPanel({ sources, itinerary }: DebugPanelProps) {
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [rawStateOpen, setRawStateOpen] = useState(false);

  return (
    <div className="bg-white border-t border-gray-200 p-4 space-y-4 max-h-[400px] overflow-y-auto">
      {/* Sources Accordion */}
      <div className="border border-gray-200 rounded-lg">
        <button
          onClick={() => setSourcesOpen(!sourcesOpen)}
          className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors rounded-t-lg"
        >
          <div className="flex items-center space-x-2">
            <ExternalLink className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-900">Sources ({sources.length})</span>
          </div>
          {sourcesOpen ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </button>
        
        {sourcesOpen && (
          <div className="p-4 space-y-3">
            {sources.length === 0 ? (
              <p className="text-sm text-gray-500">No sources available</p>
            ) : (
              sources.map((source, index) => (
                <div key={index} className="border-l-2 border-blue-500 pl-3 py-2">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900">
                        {source.source || 'Unknown Source'}
                      </p>
                      {source.section && (
                        <p className="text-xs text-gray-600 mt-1">Section: {source.section}</p>
                      )}
                      {source.activities && source.activities.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-600 mb-1">Activities:</p>
                          <div className="flex flex-wrap gap-1">
                            {source.activities.map((activity, i) => (
                              <span
                                key={i}
                                className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
                              >
                                {activity}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-blue-500 hover:text-blue-700"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Raw State Accordion */}
      <div className="border border-gray-200 rounded-lg">
        <button
          onClick={() => setRawStateOpen(!rawStateOpen)}
          className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors rounded-t-lg"
        >
          <div className="flex items-center space-x-2">
            <Code className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-900">Raw State (JSON)</span>
          </div>
          {rawStateOpen ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </button>
        
        {rawStateOpen && (
          <div className="p-4">
            {itinerary ? (
              <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto">
                {JSON.stringify(itinerary, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-gray-500">No itinerary data available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}










