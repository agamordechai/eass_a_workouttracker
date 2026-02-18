# Workout Tracker Frontend (React)

A modern React frontend for the Workout Tracker API, converted from Streamlit.

## Features

- **Dashboard Overview**: View metrics like total exercises, sets, volume, and weighted exercises
- **Exercise List**: Browse all exercises with filtering (all/weighted/bodyweight) and search
- **Create Exercise**: Add new exercises with name, sets, reps, and optional weight
- **Edit Exercise**: Update existing exercises via a modal dialog
- **Delete Exercise**: Remove exercises with confirmation
- **Auto-refresh**: Data automatically refreshes every 30 seconds

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn
- The FastAPI backend running on localhost:8000

### Getting Started

```bash
# Install dependencies
npm install

# Start development server (with API proxy to localhost:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The development server runs on `http://localhost:3000` and proxies API requests to the backend.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Base URL for API requests | `/api` (proxied) |

## Docker

### Building the Image

```bash
docker build -t grindlogger-frontend .
```

### Running with Docker Compose

From the project root:

```bash
docker compose up --build
```

This starts:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- React frontend on port 3000

## Project Structure

```
react-app/
├── src/
│   ├── api/
│   │   └── client.ts       # API client (matches Python client.py)
│   ├── components/
│   │   ├── Metrics.tsx           # Summary metrics display
│   │   ├── ExerciseList.tsx      # Exercise table with filters
│   │   ├── CreateExerciseForm.tsx # New exercise form
│   │   ├── EditExerciseModal.tsx  # Edit exercise modal
│   │   └── index.ts              # Component exports
│   ├── types/
│   │   └── exercise.ts     # TypeScript type definitions
│   ├── App.tsx             # Main application component
│   ├── App.css             # Application styles
│   ├── main.tsx            # React entry point
│   └── vite-env.d.ts       # Vite type declarations
├── public/                 # Static assets
├── Dockerfile              # Multi-stage Docker build
├── nginx.conf              # Nginx configuration for production
├── package.json            # npm dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite configuration with API proxy
```

## Comparison with Streamlit Version

| Feature | Streamlit | React |
|---------|-----------|-------|
| Language | Python | TypeScript |
| Framework | Streamlit | React + Vite |
| Styling | Built-in | Custom CSS |
| State Management | st.session_state | React useState |
| Data Fetching | httpx + caching | axios |
| Build Output | Python app | Static files |
| Production Server | Streamlit | Nginx |

