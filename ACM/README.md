# In Shape - Fitness Tracking App

A modern web application for tracking fitness progress through shape-based running challenges. Users connect their Strava accounts and compete in groups by running routes that match geometric patterns.

## Features

- **Profile Management**: View personal stats, lifetime points, and group memberships
- **Group Challenges**: Join fitness groups and participate in weekly shape challenges
- **Leaderboards**: Compete with group members and track progress
- **Shape Analysis**: AI-powered analysis of running routes against target geometric shapes
- **Strava Integration**: Seamless connection with Strava for activity tracking

## Tech Stack

### Frontend
- **Next.js 15** with TypeScript
- **Tailwind CSS** for styling
- **Heroicons** for iconography
- Modern React patterns with hooks and server components

### Backend (Planned)
- **Flask** API server
- **PostgreSQL** database
- **Strava API** integration
- **Shape analysis algorithms** (already implemented in Python)

### Database
- **PostgreSQL 15** with UUID primary keys
- Comprehensive schema for users, groups, activities, and leaderboards
- JSONB for flexible coordinate and analysis data storage

## Project Structure

```
├── in-shape-frontend/          # Next.js frontend application
│   ├── src/
│   │   ├── app/               # Next.js app router pages
│   │   │   ├── profile/       # User profile page
│   │   │   ├── groups/        # Groups listing page
│   │   │   └── leaderboard/   # Group leaderboards
│   │   └── components/        # Reusable React components
│   └── package.json
├── ACM/                       # Backend Python modules
│   ├── strava_api.py         # Strava API integration
│   ├── shape_grader.py       # Shape analysis algorithms
│   └── requirements.txt      # Python dependencies
├── database/
│   └── init.sql              # Database schema
└── docker-compose.yml        # PostgreSQL setup
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- Docker (for database)
- Python 3.9+ (for backend)

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd in-shape-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Database Setup

1. Start PostgreSQL with Docker:
   ```bash
   docker compose up -d
   ```

2. The database will be initialized with the schema from `database/init.sql`

3. Connection details:
   - Host: localhost:5432
   - Database: inshape
   - Username: inshape_user
   - Password: inshape_password

### Backend Setup (Python)

1. Navigate to the ACM directory:
   ```bash
   cd ACM
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Color Theme

The app uses a clean white and orange color scheme:
- Primary Orange: `#ff6b35`
- Orange Light: `#ff8c65`
- Orange Dark: `#e55a2b`
- Background: White with light gray accents

## Database Schema

### Core Tables

- **users**: User profiles and Strava integration data
- **groups**: Running groups and weekly challenges
- **group_memberships**: User-group relationships
- **activities**: Strava activity data with GPS coordinates
- **shape_challenges**: Target geometric patterns
- **activity_scores**: Shape matching scores and analysis
- **group_leaderboards**: Aggregated leaderboard data

### Sample Data

The database includes sample shape challenges:
- Perfect Rectangle
- Circle Challenge
- Triangle Sprint
- Star Pattern
- Diamond Route
- Heart Shape