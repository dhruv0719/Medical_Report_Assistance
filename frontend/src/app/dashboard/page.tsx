// frontend/src/app/dashboard/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import FileUpload from '@/components/FileUpload';
import ResultsView from '@/components/ResultsView';

export default function Dashboard() {
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const router = useRouter();

  // Protect the route
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {!analysisResult ? (
          <div className="space-y-8">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900">Upload Your Lab Report</h1>
              <p className="mt-2 text-lg text-gray-600">
                Get instant, AI-powered analysis of your medical results.
              </p>
            </div>
            
            <FileUpload onAnalysisComplete={setAnalysisResult} />
            
            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
              <FeatureCard 
                title="Smart Parsing" 
                desc="Automatically extracts test names, values, and ranges from PDFs or images."
              />
              <FeatureCard 
                title="AI Explanations" 
                desc="Uses advanced LLMs to explain complex medical terms in plain English."
              />
              <FeatureCard 
                title="Safety Triage" 
                desc="Immediately flags critical values that require urgent attention."
              />
            </div>
          </div>
        ) : (
          <ResultsView 
            data={analysisResult} 
            onReset={() => setAnalysisResult(null)} 
          />
        )}
      </main>
    </div>
  );
}

function FeatureCard({ title, desc }: { title: string, desc: string }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{desc}</p>
    </div>
  );
}