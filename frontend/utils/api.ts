export type ApiFetchOptions = { redirectOn401?: boolean }

export async function apiFetch(input: RequestInfo, init?: RequestInit, opts?: ApiFetchOptions) {
    // Ensure CSRF header (double-submit) is included for unsafe requests when running in browser.
    const method = (init && init.method) ? init.method.toUpperCase() : 'GET'
    const headers: Record<string, string> = {}
    if (init && init.headers) {
        // copy existing headers (handle Headers instance or plain object)
        if (init.headers instanceof Headers) {
            init.headers.forEach((v, k) => (headers[k] = v))
        } else if (Array.isArray(init.headers)) {
            for (const [k, v] of init.headers as Array<[string, string]>) headers[k] = v
        } else {
            Object.assign(headers, init.headers as Record<string, string>)
        }
    }

    if (typeof window !== 'undefined' && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        const cookies = (document.cookie || '').split(';').map((c) => c.trim())
        const csrfCookie = cookies.find((c) => c.startsWith('csrf_token='))
        const csrfValue = csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null
        if (csrfValue && !headers['x-csrf-token'] && !headers['X-CSRF-Token']) {
            headers['x-csrf-token'] = csrfValue
        }
    }

    const finalInit = { credentials: 'include', ...(init || {}), headers }
    const res = await fetch(input, finalInit)
    const redirectOn401 = opts?.redirectOn401 ?? true
    if (typeof window !== 'undefined' && res.status === 401 && redirectOn401) {
        const next = window.location.pathname || '/'
        window.location.replace(`/login?next=${encodeURIComponent(next)}`)
    }
    return res
}
