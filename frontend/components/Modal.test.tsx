import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Modal from './Modal'

describe('Modal', () => {
  test('renders children and closes on Escape', async () => {
    const user = userEvent.setup()
    const onClose = jest.fn()
    render(
      <div>
        <button>outside</button>
        <Modal title="Test" onClose={onClose}>
          <button>first</button>
          <button>second</button>
        </Modal>
      </div>
    )

    // children present
    expect(screen.getByText('first')).toBeInTheDocument()

    // press Escape closes
    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })

  test('focus traps inside modal with Tab and Shift+Tab', async () => {
    const user = userEvent.setup()
    const onClose = jest.fn()
    render(
      <div>
        <button>outside</button>
        <Modal title="Trap" onClose={onClose}>
          <button>one</button>
          <button>two</button>
        </Modal>
      </div>
    )

    const one = screen.getByText('one') as HTMLElement
    const two = screen.getByText('two') as HTMLElement

    // tab cycles: first tab should focus the first focusable inside modal
    await user.tab()
    expect(document.activeElement).toBe(one)
    await user.tab()
    expect(document.activeElement).toBe(two)

    // shift+tab cycles backwards
    await user.keyboard('{Shift>}{Tab}{/Shift}')
    expect(document.activeElement).toBe(one)
  })
})
