import { describe, it, expect } from 'vitest'
import {
  getScoreColor,
  getScoreBgColor,
  getScoreLabel,
  getScoreBadgeColor,
  formatScore,
  formatTime,
  truncateText,
  getSeniorityColor,
} from '../utils/helpers'

describe('helpers', () => {
  describe('getScoreColor', () => {
    it('returns emerald for 90+', () => {
      expect(getScoreColor(95)).toBe('text-emerald-600')
      expect(getScoreColor(90)).toBe('text-emerald-600')
    })
    it('returns blue for 80-89', () => {
      expect(getScoreColor(85)).toBe('text-blue-600')
      expect(getScoreColor(80)).toBe('text-blue-600')
    })
    it('returns amber for 70-79', () => {
      expect(getScoreColor(75)).toBe('text-amber-600')
      expect(getScoreColor(70)).toBe('text-amber-600')
    })
    it('returns gray for below 70', () => {
      expect(getScoreColor(60)).toBe('text-gray-500')
      expect(getScoreColor(0)).toBe('text-gray-500')
    })
  })

  describe('getScoreLabel', () => {
    it('returns Excellent for 90+', () => {
      expect(getScoreLabel(95)).toBe('Excellent')
    })
    it('returns Strong for 80-89', () => {
      expect(getScoreLabel(85)).toBe('Strong')
    })
    it('returns Good for 70-79', () => {
      expect(getScoreLabel(75)).toBe('Good')
    })
    it('returns Average for below 70', () => {
      expect(getScoreLabel(60)).toBe('Average')
    })
  })

  describe('formatScore', () => {
    it('formats to 1 decimal', () => {
      expect(formatScore(92.5)).toBe('92.5')
      expect(formatScore(80)).toBe('80.0')
    })
  })

  describe('formatTime', () => {
    it('formats ms correctly', () => {
      expect(formatTime(500)).toBe('500ms')
      expect(formatTime(1500)).toBe('1.5s')
    })
  })

  describe('truncateText', () => {
    it('truncates long text', () => {
      expect(truncateText('hello world', 5)).toBe('hello...')
    })
    it('keeps short text', () => {
      expect(truncateText('hi', 5)).toBe('hi')
    })
  })

  describe('getSeniorityColor', () => {
    it('returns correct colors', () => {
      expect(getSeniorityColor('Senior')).toContain('blue')
      expect(getSeniorityColor('Junior')).toContain('orange')
      expect(getSeniorityColor('Mid')).toContain('green')
      expect(getSeniorityColor('Executive')).toContain('purple')
    })
  })
})
