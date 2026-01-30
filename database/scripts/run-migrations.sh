#!/bin/bash
set -e

# Default values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-puckwise}"
DB_PASSWORD="${DB_PASSWORD:-puckwise_dev}"
DB_NAME="${DB_NAME:-hockey_analytics}"
MIGRATIONS_PATH="${MIGRATIONS_PATH:-./database/migrations}"

# Build connection string
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=disable"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if migrate is installed
if ! command -v migrate &> /dev/null; then
    echo_error "golang-migrate is not installed."
    echo "Install with:"
    echo "  brew install golang-migrate  (macOS)"
    echo "  go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest  (Go)"
    echo "  scoop install migrate  (Windows)"
    exit 1
fi

# Parse command line arguments
COMMAND="${1:-up}"
STEPS="${2:-}"

case "$COMMAND" in
    up)
        echo_info "Running migrations UP..."
        if [ -n "$STEPS" ]; then
            migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" up "$STEPS"
        else
            migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" up
        fi
        echo_info "Migrations completed successfully!"
        ;;
    down)
        if [ -z "$STEPS" ]; then
            echo_warn "Rolling back ALL migrations. Are you sure? (y/N)"
            read -r confirm
            if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
                echo "Aborted."
                exit 0
            fi
            STEPS="all"
        fi
        echo_info "Running migrations DOWN ($STEPS)..."
        if [ "$STEPS" = "all" ]; then
            migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" down -all
        else
            migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" down "$STEPS"
        fi
        echo_info "Rollback completed!"
        ;;
    force)
        if [ -z "$STEPS" ]; then
            echo_error "Version number required for force command"
            exit 1
        fi
        echo_warn "Forcing migration version to $STEPS..."
        migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" force "$STEPS"
        echo_info "Version forced to $STEPS"
        ;;
    version)
        echo_info "Current migration version:"
        migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" version
        ;;
    create)
        if [ -z "$STEPS" ]; then
            echo_error "Migration name required"
            echo "Usage: $0 create <migration_name>"
            exit 1
        fi
        echo_info "Creating new migration: $STEPS"
        migrate create -ext sql -dir "$MIGRATIONS_PATH" -seq "$STEPS"
        echo_info "Migration files created!"
        ;;
    seed)
        echo_info "Running seed files..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f ./database/seeds/seed_teams.sql
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f ./database/seeds/seed_seasons.sql
        echo_info "Seed data loaded successfully!"
        ;;
    reset)
        echo_warn "This will DROP all tables and re-run migrations. Are you sure? (y/N)"
        read -r confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "Aborted."
            exit 0
        fi
        echo_info "Resetting database..."
        migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" drop -f
        migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" up
        echo_info "Database reset complete!"
        ;;
    status)
        echo_info "Database connection info:"
        echo "  Host: $DB_HOST"
        echo "  Port: $DB_PORT"
        echo "  Database: $DB_NAME"
        echo "  User: $DB_USER"
        echo ""
        echo_info "Migration version:"
        migrate -path "$MIGRATIONS_PATH" -database "$DATABASE_URL" version
        ;;
    *)
        echo "Usage: $0 {up|down|force|version|create|seed|reset|status} [steps/name/version]"
        echo ""
        echo "Commands:"
        echo "  up [N]        Run all (or N) migrations up"
        echo "  down [N]      Roll back all (or N) migrations"
        echo "  force V       Force set migration version (for fixing dirty state)"
        echo "  version       Show current migration version"
        echo "  create NAME   Create a new migration"
        echo "  seed          Run seed files (teams, seasons)"
        echo "  reset         Drop all tables and re-run migrations"
        echo "  status        Show database connection info and version"
        exit 1
        ;;
esac
