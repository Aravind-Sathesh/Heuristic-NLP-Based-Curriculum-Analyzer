'use client';

import {
  Info,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  XCircle,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { AnalysisResults } from '@/types/api';

interface ResultsProps {
  isLoading: boolean;
  error: string | null;
  results: AnalysisResults | null;
}

export default function Results({ isLoading, error, results }: ResultsProps) {
  if (!isLoading && !error && !results) {
    return (
      <Card className='bg-white rounded-lg shadow-md p-6 border border-blue-100'>
        <div className='flex items-center gap-3 text-blue-600'>
          <Info className='w-5 h-5 flex-shrink-0' />
          <p className='font-medium'>
            Upload your curriculum and question paper documents to get a
            detailed analysis with actionable insights.
          </p>
        </div>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className='bg-white rounded-lg shadow-md p-8 border border-blue-100'>
        <div className='flex flex-col items-center justify-center gap-4'>
          <div className='relative w-16 h-16'>
            <Loader2 className='w-16 h-16 text-blue-600 animate-spin' />
            <div className='absolute inset-0 bg-blue-100 rounded-full opacity-20 animate-pulse' />
          </div>
          <div className='text-center'>
            <p className='text-lg font-semibold text-blue-900'>
              Analyzing Documents
            </p>
            <p className='text-sm text-blue-600 mt-1'>
              Extracting topics, analyzing questions, and generating insights...
            </p>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert className='bg-red-50 border-red-300'>
        <AlertTriangle className='h-5 w-5 text-red-600' />
        <div>
          <h3 className='font-semibold text-red-900'>Analysis Failed</h3>
          <AlertDescription className='text-red-700 mt-1'>
            {error}
          </AlertDescription>
        </div>
      </Alert>
    );
  }

  if (!results) return null;

  const getCoverageColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-blue-600';
    if (percentage >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCoverageBgColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-50 border-green-200';
    if (percentage >= 60) return 'bg-blue-50 border-blue-200';
    if (percentage >= 40) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <Card className='bg-white rounded-lg shadow-md p-6 border border-blue-100'>
      {/* Coverage Score */}
      <div
        className={`rounded-lg p-6 border-2 ${getCoverageBgColor(
          results.coveragePercentage
        )}`}
      >
        <div className='flex items-center justify-between'>
          <div>
            <h2 className='text-sm font-medium text-gray-600 mb-1'>
              Curriculum Coverage
            </h2>
            <p
              className={`text-5xl font-bold ${getCoverageColor(
                results.coveragePercentage
              )}`}
            >
              {results.coveragePercentage}%
            </p>
          </div>
          <div className='text-right'>
            <p className='text-sm text-gray-600'>
              <span className='font-semibold text-green-600'>
                {results.testedTopics.length}
              </span>{' '}
              tested
            </p>
            <p className='text-sm text-gray-600'>
              <span className='font-semibold text-red-600'>
                {results.missedTopics.length}
              </span>{' '}
              missed
            </p>
          </div>
        </div>
      </div>

      {/* Insights Section */}
      <div className='mt-6 space-y-4'>
        {/* Strengths */}
        {results.insights.strengths.length > 0 && (
          <div className='border-l-4 border-green-500 bg-green-50 p-4 rounded-r'>
            <div className='flex items-start gap-3'>
              <CheckCircle2 className='w-5 h-5 text-green-600 flex-shrink-0 mt-0.5' />
              <div className='flex-1'>
                <h3 className='font-semibold text-green-900 mb-2'>Strengths</h3>
                <ul className='space-y-2'>
                  {results.insights.strengths.map((strength, idx) => (
                    <li key={idx} className='text-sm text-green-800'>
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Weaknesses */}
        {results.insights.weaknesses.length > 0 && (
          <div className='border-l-4 border-orange-500 bg-orange-50 p-4 rounded-r'>
            <div className='flex items-start gap-3'>
              <AlertCircle className='w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5' />
              <div className='flex-1'>
                <h3 className='font-semibold text-orange-900 mb-2'>
                  Areas for Improvement
                </h3>
                <ul className='space-y-2'>
                  {results.insights.weaknesses.map((weakness, idx) => (
                    <li key={idx} className='text-sm text-orange-800'>
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {results.insights.recommendations.length > 0 && (
          <div className='border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r'>
            <div className='flex items-start gap-3'>
              <Lightbulb className='w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5' />
              <div className='flex-1'>
                <h3 className='font-semibold text-blue-900 mb-2'>
                  Recommendations
                </h3>
                <ul className='space-y-2'>
                  {results.insights.recommendations.map(
                    (recommendation, idx) => (
                      <li key={idx} className='text-sm text-blue-800'>
                        • {recommendation}
                      </li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Detailed Breakdown Accordion */}
      <Accordion type='single' collapsible className='mt-6'>
        <AccordionItem value='details'>
          <AccordionTrigger className='text-lg font-semibold text-blue-900 hover:text-blue-700'>
            Topic-by-Topic Analysis
          </AccordionTrigger>
          <AccordionContent className='pt-4'>
            <div className='space-y-3'>
              {results.topicAnalysis.map((topic, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${
                    topic.tested
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className='flex items-start justify-between'>
                    <div className='flex-1'>
                      <div className='flex items-center gap-2 mb-2'>
                        {topic.tested ? (
                          <CheckCircle2 className='w-4 h-4 text-green-600' />
                        ) : (
                          <XCircle className='w-4 h-4 text-red-600' />
                        )}
                        <h4 className='font-semibold text-gray-900'>
                          {topic.topic}
                        </h4>
                      </div>

                      {topic.tested && topic.questionNumbers && (
                        <div className='ml-6 space-y-1 text-sm'>
                          <p className='text-gray-700'>
                            <span className='font-medium'>Questions:</span>{' '}
                            {topic.questionNumbers.join(', ')}
                            <span className='text-gray-500 ml-2'>
                              ({topic.questionCount} question
                              {topic.questionCount !== 1 ? 's' : ''},{' '}
                              {topic.totalMarks} marks)
                            </span>
                          </p>

                          {topic.dominantBloom && (
                            <p className='text-gray-700'>
                              <span className='font-medium'>
                                Cognitive Level:
                              </span>{' '}
                              {topic.dominantBloom}
                              {topic.curriculumExpectedBloom &&
                                topic.bloomMatch !== null && (
                                  <span
                                    className={
                                      topic.bloomMatch
                                        ? 'text-green-600 ml-2'
                                        : 'text-orange-600 ml-2'
                                    }
                                  >
                                    {topic.bloomMatch
                                      ? '✓ Matches curriculum'
                                      : `⚠ Expected ${topic.curriculumExpectedBloom}`}
                                  </span>
                                )}
                            </p>
                          )}

                          {topic.bloomDistribution &&
                            Object.keys(topic.bloomDistribution).length > 1 && (
                              <p className='text-gray-600 text-xs'>
                                Distribution:{' '}
                                {Object.entries(topic.bloomDistribution)
                                  .map(
                                    ([level, count]) => `${level} (${count})`
                                  )
                                  .join(', ')}
                              </p>
                            )}
                        </div>
                      )}

                      {!topic.tested && topic.curriculumExpectedBloom && (
                        <p className='ml-6 text-sm text-red-700'>
                          Expected cognitive level:{' '}
                          {topic.curriculumExpectedBloom}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );
}
