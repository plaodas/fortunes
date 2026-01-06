import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PROTECTED_ROUTE_PREFIXES = ['/profile', '/settings', '/analysis']

function isProtectedPath(pathname: string) {
    return PROTECTED_ROUTE_PREFIXES.some((p) => pathname.startsWith(p))
}

function getAccessToken(req: NextRequest): string | undefined {
    const raw = req.cookies.get('access_token')
    if (!raw) return undefined
    return typeof raw === 'object' ? raw.value : raw
}

export function middleware(req: NextRequest) {
    const { pathname } = req.nextUrl

    // Debug logging to help trace middleware behavior in dev/containers
    try {
        console.log(`[middleware] url=${req.url} pathname=${pathname}`)
        const cookieRaw = req.cookies.get('access_token')
        const hasCookie = !!cookieRaw && (typeof cookieRaw === 'object' ? !!cookieRaw.value : !!cookieRaw)
        console.log(`[middleware] access_token cookie present=${hasCookie}`)
        console.log(`[middleware] isProtectedPath=${isProtectedPath(pathname)}`)
    } catch (e) {
        // logging should never break middleware behavior
    }

    if (!isProtectedPath(pathname)) {
        console.log('[middleware] route not protected — allow')
        return NextResponse.next()
    }

    const token = getAccessToken(req)
    if (token) {
        console.log('[middleware] token present — allow')
        return NextResponse.next()
    }

    const loginUrl = new URL('/login', req.url)
    // preserve original destination for optional post-login redirect
    loginUrl.searchParams.set('next', pathname)
    console.log(`[middleware] no token — redirecting to ${loginUrl.href}`)
    return NextResponse.redirect(loginUrl)
}

export const config = {
    // Next.js requires `config.matcher` to be a static array literal
    matcher: ['/profile', '/profile/:path*', '/settings', '/settings/:path*', '/analysis', '/analysis/:path*'],
}
