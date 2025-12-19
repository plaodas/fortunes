import React, { useEffect, useRef } from 'react'

type Props = {
  title?: React.ReactNode
  onClose: () => void
  children: React.ReactNode
}

function getFocusableElements(el: HTMLElement) {
  const selectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'textarea:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ]
  return Array.from(el.querySelectorAll<HTMLElement>(selectors.join(',')))
}

export default function Modal({ title, onClose, children }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    previouslyFocused.current = document.activeElement as HTMLElement | null

    const container = containerRef.current
    if (!container) return

    // ensure container is focusable if no interactive children
    if (!container.hasAttribute('tabIndex')) container.setAttribute('tabIndex', '-1')

    const focusable = getFocusableElements(container)
    if (focusable.length) {
      focusable[0].focus()
    } else {
      container.focus()
    }

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
        return
      }

      if (e.key === 'Tab') {
        const els = getFocusableElements(container)
        if (els.length === 0) {
          e.preventDefault()
          return
        }
        const currentIndex = els.indexOf(document.activeElement as HTMLElement)
        let nextIndex = 0
        if (e.shiftKey) {
          nextIndex = currentIndex <= 0 ? els.length - 1 : currentIndex - 1
        } else {
          nextIndex = currentIndex === -1 || currentIndex === els.length - 1 ? 0 : currentIndex + 1
        }
        e.preventDefault()
        els[nextIndex].focus()
      }
    }

    document.addEventListener('keydown', onKeyDown, true)

    return () => {
      document.removeEventListener('keydown', onKeyDown, true)
      // restore focus
      try {
        previouslyFocused.current?.focus()
      } catch (err) {
        // ignore
      }
    }
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden />
      <div ref={containerRef} role="dialog" aria-modal="true" className="bg-white rounded-xl shadow-2xl p-6 w-[min(720px,95%)] z-10">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            {title && <div className="text-2xl font-bold">{title}</div>}
          </div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <div style={{ marginTop: 12 }}>{children}</div>
      </div>
    </div>
  )
}
