// frontend/src/app/page.tsx
'use client';

import Link from 'next/link';
import { Activity, ShieldCheck, FileText, BrainCircuit, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Activity className="h-8 w-8 text-blue-600" />
          <span className="text-xl font-bold text-gray-900">MedReport AI</span>
        </div>
        <div className="flex gap-4">
          <Link 
            href="/login" 
            className="text-gray-600 hover:text-gray-900 font-medium px-4 py-2"
          >
            Sign in
          </Link>
          <Link 
            href="/signup" 
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-24">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-5xl font-extrabold text-gray-900 tracking-tight mb-8">
            Understand Your Medical Reports with <span className="text-blue-600">AI Precision</span>
          </h1>
          <p className="text-xl text-gray-600 mb-10 leading-relaxed">
            Stop guessing what your lab results mean. Upload your report and get instant, 
            plain-English explanations, safety alerts, and actionable next steps.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/signup" 
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl"
            >
              Analyze My Report Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link 
              href="/login" 
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-gray-700 bg-white border-2 border-gray-200 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all"
            >
              Log In
            </Link>
          </div>
          
          <p className="mt-6 text-sm text-gray-500">
            🔒 Your data is processed securely and never stored permanently.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-24">
          <FeatureCard 
            icon={<FileText className="h-8 w-8 text-blue-500" />}
            title="Instant Parsing"
            desc="Upload PDF or text files. Our AI extracts test names, values, and flags automatically."
          />
          <FeatureCard 
            icon={<BrainCircuit className="h-8 w-8 text-purple-500" />}
            title="Smart Explanations"
            desc="Get clear, jargon-free explanations for every test result, powered by advanced LLMs."
          />
          <FeatureCard 
            icon={<ShieldCheck className="h-8 w-8 text-green-500" />}
            title="Safety First"
            desc="Automatic triage detects critical values and provides urgent recommendations when needed."
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="mb-4 bg-gray-50 w-16 h-16 rounded-xl flex items-center justify-center">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{desc}</p>
    </div>
  );
}