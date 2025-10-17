// API Response Types

export interface BloomProfile {
  Remembering: number;
  Understanding: number;
  Applying: number;
  Analyzing: number;
  Evaluating: number;
  Creating: number;
}

export interface TopicProfile {
  topicName: string;
  bloomProfile: BloomProfile;
}

export interface CurriculumAnalysisData {
  topicProfiles: TopicProfile[];
}

export interface Question {
  number: string;
  text: string;
  topic?: string;
  bloomLevel?: string;
  subQuestions?: Question[];
}

export interface QuestionPaperAnalysisData {
  questions: Question[];
}

export interface TopicAnalysis {
  topic: string;
  tested: boolean;
  questionCount?: number;
  totalMarks?: number;
  questionNumbers?: string[];
  bloomDistribution?: Record<string, number>;
  dominantBloom?: string;
  curriculumExpectedBloom?: string;
  bloomMatch?: boolean;
}

export interface Insights {
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface AnalysisResults {
  status: string;
  coveragePercentage: number;
  testedTopics: string[];
  missedTopics: string[];
  topicAnalysis: TopicAnalysis[];
  insights: Insights;
  curriculumData?: CurriculumAnalysisData;
  questionPaperData?: QuestionPaperAnalysisData;
}

export interface AnalysisError {
  error: string;
}

export type AnalysisResponse = AnalysisResults | AnalysisError;
