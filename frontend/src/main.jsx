import { ViteReactSSG } from 'vite-react-ssg'
import './index.css'
import { routes } from './App.jsx'

export const createRoot = ViteReactSSG({ routes });
