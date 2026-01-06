import React, { useEffect, useRef } from 'react'

type Props = {
  title?: React.ReactNode
  onClose: () => void
  children: React.ReactNode
  contentClassName?: string
}

function getFocusableElements(el?: HTMLElement | null) {
  if (!el) return [] as HTMLElement[]
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

export default function Modal({ title, onClose, children, contentClassName }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    previouslyFocused.current = document.activeElement as HTMLElement | null

    // prevent background scrolling while modal is open
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

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
      // restore body scroll
      document.body.style.overflow = prevOverflow
      // restore focus
      try {
        previouslyFocused.current?.focus()
      } catch (err) {
        // ignore
      }
    }
  }, [onClose])

  const baseInner = 'rounded-xl shadow-2xl p-6 w-[min(720px,95%)] z-10 max-h-[80vh] overflow-y-auto'
  const innerClass = `${contentClassName ? contentClassName : 'bg-white'} ${baseInner}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden />
      <div ref={containerRef} role="dialog" aria-modal="true" className={innerClass}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            {title && <div className="text-2xl font-bold">{title}</div>}
          </div>
          <button
            className="btn"
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              boxShadow: 'none',
              padding: '6px 10px',
              fontSize: 13,
              lineHeight: '18px',
              borderRadius: 6,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#e6e6e6',
              border: 'none',
              color: '#6b7280', /* muted gray */
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M6 6L18 18M6 18L18 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <div style={{ marginTop: 12 }}>{children}</div>
      </div>
    </div >
  )
}
