# Technical Requirements Document
## HRBot - Telegram HR Automation System

**Version:** 1.0
**Last Updated:** 2026-03-06
**Status:** Active Development

---

## 1. System Overview

### 1.1 Purpose
HRBot is a Telegram-based HR automation system that streamlines recruitment workflows by automatically parsing job applications from Gmail, analyzing resumes using AI, and providing recruiters with structured candidate information through an interactive bot interface.

### 1.2 Scope
- Automated email parsing from multiple Gmail accounts
- AI-powered resume analysis and candidate evaluation
- Role-based access control for recruitment team members
- Application lifecycle management
- Data export capabilities for reporting

### 1.3 Target Users
- **Admins**: System administrators with full access
- **Moderators**: HR specialists managing applications
- **Users**: Limited access, registration pending approval

---

## 2. Functional Requirements

### 2.1 Authentication & Authorization

#### FR-2.1.1 User Registration
- System SHALL automatically create user records on first interaction
- System SHALL assign default USER role to new registrations
- System SHALL persist Telegram user ID, username, first name, and last name

#### FR-2.1.2 Role-Based Access Control
- System SHALL support three role levels: USER, MODERATOR, ADMIN
- System SHALL enforce permission checks at handler level
- System SHALL prevent unauthorized access to protected commands

#### FR-2.1.3 Role Management
- ADMIN users SHALL be able to promote/demote users
- System SHALL maintain audit trail of role changes
- System SHALL support database-level role initialization

### 2.2 Gmail Integration

#### FR-2.2.1 Multi-Account Support
- System SHALL support multiple Gmail accounts simultaneously
- System SHALL maintain separate OAuth tokens per account
- System SHALL allow account-specific sender email filtering

#### FR-2.2.2 OAuth Authentication
- System SHALL implement OAuth 2.0 authorization flow
- System SHALL store refresh tokens securely
- System SHALL automatically refresh expired access tokens
- System SHALL handle token expiration gracefully

#### FR-2.2.3 Email Parsing
- System SHALL poll Gmail accounts at configurable intervals
- System SHALL extract applicant name, email, phone from email content
- System SHALL detect and download resume attachments (.pdf, .docx)
- System SHALL parse cover letters and application messages
- System SHALL associate applications with vacancies based on subject line
- System SHALL create new vacancy records for unrecognized positions

#### FR-2.2.4 Account Management
- ADMIN SHALL be able to add/remove Gmail accounts
- ADMIN SHALL configure sender email filters per account
- System SHALL validate OAuth credentials before activation
- System SHALL display account status and statistics

### 2.3 Resume Processing

#### FR-2.3.1 Document Extraction
- System SHALL extract text from PDF files using PyPDF2
- System SHALL extract text from DOCX files using python-docx
- System SHALL handle malformed or corrupted files gracefully
- System SHALL log extraction failures with error details

#### FR-2.3.2 AI-Powered Analysis
- System SHALL integrate with Google Gemini API
- System SHALL generate structured candidate summaries including:
  - Key strengths and qualifications
  - Technical and soft skills list
  - Years of experience
  - Educational background
  - Risk flags and concerns
  - Suggested interview questions with answers

#### FR-2.3.3 Summary Storage
- System SHALL persist AI-generated summaries in database
- System SHALL link summaries to application records
- System SHALL support summary regeneration

### 2.4 Application Management

#### FR-2.4.1 Application Listing
- System SHALL display applications grouped by vacancy
- System SHALL show unprocessed applications count
- System SHALL support filtering by processing status
- System SHALL paginate results for large datasets

#### FR-2.4.2 Application Details
- System SHALL display complete candidate information
- System SHALL show AI-generated summaries
- System SHALL provide resume download links
- System SHALL display application source (email/Telegram)

#### FR-2.4.3 Status Management
- MODERATOR SHALL be able to mark applications as processed/unprocessed
- System SHALL track processing timestamps
- System SHALL support processing notes and descriptions

#### FR-2.4.4 Application Deletion
- MODERATOR SHALL be able to delete applications
- System SHALL implement soft delete with deleted_at timestamp
- System SHALL exclude deleted records from standard queries

### 2.5 Vacancy Management

#### FR-2.5.1 Vacancy CRUD Operations
- ADMIN SHALL be able to create vacancies manually
- System SHALL auto-create vacancies from email subjects
- ADMIN SHALL be able to edit vacancy details
- ADMIN SHALL be able to delete vacancies (cascade to applications)

#### FR-2.5.2 Vacancy Display
- System SHALL list all active vacancies
- System SHALL show application count per vacancy
- System SHALL display vacancy source (email/manual)

### 2.6 Data Export

#### FR-2.6.1 Excel Export
- MODERATOR SHALL be able to export applications to Excel
- System SHALL include all candidate fields
- System SHALL include AI-generated summaries
- System SHALL support export filtering (all/unprocessed)
- System SHALL generate timestamped filenames

#### FR-2.6.2 Export Format
- Files SHALL be in .xlsx format
- Columns SHALL include: Name, Email, Phone, Vacancy, Status, Skills, Experience, Summary, Interview Questions
- System SHALL handle Unicode characters correctly

### 2.7 User Interface

#### FR-2.7.1 Command Interface
- System SHALL support following commands:
  - `/start` - Initialize bot interaction
  - `/parse_now` - Trigger manual email parsing
  - `/manage_accounts` - Gmail account management
  - `/list_users` - Display user list
  - `/export_all` - Export all applications
  - `/export_unprocessed` - Export unprocessed only

#### FR-2.7.2 Inline Keyboards
- System SHALL use inline keyboards for navigation
- System SHALL support callback query handling
- System SHALL implement hierarchical menu structures
- System SHALL provide cancel/back buttons

#### FR-2.7.3 Message Formatting
- System SHALL format messages using Markdown
- System SHALL display data in structured format
- System SHALL truncate long text with "Show more" buttons
- System SHALL use emojis for visual clarity

---

## 3. Non-Functional Requirements

### 3.1 Performance

#### NFR-3.1.1 Response Time
- Bot commands SHALL respond within 2 seconds
- Email parsing SHALL complete within 30 seconds per account
- AI analysis SHALL complete within 15 seconds per resume
- Database queries SHALL execute within 500ms

#### NFR-3.1.2 Throughput
- System SHALL handle 100 applications per hour
- System SHALL support up to 10 concurrent users
- System SHALL process up to 5 Gmail accounts simultaneously

#### NFR-3.1.3 Resource Usage
- Container SHALL run with maximum 512MB RAM
- Database file SHALL not exceed 1GB for 10,000 applications
- Downloaded resumes SHALL be periodically archived

### 3.2 Reliability

#### NFR-3.2.1 Availability
- System SHALL maintain 95% uptime during business hours
- System SHALL restart automatically after failures
- System SHALL recover from network interruptions

#### NFR-3.2.2 Error Handling
- System SHALL log all exceptions with stack traces
- System SHALL notify admins of critical errors
- System SHALL continue processing after individual failures
- System SHALL implement retry logic for transient errors

#### NFR-3.2.3 Data Integrity
- System SHALL use database transactions for multi-step operations
- System SHALL prevent duplicate application entries
- System SHALL validate data before persistence

### 3.3 Security

#### NFR-3.3.1 Authentication
- System SHALL use OAuth 2.0 for Gmail integration
- System SHALL never store Gmail passwords
- System SHALL rotate OAuth tokens automatically

#### NFR-3.3.2 Authorization
- System SHALL enforce role-based permissions
- System SHALL block unauthorized command execution
- System SHALL log permission violations

#### NFR-3.3.3 Data Protection
- System SHALL store sensitive credentials in environment variables
- System SHALL exclude token files from version control
- System SHALL use HTTPS for all API communications
- System SHALL sanitize user inputs to prevent injection attacks

#### NFR-3.3.4 Privacy
- System SHALL not log PII in debug messages
- System SHALL handle candidate data in compliance with GDPR
- System SHALL support data deletion upon request

### 3.4 Scalability

#### NFR-3.4.1 Horizontal Scaling
- Architecture SHALL support multiple bot instances (future)
- Database SHALL migrate to PostgreSQL for production
- File storage SHALL move to object storage (S3-compatible)

#### NFR-3.4.2 Data Volume
- System SHALL handle up to 50,000 applications
- System SHALL support up to 500 vacancies
- System SHALL manage up to 100 users

### 3.5 Maintainability

#### NFR-3.5.1 Code Quality
- Code SHALL follow PEP 8 style guidelines
- Code SHALL maintain 80%+ test coverage
- Code SHALL use type hints for all functions
- Code SHALL be self-documenting with clear naming

#### NFR-3.5.2 Documentation
- API integrations SHALL be documented
- Database schema SHALL be versioned with migrations
- Configuration options SHALL be documented in .env.example

#### NFR-3.5.3 Logging
- System SHALL implement structured logging with levels: INFO, WARN, ERROR
- Logs SHALL include timestamps, module names, and context
- Logs SHALL rotate daily with 30-day retention

### 3.6 Usability

#### NFR-3.6.1 User Experience
- Bot responses SHALL be clear and concise
- Error messages SHALL provide actionable guidance
- Navigation SHALL require minimum clicks
- Commands SHALL have intuitive names

#### NFR-3.6.2 Internationalization
- System SHALL support UTF-8 encoding
- Messages SHALL be structured for future localization

---

## 4. Technical Architecture

### 4.1 System Components

#### 4.1.1 Bot Layer
- **Framework**: Aiogram 3.10
- **Responsibilities**:
  - Command handling
  - Callback query processing
  - User interaction management
  - Background task scheduling

#### 4.1.2 Service Layer
- **Components**:
  - `GeminiService`: AI resume analysis
  - `ResumeSummaryService`: Summary orchestration
  - `DocumentTextExtractor`: File processing
- **Responsibilities**:
  - Business logic encapsulation
  - External API communication
  - Data transformation

#### 4.1.3 Data Layer
- **ORM**: SQLAlchemy 2.0
- **Driver**: aiosqlite (async)
- **Migrations**: Alembic
- **Responsibilities**:
  - Data persistence
  - Query optimization
  - Schema versioning

#### 4.1.4 Integration Layer
- **Gmail API**: Email retrieval and parsing
- **Gemini API**: AI-powered analysis
- **Telegram Bot API**: User interaction

### 4.2 Architectural Patterns

#### 4.2.1 Service Layer Architecture
- Business logic SHALL be isolated in service classes
- Handlers SHALL delegate to services
- Services SHALL not depend on bot framework

#### 4.2.2 Dependency Injection
- Services SHALL receive dependencies via constructor
- Database sessions SHALL be injected into services
- Configuration SHALL be injected via environment

#### 4.2.3 Middleware Pattern
- Cross-cutting concerns SHALL use middleware
- Role checking SHALL be implemented as middleware
- Error handling SHALL use middleware

#### 4.2.4 Async-First Design
- All I/O operations SHALL use async/await
- Database operations SHALL be asynchronous
- API calls SHALL be asynchronous
- File operations SHALL use aiofiles where applicable

### 4.3 Technology Stack

#### 4.3.1 Runtime
- Python 3.11+
- asyncio event loop

#### 4.3.2 Frameworks & Libraries
- `aiogram 3.10`: Telegram bot framework
- `sqlalchemy 2.0`: ORM and query builder
- `alembic 1.13`: Database migrations
- `pydantic 2.5`: Data validation and settings

#### 4.3.3 External Services
- Telegram Bot API
- Google Gmail API
- Google Gemini API

#### 4.3.4 Development Tools
- Docker & Docker Compose
- Git version control
- Virtual environment (venv)

---

## 5. Data Models & Schema

### 5.1 Core Entities

#### 5.1.1 TelegramUser
```
- id: Integer (PK, autoincrement)
- telegram_id: BigInteger (unique, indexed)
- username: String (nullable)
- first_name: String (nullable)
- last_name: String (nullable)
- role: Enum(USER, MODERATOR, ADMIN)
- created_at: DateTime
- updated_at: DateTime
```

**Relationships:**
- 1:N with GmailAccount (owner)

#### 5.1.2 GmailAccount
```
- id: Integer (PK, autoincrement)
- email: String (unique)
- credentials_path: String
- token_path: String
- added_by_user_id: Integer (FK to TelegramUser)
- is_active: Boolean
- sender_emails: Text (JSON array)
- created_at: DateTime
- updated_at: DateTime
```

**Relationships:**
- N:1 with TelegramUser (added_by)
- 1:N with Vacancy

#### 5.1.3 Vacancy
```
- id: Integer (PK, autoincrement)
- title: String (indexed)
- description: Text (nullable)
- source: Enum(email, telegram)
- gmail_account_id: Integer (FK to GmailAccount, nullable)
- created_at: DateTime
- updated_at: DateTime
```

**Relationships:**
- N:1 with GmailAccount
- 1:N with Application

#### 5.1.4 Application
```
- id: Integer (PK, autoincrement)
- vacancy_id: Integer (FK to Vacancy)
- name: String
- email: String (indexed)
- phone: String (nullable)
- resume_path: String (nullable)
- cover_letter: Text (nullable)
- source: Enum(email, telegram)
- message_id: Integer (nullable)
- summary: Text (nullable)
- skills: Text (JSON array, nullable)
- experience_years: String (nullable)
- education: Text (nullable)
- red_flags: Text (nullable)
- interview_questions: Text (nullable)
- is_processed: Boolean (default=False)
- processing_description: Text (nullable)
- processed_at: DateTime (nullable)
- deleted_at: DateTime (nullable)
- created_at: DateTime
- updated_at: DateTime
```

**Relationships:**
- N:1 with Vacancy

### 5.2 Database Requirements

#### 5.2.1 Indexing Strategy
- Index on `telegram_users.telegram_id` for O(1) user lookup
- Index on `vacancies.title` for vacancy search
- Index on `applications.email` for duplicate detection
- Composite index on `applications.vacancy_id, is_processed`

#### 5.2.2 Migration Management
- All schema changes SHALL use Alembic migrations
- Migrations SHALL be tested in development before production
- Migrations SHALL include rollback scripts
- Migration versions SHALL be sequential and documented

#### 5.2.3 Data Retention
- Deleted applications SHALL be soft-deleted with deleted_at timestamp
- Hard deletion SHALL occur after 90 days (configurable)
- Resume files SHALL be archived after 180 days

---

## 6. External API Integrations

### 6.1 Telegram Bot API

#### 6.1.1 Authentication
- Bot token SHALL be stored in BOT_TOKEN environment variable
- Token SHALL use HTTPS webhook or long-polling

#### 6.1.2 API Usage
- sendMessage for text responses
- sendDocument for file downloads
- editMessageText for dynamic updates
- answerCallbackQuery for inline keyboard interactions

#### 6.1.3 Rate Limits
- Maximum 30 messages per second per chat
- Maximum 20 messages per minute to same group
- Implement exponential backoff on rate limit errors

### 6.2 Google Gmail API

#### 6.2.1 Authentication
- OAuth 2.0 with offline access
- Scopes: `gmail.readonly`
- Credentials file: `credentials.json` (git-ignored)
- Token storage: `gmail_tokens/{email}.json`

#### 6.2.2 API Usage
- `users.messages.list`: Retrieve message IDs
- `users.messages.get`: Fetch message details
- `users.messages.attachments.get`: Download attachments
- Query filters: `from:{sender_email} is:unread`

#### 6.2.3 Error Handling
- Handle 401 Unauthorized (token refresh)
- Handle 403 Forbidden (insufficient permissions)
- Handle 429 Rate Limit (exponential backoff)
- Handle 500 Server Error (retry logic)

#### 6.2.4 Rate Limits
- 250 quota units per second per user
- 1 billion quota units per day
- Message retrieval: 5 quota units per request

### 6.3 Google Gemini API

#### 6.3.1 Authentication
- API key stored in GEMINI_API_KEY environment variable
- Use `google.generativeai` Python SDK

#### 6.3.2 Model Configuration
- Model: `gemini-1.5-flash` or `gemini-1.5-pro`
- Temperature: 0.7
- Max tokens: 2048
- Safety settings: BLOCK_MEDIUM_AND_ABOVE

#### 6.3.3 Prompt Engineering
- Structured prompts for consistent output
- JSON response format with defined schema
- Include resume text and position context
- Request specific fields: summary, skills, experience, red_flags, questions

#### 6.3.4 Error Handling
- Handle 400 Bad Request (malformed prompt)
- Handle 429 Rate Limit (exponential backoff)
- Handle 500 Server Error (retry with fallback model)
- Timeout: 30 seconds per request

#### 6.3.5 Cost Management
- Cache resume text to avoid duplicate analysis
- Use flash model for standard resumes
- Use pro model only for complex resumes
- Monitor monthly token usage

---

## 7. Security Requirements

### 7.1 Secrets Management
- All API keys SHALL be stored in environment variables
- .env file SHALL be git-ignored
- .env.example SHALL document required variables without values
- credentials.json SHALL be git-ignored
- Token files SHALL be stored in git-ignored directory

### 7.2 Access Control
- Role verification SHALL occur before command execution
- Database queries SHALL filter by user permissions
- Admin commands SHALL be restricted to ADMIN role
- Moderator commands SHALL require MODERATOR or ADMIN role

### 7.3 Input Validation
- Email addresses SHALL be validated with regex
- Phone numbers SHALL be sanitized
- SQL queries SHALL use parameterized statements
- File uploads SHALL validate file types and sizes

### 7.4 Secure Communication
- All external API calls SHALL use HTTPS
- OAuth tokens SHALL be transmitted securely
- Telegram webhook SHALL use SSL certificate

### 7.5 Data Protection
- Resume files SHALL be stored with restricted permissions (0600)
- Database SHALL be backed up daily
- Backups SHALL be encrypted at rest
- PII SHALL not appear in logs or error messages

---

## 8. Performance Requirements

### 8.1 Response Time Targets
- Command execution: < 2 seconds
- Application listing: < 1 second (per page)
- Resume download: < 3 seconds
- Excel export: < 10 seconds (1000 records)
- AI analysis: < 15 seconds per resume

### 8.2 Optimization Strategies
- Database connection pooling
- Async I/O for all network operations
- Lazy loading of relationships
- Pagination for large datasets
- Caching of AI analysis results

### 8.3 Resource Limits
- Maximum resume file size: 10MB
- Maximum email attachment size: 25MB (Gmail limit)
- Maximum concurrent API requests: 10
- Database query timeout: 30 seconds

---

## 9. Deployment Requirements

### 9.1 Container Configuration
- Base image: python:3.11-slim
- Working directory: /app
- Non-root user for security
- Volume mounts for persistence

### 9.2 Docker Compose Setup
```
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./hrbot.db:/app/hrbot.db
      - ./downloads:/app/downloads
      - ./exports:/app/exports
      - ./gmail_tokens:/app/gmail_tokens
      - ./logs:/app/logs
      - ./bot/gmail_accounts.json:/app/bot/gmail_accounts.json
```

### 9.3 Environment Variables
Required variables:
- `BOT_TOKEN`: Telegram bot token
- `GEMINI_API_KEY`: Google Gemini API key
- `DATABASE_URL`: SQLite database path
- `GMAIL_CHECK_INTERVAL`: Polling interval in minutes

### 9.4 Deployment Steps
1. Clone repository
2. Create .env file from .env.example
3. Place credentials.json in project root
4. Run `docker-compose up -d`
5. Execute database migrations: `alembic upgrade head`
6. Assign first admin user via database

### 9.5 Health Checks
- Bot process SHALL log startup confirmation
- Background scheduler SHALL log each polling cycle
- Database connectivity SHALL be verified on startup

### 9.6 Monitoring
- Application logs SHALL be written to logs/ directory
- Container logs SHALL be accessible via `docker logs`
- Error rate SHALL be monitored
- API quota usage SHALL be tracked

---

## 10. Testing Requirements

### 10.1 Unit Testing

#### 10.1.1 Coverage Requirements
- Service layer: 90%+ coverage
- Database models: 80%+ coverage
- Utility functions: 100% coverage

#### 10.1.2 Test Framework
- pytest for test execution
- pytest-asyncio for async tests
- pytest-cov for coverage reporting

#### 10.1.3 Test Scope
- Service methods with mocked dependencies
- Data validation and transformation
- Error handling and edge cases
- Database operations with in-memory SQLite

### 10.2 Integration Testing

#### 10.2.1 Test Scenarios
- Gmail OAuth flow
- Email parsing with real email samples
- Resume extraction from various formats
- Gemini API integration with sample resumes
- Database transactions and rollbacks

#### 10.2.2 Test Environment
- Separate test database
- Mocked external API responses
- Test data fixtures

### 10.3 Manual Testing

#### 10.3.1 Test Cases
- User registration and role assignment
- Gmail account addition via OAuth
- Email parsing triggering
- Application status changes
- Export generation
- Permission enforcement

#### 10.3.2 Test Data
- Sample resumes in PDF and DOCX formats
- Test Gmail accounts with controlled emails
- Multiple user accounts with different roles

### 10.4 Quality Gates
- All tests SHALL pass before merging to main branch
- Code coverage SHALL not decrease with new commits
- Static analysis (pylint, mypy) SHALL report no critical issues
- Security scanning SHALL detect no vulnerabilities

---

## 11. Monitoring & Logging

### 11.1 Logging Strategy

#### 11.1.1 Log Levels
- **INFO**: Normal operations (startup, parsing completion, user actions)
- **WARN**: Recoverable issues (token refresh, API retries, missing fields)
- **ERROR**: Failures requiring attention (API errors, database errors, parsing failures)

#### 11.1.2 Log Format
```
[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
```

#### 11.1.3 Log Contents
- Timestamp with timezone
- Log level
- Module/logger name
- Message with context
- Exception stack traces (for errors)

#### 11.1.4 Sensitive Data
- SHALL NOT log API keys or tokens
- SHALL NOT log full resume content
- SHALL NOT log candidate PII in debug logs
- SHALL mask email addresses in non-critical logs

### 11.2 Metrics Collection

#### 11.2.1 Key Metrics
- Applications processed per hour
- AI analysis success rate
- Gmail API quota usage
- Bot command response times
- Error rates by type

#### 11.2.2 Alerting
- Critical errors SHALL notify admins via Telegram
- Gmail token expiration SHALL alert before failure
- API quota exhaustion SHALL trigger warnings at 80%

### 11.3 Audit Trail
- Role changes SHALL be logged
- Application deletions SHALL be logged
- Gmail account additions/removals SHALL be logged
- Export operations SHALL be logged

---

## 12. Scalability Considerations

### 12.1 Current Limitations
- SQLite single-writer bottleneck
- File system storage for resumes
- Single bot instance deployment
- In-memory state for multi-step operations

### 12.2 Future Scaling Path

#### 12.2.1 Database Migration
- Migrate to PostgreSQL for concurrent writes
- Implement read replicas for queries
- Partition large tables by date

#### 12.2.2 Storage Migration
- Move resume files to S3-compatible object storage
- Implement CDN for file downloads
- Use signed URLs for temporary access

#### 12.2.3 Multi-Instance Deployment
- Replace in-memory state with Redis
- Implement distributed locking
- Use message queue for background tasks (Celery)

#### 12.2.4 Caching Layer
- Redis cache for frequently accessed data
- Cache Gemini analysis results
- Cache vacancy listings

### 12.3 Capacity Planning
- Current design: 100 applications/hour, 10 concurrent users
- Target: 1000 applications/hour, 100 concurrent users
- Database: Migrate to PostgreSQL at 50,000 applications
- Storage: Migrate to object storage at 100GB

---

## 13. Compliance & Legal

### 13.1 Data Privacy
- System SHALL comply with GDPR for EU candidates
- System SHALL support data deletion requests (Right to be Forgotten)
- System SHALL provide data export on request (Right to Access)
- System SHALL obtain consent before storing candidate data

### 13.2 Data Retention
- Application data SHALL be retained for 2 years
- Deleted applications SHALL be purged after 90 days
- Resume files SHALL be archived after 180 days
- Logs SHALL be retained for 30 days

### 13.3 Terms of Service
- Bot SHALL display terms on first use
- System SHALL require acceptance before processing
- Terms SHALL outline data usage and retention

---

## 14. Maintenance & Support

### 14.1 Backup Strategy
- Database: Daily backups with 30-day retention
- Resume files: Weekly backups with 90-day retention
- Configuration: Version controlled in Git

### 14.2 Update Procedures
- Dependency updates: Monthly security patches
- Feature updates: Quarterly releases
- Database migrations: Tested in staging before production

### 14.3 Disaster Recovery
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 24 hours
- Restore process documented in runbook

### 14.4 Support Channels
- GitHub Issues for bug reports
- Internal Telegram group for user support
- Admin documentation for troubleshooting

---

## 15. Glossary

**Application**: A candidate's job application including resume and contact information

**Vacancy**: A job opening or position being recruited for

**Processing**: Marking an application as reviewed by HR team

**Soft Delete**: Marking records as deleted without removing from database

**OAuth Token**: Temporary credential for accessing Gmail API

**Callback Query**: Telegram inline keyboard button interaction

**Service Layer**: Business logic components isolated from presentation layer

---

## 16. Revision History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.0     | 2026-03-06 | System | Initial technical requirements document |

---

**Document Owner**: Development Team
**Approval Required**: Product Owner, Technical Lead
**Next Review Date**: 2026-06-06
