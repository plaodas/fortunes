import { useState } from "react";

export default function LoginPage(): JSX.Element {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setMessage(null);

        const form = new FormData();
        form.append("username", username);
        form.append("password", password);

        try {
            const res = await fetch('/api/v1/auth/login', {
                method: "POST",
                body: form,
                credentials: "include",
            });

            if (!res.ok) {
                setMessage(`Login failed: ${res.status}`);
                return;
            }

            setMessage("Login succeeded — calling protected endpoint...");

            // Read csrf_token cookie (double-submit) and call protected endpoint
            const cookies = (document.cookie || "").split(";").map((c) => c.trim());
            const csrfCookie = cookies.find((c) => c.startsWith("csrf_token="));
            const csrfValue = csrfCookie ? decodeURIComponent(csrfCookie.split("=")[1]) : null;

            const prot = await fetch('/api/v1/auth/me', {
                method: "GET",
                credentials: "include",
                headers: csrfValue ? { "x-csrf-token": csrfValue } : {},
            });

            if (!prot.ok) {
                setMessage(`Protected call failed: ${prot.status}`);
                return;
            }

            const data = await prot.json();
            setMessage("Protected call succeeded: " + JSON.stringify(data));
        } catch (err) {
            setMessage("Network error");
        }
    }

    return (
        <div style={{ padding: 24, maxWidth: 420, margin: "0 auto" }}>
            <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12 }}>Login</h1>
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
                <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" type="password" />
                <button type="submit">Login</button>
            </form>
            {message && <p style={{ marginTop: 16 }}>{message}</p>}
        </div>
    );
}
