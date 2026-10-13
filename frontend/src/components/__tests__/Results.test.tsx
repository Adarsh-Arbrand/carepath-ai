import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Results } from '../Results';
import { AssessmentResponse } from '../../types';

describe('Results', () => {
  const mockOnReset = vi.fn();

  const emergencyResponse: AssessmentResponse = {
    urgency: 'emergency',
    warning_signs_detected: [
      {
        sign: 'chest pain',
        description: 'Chest pain can indicate heart attack',
        source: 'American Heart Association',
      },
    ],
    reasoning: 'Emergency warning signs detected',
    recommended_next_steps: [
      'Contact emergency services immediately (112)',
      'Do not drive yourself',
    ],
    limitations: [
      'This is not a diagnostic system',
      'Not clinically validated',
    ],
    is_demo_mode: false,
    needs_follow_up: false,
  };

  const routineResponse: AssessmentResponse = {
    urgency: 'routine',
    warning_signs_detected: [],
    reasoning: 'No emergency warning signs detected',
    recommended_next_steps: [
      'Schedule an appointment with a healthcare provider',
      'Monitor symptoms',
    ],
    limitations: [
      'This is not a diagnostic system',
      'Not clinically validated',
    ],
    is_demo_mode: true,
    needs_follow_up: false,
  };

  const followUpResponse: AssessmentResponse = {
    urgency: 'unknown',
    warning_signs_detected: [],
    reasoning: 'Insufficient information',
    recommended_next_steps: [
      'Consult a healthcare provider',
    ],
    limitations: [
      'More information needed',
    ],
    is_demo_mode: true,
    needs_follow_up: true,
    follow_up_question: 'Could you provide more details?',
  };

  beforeEach(() => {
    mockOnReset.mockClear();
  });

  it('renders emergency urgency correctly', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.getByText('EMERGENCY')).toBeInTheDocument();
    expect(screen.getByText('Call emergency services immediately (112 in India)')).toBeInTheDocument();
  });

  it('renders routine urgency correctly', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    expect(screen.getByText('ROUTINE')).toBeInTheDocument();
  });

  it('renders unknown urgency correctly', () => {
    render(<Results response={followUpResponse} onReset={mockOnReset} />);

    expect(screen.getByText('INSUFFICIENT INFORMATION')).toBeInTheDocument();
  });

  it('displays warning signs when present', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Warning Signs Detected')).toBeInTheDocument();
    expect(screen.getAllByText(/chest pain/i)).toHaveLength(2); // Once in sign, once in description
    expect(screen.getByText(/Chest pain can indicate heart attack/i)).toBeInTheDocument();
    expect(screen.getByText(/American Heart Association/i)).toBeInTheDocument();
  });

  it('does not display warning signs section when none detected', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    expect(screen.queryByText('Warning Signs Detected')).not.toBeInTheDocument();
  });

  it('displays reasoning', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Assessment Reasoning')).toBeInTheDocument();
    expect(screen.getByText('Emergency warning signs detected')).toBeInTheDocument();
  });

  it('displays recommended next steps', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Recommended Next Steps')).toBeInTheDocument();
    expect(screen.getByText('Contact emergency services immediately (112)')).toBeInTheDocument();
    expect(screen.getByText('Do not drive yourself')).toBeInTheDocument();
  });

  it('displays limitations', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Important Limitations')).toBeInTheDocument();
    expect(screen.getByText('This is not a diagnostic system')).toBeInTheDocument();
    expect(screen.getByText('Not clinically validated')).toBeInTheDocument();
  });

  it('shows demo mode indicator when in demo mode', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    expect(screen.getByText(/Demo Mode/i)).toBeInTheDocument();
    expect(screen.getByText(/AI explanations are generalized/i)).toBeInTheDocument();
  });

  it('does not show demo mode indicator when not in demo mode', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.queryByText('Demo Mode')).not.toBeInTheDocument();
  });

  it('displays follow-up question when needed', () => {
    render(<Results response={followUpResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Additional Information Needed')).toBeInTheDocument();
    expect(screen.getByText('Could you provide more details?')).toBeInTheDocument();
  });

  it('calls onReset when Start New Assessment is clicked', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    const resetButton = screen.getByText('Start New Assessment');
    fireEvent.click(resetButton);

    expect(mockOnReset).toHaveBeenCalledTimes(1);
  });

  it('has print button', () => {
    render(<Results response={routineResponse} onReset={mockOnReset} />);

    expect(screen.getByText('Print Summary')).toBeInTheDocument();
  });

  it('emergency banner has accessible attributes', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    const banner = screen.getByTestId('urgency-banner');
    expect(banner).toHaveAttribute('role', 'alert');
    expect(banner).toHaveAttribute('aria-live', 'assertive');
  });

  it('displays numbered next steps', () => {
    render(<Results response={emergencyResponse} onReset={mockOnReset} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});
