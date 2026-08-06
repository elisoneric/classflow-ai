# ClassFlow AI - Project Specifications

## 1. Overview
ClassFlow AI is a platform designed to automate communication between lecturers and students regarding scheduled university classes. It acts as an intermediary, sending automated reminders to lecturers, parsing their responses using AI, and forwarding the parsed status to the class WhatsApp group.

## 2. Scope & Target Audience
- **Primary User:** Course Representative (Single Admin).
- **Lecturers:** No login required. Interact via Email (and later WhatsApp).
- **Students:** Receive updates directly in the class WhatsApp group.

## 3. Architecture & Tech Stack
- **Backend:** FastAPI, Python, SQLAlchemy, Alembic
- **Database:** PostgreSQL
- **Background Jobs & Scheduling:** Redis, RQ (Redis Queue), APScheduler
- **Frontend:** React, TypeScript, TailwindCSS, Vite
- **Deployment:** Docker & Docker Compose

## 4. Key Decisions
1. **Email Ingestion:** Uses standard IMAP polling connected to a cPanel-hosted email account. To reliably track responses, outbound emails will embed a unique session reference ID (e.g., `Ref: [SESSION_ID]`).
2. **AI Interpretation:** Utilizes **Gemini 1.5 Flash** for parsing natural language replies from lecturers into structured JSON.
3. **WhatsApp Integration:** An unofficial WhatsApp Web bot (using Baileys or `whatsapp-web.js`) will run as a separate Node.js microservice to handle automated group messaging.

## 5. Domain Models
- **CourseRep (User):** Admin account for dashboard access.
- **Lecturer:** Contact details and preferences.
- **Course:** Active/Paused/Completed status.
- **Timetable:** Weekly schedule templates.
- **ClassSession:** A generated instance for a specific day, tracking its state (`SCHEDULED`, `WAITING`, `CONFIRMED`, `CANCELLED`, `DELAYED`, `RELOCATED`, `ONLINE`, `REVIEW_NEEDED`).

## 6. Implementation Phases
1. **Infrastructure Setup:** Docker compose, FastAPI boilerplate, React boilerplate.
2. **Database & Core Models:** Alembic migrations for core entities.
3. **API & Dashboard Foundation:** CRUD endpoints for Lecturers, Courses, and Timetables.
4. **Scheduling Engine:** APScheduler generating daily sessions and RQ enqueuing reminders.
5. **Notification Layer:** Email sending (SMTP) and Ingestion (IMAP).
6. **AI Pipeline:** Integrating Gemini 1.5 Flash for response parsing.
7. **WhatsApp Service:** Building the Node.js bot.
8. **Frontend Dashboard:** React UI for management and daily view.
9. **Final Assembly & Testing:** End-to-end testing and deployment scripts.
