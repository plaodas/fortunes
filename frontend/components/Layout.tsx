import React from 'react'
import Header from './Header'

type Props = {
    children: React.ReactNode
    hero?: React.ReactNode
}

export default function Layout({ children, hero }: Props) {
    return (
        <main className="container">
            <Header />
            {hero}
            {children}
        </main>
    )
}
