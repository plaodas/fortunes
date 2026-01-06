import React from 'react'
import Modal from './Modal'

type Props = {
    open: boolean
    onClose: () => void
    title?: React.ReactNode
    children?: React.ReactNode
}

export default function AuthModal({ open, onClose, title, children }: Props) {
    if (!open) return null

    // Use Modal for accessibility/focus trap but apply the `hero` content class
    return (
        <Modal title={title} onClose={onClose} contentClassName="">
            {children}
        </Modal>
    )
}
