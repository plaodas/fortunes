import React, { useEffect, useState } from 'react'

// Stable fallback used for server-render and initial client render
export const defaultTZ = 'Asia/Tokyo'

const fallbackTimeZones = [
  'America/Los_Angeles',
  'Asia/Hong_Kong',
  'Asia/Shanghai',
  'Asia/Taipei',
  'Asia/Tokyo',
  'Europe/London',
  'UTC',
]

export default function TimeZoneSelector({ birthTz, setBirthTz }: { birthTz: string; setBirthTz: React.Dispatch<React.SetStateAction<string>> }) {
  const [timeZoneOptions, setTimeZoneOptions] = useState<string[]>(() => fallbackTimeZones)

  useEffect(() => {
    if (typeof Intl !== 'undefined' && typeof (Intl as any).supportedValuesOf === 'function') {
      try {
        const vals = (Intl as any).supportedValuesOf('timeZone')
        if (Array.isArray(vals) && vals.length > 0) setTimeZoneOptions(vals)
      } catch (e) {
        // ignore and keep fallback
      }
    }
  }, [])

  return (
    <div className="form-row">
      <label htmlFor="birth-tz">タイムゾーン</label>
      <select
        id="birth-tz"
        className="input"
        value={birthTz}
        onChange={(e) => setBirthTz(e.target.value)}
        required
      >
        {timeZoneOptions.map((tz) => (
          <option key={tz} value={tz}>{tz}</option>
        ))}
      </select>
    </div>
  )
}

