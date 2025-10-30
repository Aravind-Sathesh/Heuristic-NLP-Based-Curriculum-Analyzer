import { type NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const handout = formData.get('handout') as File;
    const question = formData.get('question') as File;
    const useImageMode = formData.get('useImageMode') as string;

    if (!handout || !question) {
      return NextResponse.json(
        { error: 'Both files are required' },
        { status: 400 }
      );
    }

    // Get backend URL from environment variable or use default
    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

    // Create FormData for backend API
    const backendFormData = new FormData();
    backendFormData.append('curriculum', handout);
    backendFormData.append('questionPaper', question);
    backendFormData.append('useImageMode', useImageMode || 'false');

    // Call the backend API
    const response = await fetch(`${backendUrl}/api/analyze`, {
      method: 'POST',
      body: backendFormData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || 'Backend analysis failed' },
        { status: response.status }
      );
    }

    const results = await response.json();

    // Return the results from the backend
    return NextResponse.json(results);
  } catch (error) {
    console.error('Analysis error:', error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'Failed to analyze documents',
      },
      { status: 500 }
    );
  }
}
