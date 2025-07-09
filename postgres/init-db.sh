#!/bin/bash
set -e

# PostgreSQL initialization script for Docker environment
echo "🔧 Initializing PostgreSQL with custom configuration..."

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 2
done

echo "✅ PostgreSQL is ready, applying custom configuration..."

# Copy custom configuration files to data directory
if [ -f /etc/postgresql/pg_hba.conf ]; then
    echo "📋 Copying custom pg_hba.conf..."
    cp /etc/postgresql/pg_hba.conf "$PGDATA/pg_hba.conf"
    chown postgres:postgres "$PGDATA/pg_hba.conf"
    chmod 600 "$PGDATA/pg_hba.conf"
fi

if [ -f /etc/postgresql/postgresql.conf ]; then
    echo "📋 Copying custom postgresql.conf..."
    cp /etc/postgresql/postgresql.conf "$PGDATA/postgresql.conf"
    chown postgres:postgres "$PGDATA/postgresql.conf"
    chmod 600 "$PGDATA/postgresql.conf"
fi

echo "🔄 Reloading PostgreSQL configuration..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();"

echo "✅ PostgreSQL configuration applied successfully!"

# Create any additional databases or users if needed
echo "👤 Setting up auction database and user..."

# The main database and user should already be created by the environment variables
# but let's make sure they exist and have the right permissions
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    -- Ensure the auction_user has all necessary privileges
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};

    -- Create any additional schemas if needed
    -- (This is where you could add more setup if required)

    -- Confirm the setup
    SELECT 'Database setup completed successfully!' as status;
EOSQL

echo "🎉 Database initialization completed!"
