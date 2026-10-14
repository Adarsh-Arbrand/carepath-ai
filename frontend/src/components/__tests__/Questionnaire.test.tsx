import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Questionnaire } from '../Questionnaire';
import type { SymptomRequest } from '../../types';

describe('Questionnaire', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders first step (age group selection)', () => {
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);
    expect(screen.getByText('Age Group')).toBeInTheDocument();
    expect(screen.getByText('Infant (0-2 years)')).toBeInTheDocument();
    expect(screen.getByText('Adult (18-64 years)')).toBeInTheDocument();
  });

  it('validates age group selection', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    // Age group is pre-selected to '18-64', so continue button should be enabled
    const continueButton = screen.getByText('Continue');
    expect(continueButton).not.toBeDisabled();

    // Select a different age group to confirm interaction works
    await user.click(screen.getByRole('button', { name: /Child \(3-12 years\)/i }));
    expect(continueButton).not.toBeDisabled();
  });

  it('navigates through steps', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    // Step 1: Select age group
    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));

    // Step 2: Main symptom
    expect(screen.getByText('Main Symptom')).toBeInTheDocument();
    const symptomInput = screen.getByLabelText('Main symptom');
    await user.type(symptomInput, 'headache');
    await user.click(screen.getByText('Continue'));

    // Step 3: Duration and onset
    expect(screen.getByText('Duration & Onset')).toBeInTheDocument();
  });

  it('validates main symptom input', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    // Step 1
    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));

    // Step 2 - try to continue without input
    const continueButton = screen.getByText('Continue');
    expect(continueButton).toBeDisabled();

    const symptomInput = screen.getByLabelText('Main symptom');
    await user.type(symptomInput, 'headache');
    expect(continueButton).not.toBeDisabled();
  });

  it('adds and removes associated symptoms', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    // Navigate to step 5
    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));
    await user.type(screen.getByLabelText('Main symptom'), 'headache');
    await user.click(screen.getByText('Continue'));
    await user.type(screen.getByLabelText('Duration of symptoms'), '2 hours');
    await user.type(screen.getByLabelText('How symptoms started'), 'gradual');
    await user.click(screen.getByText('Continue'));
    await user.click(screen.getByRole('button', { name: /Moderate/i }));
    await user.click(screen.getByText('Continue'));

    // Add associated symptom
    const input = screen.getByLabelText('Associated symptom');
    await user.type(input, 'nausea');
    await user.click(screen.getByText('Add'));

    expect(screen.getByText('nausea')).toBeInTheDocument();

    // Remove associated symptom
    await user.click(screen.getByText('Remove'));
    expect(screen.queryByText('nausea')).not.toBeInTheDocument();
  });

  it('submits form with all data', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    // Step 1
    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));

    // Step 2
    await user.type(screen.getByLabelText('Main symptom'), 'headache');
    await user.click(screen.getByText('Continue'));

    // Step 3
    await user.type(screen.getByLabelText('Duration of symptoms'), '2 hours');
    await user.type(screen.getByLabelText('How symptoms started'), 'gradual');
    await user.click(screen.getByText('Continue'));

    // Step 4
    await user.click(screen.getByRole('button', { name: /Moderate/i }));
    await user.click(screen.getByText('Continue'));

    // Step 5
    await user.click(screen.getByText('Continue'));

    // Step 6
    await user.click(screen.getByText('Get Assessment'));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });

    const submittedData = mockOnSubmit.mock.calls[0][0] as SymptomRequest;
    expect(submittedData.age_group).toBe('18-64');
    expect(submittedData.main_symptom).toBe('headache');
    expect(submittedData.duration).toBe('2 hours');
    expect(submittedData.onset).toBe('gradual');
    expect(submittedData.severity).toBe('moderate');
  });

  it('shows loading state', () => {
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={true} />);
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('displays progress bar', () => {
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);
    expect(screen.getByText('Step 1 of 6')).toBeInTheDocument();
    expect(screen.getByText('17%')).toBeInTheDocument();
  });

  it('back button works', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));

    expect(screen.getByText('Main Symptom')).toBeInTheDocument();

    await user.click(screen.getByText('Back'));
    expect(screen.getByText('Age Group')).toBeInTheDocument();
  });

  it('respects character limits', async () => {
    const user = userEvent.setup();
    render(<Questionnaire onSubmit={mockOnSubmit} isLoading={false} />);

    await user.click(screen.getByRole('button', { name: /Adult \(18-64 years\)/i }));
    await user.click(screen.getByText('Continue'));

    const symptomInput = screen.getByLabelText('Main symptom');
    // Check that maxLength attribute is set
    expect(symptomInput).toHaveAttribute('maxLength', '500');
  });
});
