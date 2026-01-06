export async function requireAuth(context: any) {
    const req = context.req
    const cookieHeader = req.headers?.cookie || ''

    function parseCookies(header: string) {
        if (!header) return {}
        return Object.fromEntries(header.split(';').map((c) => {
            const idx = c.indexOf('=')
            if (idx === -1) return [c.trim(), '']
            const k = c.slice(0, idx).trim()
            const v = c.slice(idx + 1).trim()
            try { return [k, decodeURIComponent(v)] } catch (e) { return [k, v] }
        }))
    }

    const cookies = parseCookies(cookieHeader)
    const token = cookies['access_token']
    if (!token) {
        const next = context.resolvedUrl || (context.req && context.req.url) || '/'
        return {
            redirect: {
                destination: `/login?next=${encodeURIComponent(next)}`,
                permanent: false,
            },
        }
    }

    return { props: {} }
}

export default requireAuth
