import { z } from 'zod';

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:8000'),
  VITE_API_KEY: z.string().min(1, 'VITE_API_KEY is required'),
});

const parseResult = envSchema.safeParse({
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_API_KEY: import.meta.env.VITE_API_KEY,
});

if (!parseResult.success) {
  const formatted = parseResult.error.issues
    .map((issue) => `  ${issue.path.join('.')}: ${issue.message}`)
    .join('\n');
  throw new Error(`Invalid environment variables:\n${formatted}`);
}

const env = parseResult.data;

export const API_BASE_URL = env.VITE_API_BASE_URL;
export const API_KEY = env.VITE_API_KEY;
