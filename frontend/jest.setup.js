// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock environment variables for tests
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_API_V1_PREFIX = '/api/v1'
