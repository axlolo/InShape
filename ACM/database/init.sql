-- In Shape Database Schema
-- This script initializes the database structure for the In Shape fitness tracking app

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strava_user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    profile_picture_url TEXT,
    lifetime_points INTEGER DEFAULT 0,
    member_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    strava_access_token TEXT,
    strava_refresh_token TEXT,
    strava_token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar_url TEXT,
    created_by UUID REFERENCES users(id),
    weekly_challenge VARCHAR(255),
    challenge_end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group memberships table
CREATE TABLE group_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- 'member', 'admin', 'owner'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, group_id)
);

-- Activities/Runs table
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    strava_activity_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    activity_type VARCHAR(50) DEFAULT 'Run',
    distance DECIMAL(10,2), -- in miles
    moving_time INTEGER, -- in seconds
    elapsed_time INTEGER, -- in seconds
    total_elevation_gain DECIMAL(8,2), -- in feet
    average_speed DECIMAL(8,4), -- in mph
    max_speed DECIMAL(8,4), -- in mph
    start_date TIMESTAMP,
    coordinates JSONB, -- GPS coordinates array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shape challenges table
CREATE TABLE shape_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_shape VARCHAR(100) NOT NULL, -- 'rectangle', 'circle', 'triangle', etc.
    svg_path TEXT, -- SVG path for the target shape
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity scores table (for shape matching)
CREATE TABLE activity_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    activity_id UUID REFERENCES activities(id) ON DELETE CASCADE,
    shape_challenge_id UUID REFERENCES shape_challenges(id),
    group_id UUID REFERENCES groups(id),
    score DECIMAL(5,2) NOT NULL, -- percentage score (0-100)
    algorithm_used VARCHAR(100),
    analysis_data JSONB, -- detailed analysis metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_id, shape_challenge_id, group_id)
);

-- Group leaderboards (aggregated scores)
CREATE TABLE group_leaderboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    shape_challenge_id UUID REFERENCES shape_challenges(id),
    best_score DECIMAL(5,2),
    best_activity_id UUID REFERENCES activities(id),
    total_attempts INTEGER DEFAULT 0,
    week_start DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id, shape_challenge_id, week_start)
);

-- Create indexes for better performance
CREATE INDEX idx_users_strava_id ON users(strava_user_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_strava_id ON activities(strava_activity_id);
CREATE INDEX idx_activities_start_date ON activities(start_date);
CREATE INDEX idx_group_memberships_user_id ON group_memberships(user_id);
CREATE INDEX idx_group_memberships_group_id ON group_memberships(group_id);
CREATE INDEX idx_activity_scores_group_id ON activity_scores(group_id);
CREATE INDEX idx_group_leaderboards_group_id ON group_leaderboards(group_id);
CREATE INDEX idx_group_leaderboards_week ON group_leaderboards(week_start);

-- Insert sample shape challenges
INSERT INTO shape_challenges (name, description, target_shape, svg_path) VALUES
('Perfect Rectangle', 'Run a route that forms a perfect rectangle shape', 'rectangle', 'M 10 10 L 90 10 L 90 40 L 10 40 Z'),
('Circle Challenge', 'Create a circular running route', 'circle', 'M 50 10 A 20 20 0 1 1 49.99 10'),
('Triangle Sprint', 'Run a triangular route with three equal sides', 'triangle', 'M 50 10 L 80 50 L 20 50 Z'),
('Star Pattern', 'Create a 5-pointed star with your running route', 'star', 'M 50 10 L 55 25 L 70 25 L 60 35 L 65 50 L 50 40 L 35 50 L 40 35 L 30 25 L 45 25 Z'),
('Diamond Route', 'Run a diamond-shaped route', 'diamond', 'M 50 10 L 70 30 L 50 50 L 30 30 Z'),
('Heart Shape', 'Run a heart-shaped route for the romantic challenge', 'heart', 'M 50 40 C 35 25 10 30 10 50 C 10 65 35 75 50 85 C 65 75 90 65 90 50 C 90 30 65 25 50 40 Z');

-- Insert sample groups
INSERT INTO groups (id, name, description, weekly_challenge, challenge_end_date) VALUES
(uuid_generate_v4(), 'Downtown Runners', 'A community of runners exploring downtown routes and geometric challenges', 'Perfect Rectangle', '2024-09-20'),
(uuid_generate_v4(), 'Shape Masters', 'Elite group focused on achieving perfect geometric running patterns', 'Star Pattern', '2024-09-22'),
(uuid_generate_v4(), 'Weekend Warriors', 'Casual group for weekend running adventures and fun shape challenges', 'Heart Shape', '2024-09-25');

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_group_leaderboards_updated_at BEFORE UPDATE ON group_leaderboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (optional, for specific user access)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inshape_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inshape_user;
