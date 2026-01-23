// frontend/src/components/ResultsView.tsx
'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp, FileText } from 'lucide-react';

interface ResultsViewProps {
  data: any;
  onReset: () => void;
}

export default function ResultsView({ data, onReset }: ResultsViewProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'explanations' | 'next_steps'>('summary');
  
  // Helper to get color based on urgency
  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MODERATE': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header / Triage Banner */}
      <div className={`p-6 rounded-xl border ${getUrgencyColor(data.triage.overall_urgency)}`}>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              {data.triage.overall_urgency === 'CRITICAL' && <AlertTriangle className="h-6 w-6" />}
              Urgency: {data.triage.overall_urgency}
            </h2>
            <p className="mt-2 text-lg font-medium opacity-90">
              {data.triage.recommendation}
            </p>
          </div>
          <button 
            onClick={onReset}
            className="px-4 py-2 bg-white bg-opacity-50 hover:bg-opacity-80 rounded-lg text-sm font-medium transition-colors"
          >
            Analyze Another
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['summary', 'explanations', 'next_steps'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1).replace('_', ' ')}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 min-h-[400px] p-6">
        
        {/* SUMMARY TAB */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard label="Total Tests" value={data.parsed.tests.length} />
              <StatCard label="Abnormal" value={data.parsed.tests.filter((t: any) => t.is_abnormal).length} type="warning" />
              <StatCard label="Critical" value={data.triage.critical_count} type="danger" />
            </div>

            <div className="overflow-hidden border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Range</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.parsed.tests.map((test: any, idx: number) => (
                    <tr key={idx} className={test.is_abnormal ? 'bg-red-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{test.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{test.value} {test.unit}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{test.reference_range}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {test.is_abnormal ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {test.flag || 'Abnormal'}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Normal
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* EXPLANATIONS TAB */}
        {activeTab === 'explanations' && (
          <div className="space-y-4">
            {Object.entries(data.explanations).map(([name, explanation]: [string, any]) => (
              <ExplanationCard key={name} name={name} explanation={explanation} />
            ))}
          </div>
        )}

        {/* NEXT STEPS TAB */}
        {activeTab === 'next_steps' && (
          <div className="prose max-w-none">
            <ul className="space-y-3">
              {data.triage.next_steps.map((step: string, idx: number) => (
                <li key={idx} className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// Sub-components
function StatCard({ label, value, type = 'default' }: { label: string, value: number, type?: 'default' | 'warning' | 'danger' }) {
  const colors = {
    default: 'text-gray-900',
    warning: 'text-orange-600',
    danger: 'text-red-600'
  };
  
  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-center">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className={`text-3xl font-bold ${colors[type]}`}>{value}</p>
    </div>
  );
}

function ExplanationCard({ name, explanation }: { name: string, explanation: any }) {
  const [isOpen, setIsOpen] = useState(explanation.is_abnormal);

  return (
    <div className={`border rounded-lg transition-colors ${explanation.is_abnormal ? 'border-orange-200 bg-orange-50' : 'border-gray-200'}`}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          {explanation.is_abnormal ? <AlertTriangle className="h-5 w-5 text-orange-500" /> : <Info className="h-5 w-5 text-blue-500" />}
          <span className="font-semibold text-gray-900">{name}</span>
        </div>
        {isOpen ? <ChevronUp className="h-5 w-5 text-gray-500" /> : <ChevronDown className="h-5 w-5 text-gray-500" />}
      </button>
      
      {isOpen && (
        <div className="px-4 pb-4 border-t border-gray-200/50 pt-4">
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line">
            {explanation.text}
          </div>
          {explanation.sources && explanation.sources.length > 0 && (
            <div className="mt-3 text-xs text-gray-500 flex items-center gap-1">
              <FileText className="h-3 w-3" />
              Sources: {explanation.sources.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}