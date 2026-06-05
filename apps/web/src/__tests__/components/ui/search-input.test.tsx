import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchInput } from '@/components/ui/search-input'

test('renders with placeholder', () => {
  render(<SearchInput value="" onChange={() => {}} placeholder="Find something" />)
  expect(screen.getByPlaceholderText('Find something')).toBeInTheDocument()
})

test('shows clear button when value is present', () => {
  render(<SearchInput value="hello" onChange={() => {}} />)
  expect(screen.getByLabelText('Clear search')).toBeInTheDocument()
})

test('hides clear button when value is empty', () => {
  render(<SearchInput value="" onChange={() => {}} />)
  expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument()
})

test('calls onChange after typing', async () => {
  const user = userEvent.setup()
  const onChange = vi.fn()
  render(<SearchInput value="" onChange={onChange} debounceMs={0} />)
  await user.type(screen.getByRole('searchbox'), 'abc')
  expect(onChange).toHaveBeenCalled()
})
