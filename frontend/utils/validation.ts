// Utilities for validating and filtering username input
// Allow only half-width ASCII printable characters (0x21-0x7E), i.e. half-width
// alphanumeric characters and symbols. Space (0x20) and full-width characters are disallowed.
export const USERNAME_ALLOWED_REGEX = /^[\x21-\x7E]*$/

export function filterUsernameInput(s: string): string {
    if (!s) return s
    // Remove any character outside the allowed ASCII printable range
    return s.replace(/[^\x21-\x7E]/g, '')
}

export function isValidUsername(s: string): boolean {
    return USERNAME_ALLOWED_REGEX.test(s) && s.length > 0
}
