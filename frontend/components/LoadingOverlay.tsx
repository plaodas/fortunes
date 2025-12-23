import React from 'react'

type Props = {
    message?: string
}

export default function LoadingOverlay({ message = '暇そうな占い師を探してます。\n連れてくるまで数分かかります。' }: Props) {
    return (
        <div
            role="status"
            aria-live="polite"
            style={{
                position: 'fixed',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(0,0,0,0.35)',
                zIndex: 9999,
            }}
        >
            <div
                style={{
                    background: 'white',
                    padding: 20,
                    borderRadius: 10,
                    display: 'flex',
                    gap: 12,
                    alignItems: 'center',
                    boxShadow: '0 6px 18px rgba(0,0,0,0.2)',
                    maxWidth: '90%',
                }}
            >
                <svg width="44" height="44" viewBox="0 0 24 24" aria-hidden="true">
                    <g fill="none" strokeWidth="2" stroke="currentColor">
                        <circle cx="12" cy="12" r="10" strokeOpacity="0.15" />
                        <path d="M22 12a10 10 0 0 0-10-10" strokeLinecap="round">
                            <animateTransform
                                attributeName="transform"
                                type="rotate"
                                from="0 12 12"
                                to="360 12 12"
                                dur="1s"
                                repeatCount="indefinite"
                            />
                        </path>
                    </g>
                </svg>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <strong style={{ fontSize: 16 }}>{message}</strong>
                    <span style={{ fontSize: 12, color: '#666', marginTop: 6 }}>処理が完了しましたら自動で表示します</span>
                </div>
            </div>
        </div>
    )
}
