import { SHICHEN, currentDaiunIndex, shichenIndex, shichenLabel } from './readingDisplay'

test('時辰は柱の境界に対応する', () => {
    expect(shichenIndex(23)).toBe(0)
    expect(shichenIndex(0)).toBe(0)
    expect(shichenIndex(1)).toBe(1)
    expect(shichenIndex(2)).toBe(1)
    expect(shichenIndex(14)).toBe(7)
    expect(SHICHEN[0].hour).toBe(0)
    expect(SHICHEN[7].hour).toBe(13)
    expect(shichenLabel(14)).toBe('未（13時〜14時）')
})

test('開始済みの大運のうち最後の行を選ぶ', () => {
    const rows = [{ start: '3歳4ヶ月' }, { start: '13歳4ヶ月' }, { start: '23歳4ヶ月' }]
    const today = new Date(2008, 0, 1)
    expect(currentDaiunIndex(rows, '1990-01-01', today)).toBe(1)
})
