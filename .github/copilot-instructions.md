# Copilot Instructions for Puckwise

## Project Overview
Puckwise is a fantasy hockey analytics platform designed to assist users in making data-driven decisions for drafting and trading players. The application leverages historical data, team performance, injuries, and advanced statistics to predict player performance throughout the season.

## Architecture Overview
- **Backend:** Built with Go (1.22+) using the Chi router for API management.
- **Database:** PostgreSQL 15+ with TimescaleDB for time-series data management.
- **ETL/ML:** Python (3.11+) for data extraction, transformation, and machine learning using libraries like pandas, scikit-learn, and XGBoost.
- **Frontend:** React (18+) with Vite, TypeScript, and Tailwind for a responsive user interface.

### Key Components
- **API:** Handles requests for player data, projections, and analytics.
- **Database:** Stores player statistics, historical data, and projections.
- **ETL Processes:** Scripts for data extraction and transformation, including daily updates and initial data loads.

## Developer Workflows
### Building the Project
- **Go Migration Tool:** Use the following command to install the migration tool:
  ```bash
  go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest
  ```
- **Docker Compose:** Run the application using Docker Compose to manage services and dependencies.

### Testing
- **Unit Tests:** Use Go's built-in testing framework. Ensure to categorize tests using build tags to separate unit tests from integration tests.
- **Race Detector:** Always run tests with the `-race` flag to catch data races during development.

### Debugging
- Use logging extensively throughout the application to trace issues. For Go, utilize the `log` package, and for Python, use the `logging` module.

## Project Conventions
- **Code Structure:** Follow standard Go conventions for structuring packages and files. Python modules should be organized by functionality (e.g., `extract`, `load`, `transform`).
- **Naming Conventions:** Use camelCase for Go variables and functions, and snake_case for Python variables and functions.

## Integration Points
- **NHL API:** The primary data source for player statistics and game logs. Ensure to handle API rate limits and errors gracefully.
- **Database Migrations:** Use the migration tool to manage database schema changes effectively.

## External Dependencies
- **PostgreSQL:** Ensure the database is set up with the TimescaleDB extension for time-series data.
- **Python Libraries:** Install required libraries listed in `requirements.txt` for ETL and ML processes.

## Conclusion
This document serves as a guide for AI coding agents to navigate and understand the Puckwise codebase effectively. For further details, refer to the README.md and CLAUDE.md files for project context and additional instructions.