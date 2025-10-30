'use client';

import type React from 'react';

import { useState } from 'react';
import { CloudUpload, FileText, X, Loader2, ImageIcon } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

interface UploaderProps {
  handoutFile: File | null;
  questionFile: File | null;
  onHandoutChange: (file: File | null) => void;
  onQuestionChange: (file: File | null) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  isDisabled: boolean;
  useImageMode: boolean;
  onImageModeChange: (checked: boolean) => void;
}

export default function Uploader({
  handoutFile,
  questionFile,
  onHandoutChange,
  onQuestionChange,
  onAnalyze,
  isLoading,
  isDisabled,
  useImageMode,
  onImageModeChange,
}: UploaderProps) {
  const [dragActive, setDragActive] = useState<'handout' | 'question' | null>(
    null
  );

  const handleDrag = (e: React.DragEvent, zone: 'handout' | 'question') => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(zone);
    } else if (e.type === 'dragleave') {
      setDragActive(null);
    }
  };

  const handleDrop = (e: React.DragEvent, zone: 'handout' | 'question') => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(null);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      if (zone === 'handout') {
        onHandoutChange(files[0]);
      } else {
        onQuestionChange(files[0]);
      }
    }
  };

  const handleFileInput = (
    e: React.ChangeEvent<HTMLInputElement>,
    zone: 'handout' | 'question'
  ) => {
    const files = e.target.files;
    if (files && files[0]) {
      if (zone === 'handout') {
        onHandoutChange(files[0]);
      } else {
        onQuestionChange(files[0]);
      }
    }
  };

  const UploadZone = ({
    title,
    file,
    zone,
    onClear,
  }: {
    title: string;
    file: File | null;
    zone: 'handout' | 'question';
    onClear: () => void;
  }) => (
    <label
      onDragEnter={(e) => handleDrag(e, zone)}
      onDragLeave={(e) => handleDrag(e, zone)}
      onDragOver={(e) => handleDrag(e, zone)}
      onDrop={(e) => handleDrop(e, zone)}
      className={`flex-1 border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        dragActive === zone
          ? 'border-blue-500 bg-blue-100'
          : 'border-blue-200 bg-blue-50 hover:bg-blue-100'
      }`}
    >
      <input
        type='file'
        accept='.pdf'
        onChange={(e) => handleFileInput(e, zone)}
        className='hidden'
      />
      {file ? (
        <div className='flex flex-col items-center gap-2'>
          <FileText className='w-8 h-8 text-blue-600' />
          <p className='text-sm font-semibold text-blue-900'>{file.name}</p>
          <button
            onClick={(e) => {
              e.preventDefault();
              onClear();
            }}
            className='text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 mt-2'
          >
            <X className='w-4 h-4' />
            Clear
          </button>
        </div>
      ) : (
        <div className='flex flex-col items-center gap-2'>
          <CloudUpload className='w-8 h-8 text-blue-400' />
          <p className='text-sm font-semibold text-blue-900'>{title}</p>
          <p className='text-xs text-blue-600'>
            Click to upload or drag and drop
          </p>
        </div>
      )}
    </label>
  );

  return (
    <Card className='bg-white rounded-lg shadow-md mb-6 p-6 border border-blue-100'>
      <h2 className='text-xl font-bold text-blue-900 mb-6'>Upload Documents</h2>

      <div className='flex flex-col md:flex-row gap-4 mb-6'>
        <UploadZone
          title='Course Handout (PDF)'
          file={handoutFile}
          zone='handout'
          onClear={() => onHandoutChange(null)}
        />
        <UploadZone
          title='Question Paper (PDF)'
          file={questionFile}
          zone='question'
          onClear={() => onQuestionChange(null)}
        />
      </div>

      {/* Image Mode Checkbox */}
      <div className='mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg'>
        <div className='flex items-start space-x-3'>
          <Checkbox
            id='imageMode'
            checked={useImageMode}
            onCheckedChange={onImageModeChange}
            className='mt-1 bg-white'
          />
          <div className='flex-1'>
            <Label
              htmlFor='imageMode'
              className='text-sm font-semibold text-blue-900 cursor-pointer flex items-center gap-2'
            >
              <ImageIcon className='w-4 h-4' />
              Question paper contains images/graphs/diagrams
            </Label>
            <p className='text-xs text-blue-600 mt-1'>
              Enable this if your question paper includes circuit diagrams,
              graphs, mathematical figures, or other visual elements. Vision
              mode provides detailed descriptions of visual content for better
              topic mapping and cognitive depth analysis.
            </p>
            {useImageMode && (
              <p className='text-xs text-amber-600 mt-2 font-medium'>
                ⚠️ Vision mode takes longer to process and uses more API
                credits.
              </p>
            )}
          </div>
        </div>
      </div>

      <Button
        onClick={onAnalyze}
        disabled={isDisabled || isLoading}
        className={`w-full py-3 font-semibold rounded-lg transition-all ${
          isDisabled || isLoading
            ? 'bg-blue-200 text-blue-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
        }`}
      >
        {isLoading ? (
          <span className='flex items-center justify-center gap-2'>
            <Loader2 className='w-4 h-4 animate-spin' />
            Analyzing...
          </span>
        ) : (
          'Analyze'
        )}
      </Button>
    </Card>
  );
}
