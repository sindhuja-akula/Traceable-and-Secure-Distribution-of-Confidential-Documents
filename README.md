Secure PDF Distribution and Traceability System
# Project Overview

In academic, corporate, and creative domains, confidential documents such as scripts, evaluation materials, and internal reports are often shared digitally with multiple reviewers. Once distributed, controlling unauthorized sharing and identifying data leaks becomes extremely difficult.

This project proposes a Secure PDF Distribution and Traceability System that allows a document owner to generate protected PDFs, distribute them to multiple recipients via email, and track delivery while embedding unique traceable identifiers into each PDF. If a document is leaked, the embedded identifiers help trace the source of leakage.

The system focuses on document security, controlled access, traceability, and automated email delivery at a college-project scope.

# Objectives

Convert user-provided text into a secured PDF

Apply watermarking and metadata-based traceability

Protect PDFs using per-recipient passwords

Distribute PDFs via automated email delivery

Track email delivery status and retry failed emails

Maintain logs for auditing and traceability

# System Architecture

The application follows a modular architecture:

Frontend (Web Browser)
        ↓
Backend (Python + Flask)
        ↓
Database (SQLite)
        ↓
PDF Engine + Email Engine


Each module has a clearly defined responsibility to ensure scalability and maintainability.

# Workflow Summary

User enters content and recipient email addresses through the frontend

Backend receives data via HTTP POST

A unique Job ID is created

For each recipient:

Unique Trace ID and password are generated

Recipient details are stored in the database

PDF is generated with:

Watermark

Embedded metadata (Trace ID)

Password protection

PDF is emailed to recipients

Email delivery status is logged

Failed emails are retried automatically

Final status is returned to the user

# Security & Traceability Features

Watermarking: Visible identifier (email/phone/name)

Metadata Embedding: Invisible Trace ID stored inside PDF metadata

Password Protection: Unique password per recipient

Access Control: Only intended recipients can open the document

Leak Detection: Extract metadata from leaked PDFs to identify source

# Key Features

Secure text-to-PDF conversion

Per-user PDF password generation

Metadata-based traceability

Automated bulk email distribution

Email delivery tracking and retry mechanism

Centralized logging using database

College-level implementation with real-world relevance

# Technologies Used
Frontend

HTML

CSS

Basic JavaScript

Backend

Python

Flask (Web Framework)

Database

SQLite

PDF Processing

ReportLab (PDF generation)

PyPDF2 (PDF manipulation & encryption)

Email Service

SMTP (Gmail or institutional email)

 # Database Schema (High Level)

Users / Owner

Jobs

Recipients

Trace IDs

Passwords

Email Delivery Logs

# Project Structure (Proposed)
project-root/
│
├── app.py                # Flask application
├── database.db           # SQLite database
├── templates/            # HTML files
├── static/               # CSS & JS
├── pdf_engine/           # PDF creation & security
├── email_engine/         # Email sending & retry logic
├── utils/                # Helper functions
├── README.md             # Project documentation
└── requirements.txt      # Dependencies



# Team Information

Team Size: 4 Members

Project Duration: 4 Months

Level: College / Academic Project

# Academic Relevance

This project demonstrates concepts from:

Web Development

Database Management Systems

Information Security

Software Engineering

Distributed Systems

# Conclusion

The Secure PDF Distribution and Traceability System provides a practical approach to document security and controlled sharing. While designed at a college-project level, the architecture and concepts closely align with real-world digital rights management systems, making it both educational and industry-relevant.
