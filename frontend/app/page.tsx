'use client';

import { useState } from 'react';
import Header from '@/components/header';
import Uploader from '@/components/uploader';
import Results from '@/components/results';
import type { AnalysisResults } from '@/types/api';

export default function Home() {
  const [handoutFile, setHandoutFile] = useState<File | null>(null);
  const [questionFile, setQuestionFile] = useState<File | null>(null);
  const [useImageMode, setUseImageMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!handoutFile || !questionFile) return;

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('handout', handoutFile);
      formData.append('question', questionFile);
      formData.append('useImageMode', useImageMode.toString());

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Analysis failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className='min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-12 px-4'>
      <div className='max-w-4xl mx-auto'>
        <Header />
        <Uploader
          handoutFile={handoutFile}
          questionFile={questionFile}
          onHandoutChange={setHandoutFile}
          onQuestionChange={setQuestionFile}
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          isDisabled={!handoutFile || !questionFile}
          useImageMode={useImageMode}
          onImageModeChange={setUseImageMode}
        />
        <Results isLoading={isLoading} error={error} results={results} />
      </div>
    </main>
  );
}
