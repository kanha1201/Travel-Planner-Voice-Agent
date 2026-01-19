import { Info } from 'lucide-react';

interface HeaderProps {
  onInfoClick: () => void;
  activeTab: 'plan' | 'voice';
  onTabChange: (tab: 'plan' | 'voice') => void;
}

export function Header({ onInfoClick, activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200">
      {/* Title Bar */}
      <div className="px-4 py-4 flex items-center justify-between">
        <div className="w-6" /> {/* Spacer for centering */}
        <h1 className="text-lg text-gray-900 tracking-tight">Gyde</h1>
        <button
          onClick={onInfoClick}
          className="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors"
          aria-label="View sources"
        >
          <Info size={20} />
        </button>
      </div>
      
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => onTabChange('voice')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
            activeTab === 'voice'
              ? 'text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Voice Chat
          {activeTab === 'voice' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
          )}
        </button>
        <button
          onClick={() => onTabChange('plan')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
            activeTab === 'plan'
              ? 'text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Plan
          {activeTab === 'plan' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
          )}
        </button>
      </div>
    </header>
  );
}