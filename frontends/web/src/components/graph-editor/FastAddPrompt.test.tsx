/**
 * FastAddPrompt Component Tests
 * Tests for the floating fast-add form that collects the title.
 * Creator is automatically set to the logged-in user.
 *
 * **Validates: Requirements 4.7**
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FastAddPrompt } from './FastAddPrompt';

const defaultProps = {
  position: { x: 100, y: 200 },
  onSubmit: vi.fn(),
  onCancel: vi.fn(),
};

describe('FastAddPrompt', () => {
  it('renders the floating form with title input', () => {
    render(<FastAddPrompt {...defaultProps} />);

    expect(screen.getByTestId('fast-add-prompt')).toBeDefined();
    expect(screen.getByLabelText(/title/i)).toBeDefined();
    expect(screen.getByTestId('fast-add-submit-btn')).toBeDefined();
    expect(screen.getByTestId('fast-add-cancel-btn')).toBeDefined();
  });

  it('positions the form at the provided coordinates', () => {
    render(<FastAddPrompt {...defaultProps} />);

    const prompt = screen.getByTestId('fast-add-prompt');
    expect(prompt.style.left).toBe('100px');
    expect(prompt.style.top).toBe('200px');
  });

  it('auto-focuses the title input on open', () => {
    render(<FastAddPrompt {...defaultProps} />);

    const titleInput = screen.getByTestId('fast-add-title-input');
    expect(document.activeElement).toBe(titleInput);
  });

  it('disables submit when title is empty', () => {
    render(<FastAddPrompt {...defaultProps} />);
    expect(screen.getByTestId('fast-add-submit-btn')).toBeDisabled();
  });

  it('disables submit when title is whitespace-only', async () => {
    render(<FastAddPrompt {...defaultProps} />);

    const user = userEvent.setup();
    await user.type(screen.getByTestId('fast-add-title-input'), '   ');

    expect(screen.getByTestId('fast-add-submit-btn')).toBeDisabled();
  });

  it('enables submit when title has a non-empty value', async () => {
    render(<FastAddPrompt {...defaultProps} />);

    const user = userEvent.setup();
    await user.type(screen.getByTestId('fast-add-title-input'), 'My Mind');

    expect(screen.getByTestId('fast-add-submit-btn')).not.toBeDisabled();
  });

  it('calls onSubmit with trimmed title on form submit', async () => {
    const onSubmit = vi.fn();
    render(<FastAddPrompt {...defaultProps} onSubmit={onSubmit} />);

    const user = userEvent.setup();
    await user.type(screen.getByTestId('fast-add-title-input'), '  My Mind  ');
    await user.click(screen.getByTestId('fast-add-submit-btn'));

    expect(onSubmit).toHaveBeenCalledWith({ title: 'My Mind' });
  });

  it('calls onCancel when Cancel button is clicked', async () => {
    const onCancel = vi.fn();
    render(<FastAddPrompt {...defaultProps} onCancel={onCancel} />);

    const user = userEvent.setup();
    await user.click(screen.getByTestId('fast-add-cancel-btn'));

    expect(onCancel).toHaveBeenCalled();
  });

  it('calls onCancel when Escape key is pressed', () => {
    const onCancel = vi.fn();
    render(<FastAddPrompt {...defaultProps} onCancel={onCancel} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onCancel).toHaveBeenCalled();
  });

  it('calls onCancel when backdrop is clicked', async () => {
    const onCancel = vi.fn();
    render(<FastAddPrompt {...defaultProps} onCancel={onCancel} />);

    const user = userEvent.setup();
    await user.click(screen.getByTestId('fast-add-prompt-backdrop'));

    expect(onCancel).toHaveBeenCalled();
  });

  it('does not call onSubmit when form is submitted with empty fields', async () => {
    const onSubmit = vi.fn();
    render(<FastAddPrompt {...defaultProps} onSubmit={onSubmit} />);

    fireEvent.submit(screen.getByTestId('fast-add-submit-btn').closest('form')!);

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('has proper dialog role and aria-label', () => {
    render(<FastAddPrompt {...defaultProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeDefined();
    expect(dialog.getAttribute('aria-label')).toBe('Fast add new mind');
  });
});
