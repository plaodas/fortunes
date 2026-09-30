export const SHICHEN = [
    { branch: '子', range: '23時〜0時', hour: 0 },
    { branch: '丑', range: '1時〜2時', hour: 1 },
    { branch: '寅', range: '3時〜4時', hour: 3 },
    { branch: '卯', range: '5時〜6時', hour: 5 },
    { branch: '辰', range: '7時〜8時', hour: 7 },
    { branch: '巳', range: '9時〜10時', hour: 9 },
    { branch: '午', range: '11時〜12時', hour: 11 },
    { branch: '未', range: '13時〜14時', hour: 13 },
    { branch: '申', range: '15時〜16時', hour: 15 },
    { branch: '酉', range: '17時〜18時', hour: 17 },
    { branch: '戌', range: '19時〜20時', hour: 19 },
    { branch: '亥', range: '21時〜22時', hour: 21 },
] as const

export function shichenIndex(hour: number): number {
    return Math.floor((hour + 1) / 2) % 12
}

export function shichenLabel(hour: number): string {
    const item = SHICHEN[shichenIndex(hour)]
    return `${item.branch}（${item.range}）`
}

export function birthCaption(birthDate: string, hour: number, birthTz: string): string {
    const place = birthTz === 'Asia/Tokyo' ? '' : ` (${birthTz})`
    return `${birthDate} · ${shichenLabel(hour)}${place} 生まれ`
}

export function startAgeMonths(start: string): number | null {
    const matched = /^(\d+)歳(?:(\d+)ヶ月)?/.exec(start)
    if (!matched) return null
    return Number(matched[1]) * 12 + Number(matched[2] ?? 0)
}

export function ageMonths(birthDate: string, today: Date): number {
    const birth = new Date(`${birthDate}T00:00:00`)
    let months = (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth())
    if (today.getDate() < birth.getDate()) months -= 1
    return Math.max(0, months)
}

export function currentDaiunIndex(rows: { start: string }[], birthDate: string, today: Date = new Date()): number {
    const months = ageMonths(birthDate, today)
    let current = -1
    rows.forEach((row, index) => {
        const start = startAgeMonths(row.start)
        if (start !== null && months >= start) current = index
    })
    return current
}
