# Test Planning Helper (TP)

A web application that helps Software QA Engineers plan test scenarios and reduce the number of test cases using various techniques like Design of Experiments (DoE), Fractional Factorial Design, and Pairwise Testing.

## Features

- User authentication via Google Auth
- Creation of Design of Experiments (DoE) assets with custom parameters and values
- Test scenario generation and reduction using techniques:
  - Smaller Fractional Factorial Design
  - Pairwise Testing
- Asset management (view, edit, share, delete)
- Export to Markdown and Excel formats
- Storage management with quotas (100MB per user)

## Architecture

This project is a monorepo containing:

- **Frontend**: Next.js with TypeScript, Tailwind CSS
- **Backend**: Python FastAPI with PyDOE2 and allpairspy
- **Database**: PostgreSQL with JSONB for flexible schema
- **Infrastructure**: Docker for containerization and deployment

## Development

### Prerequisites

- Node.js 18+
- Python 3.10+
- Docker and Docker Compose
- PostgreSQL 15+

### Getting Started

1. Clone the repository
2. Run `docker-compose up -d` to start all services
3. Access the application at http://localhost:3000

## Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- Feature branches: `feature/<feature-name>`
- Bugfix branches: `bugfix/<bug-description>`

## License

[MIT License](LICENSE)