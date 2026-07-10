-- ============================================================
-- RiskLens AI :: Production Database Schema (MySQL 8.0+)
-- Normalized to 3NF. Designed for a real lending workflow.
-- ============================================================

CREATE DATABASE IF NOT EXISTS risklens_ai
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE risklens_ai;

-- ------------------------------------------------------------
-- 1. customers : master borrower record (KYC-level info)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name           VARCHAR(150) NOT NULL,
    age                  TINYINT UNSIGNED NOT NULL CHECK (age BETWEEN 18 AND 100),
    occupation          VARCHAR(100),
    employment_type     ENUM('Salaried','Self-Employed','Business Owner','Unemployed','Retired') NOT NULL,
    years_of_employment DECIMAL(4,1) DEFAULT 0,
    annual_income       DECIMAL(14,2) NOT NULL,
    credit_score        SMALLINT UNSIGNED NOT NULL CHECK (credit_score BETWEEN 300 AND 900),
    open_accounts       SMALLINT UNSIGNED DEFAULT 0,
    previous_defaults   SMALLINT UNSIGNED DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_credit_score (credit_score),
    INDEX idx_employment_type (employment_type)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. loan_applications : one customer can apply for many loans
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS loan_applications (
    application_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id          BIGINT NOT NULL,
    loan_amount          DECIMAL(14,2) NOT NULL,
    loan_purpose         VARCHAR(100),
    existing_debt        DECIMAL(14,2) DEFAULT 0,
    monthly_emi          DECIMAL(12,2) DEFAULT 0,
    application_status   ENUM('PENDING','APPROVED','REJECTED','UNDER_REVIEW') DEFAULT 'PENDING',
    application_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_status (application_status)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. risk_assessments : deterministic financial risk metrics
--    (rule-based, independent of the ML model)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    application_id         BIGINT NOT NULL,
    debt_to_income_ratio   DECIMAL(6,4),
    emi_to_income_ratio    DECIMAL(6,4),
    loan_to_income_ratio   DECIMAL(6,4),
    credit_utilization_score DECIMAL(6,4),
    financial_risk_score   DECIMAL(5,2),   -- 0-100 rule-based score
    assessed_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. predictions : ML model output + explainability payload
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    application_id         BIGINT NOT NULL,
    model_name             VARCHAR(50),
    default_probability    DECIMAL(6,4),
    risk_score             DECIMAL(5,2),   -- 0-100 blended score
    risk_category           ENUM('LOW','MEDIUM','HIGH','CRITICAL'),
    recommendation          ENUM('APPROVE','REVIEW','REJECT'),
    top_risk_drivers        JSON,           -- SHAP-based explanation
    predicted_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    INDEX idx_risk_category (risk_category)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. audit_logs : full traceability for compliance / model risk mgmt
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_type       VARCHAR(50),   -- e.g. 'customer','application','prediction'
    entity_id         BIGINT,
    action             VARCHAR(50),   -- 'CREATE','UPDATE','PREDICT','EXPORT'
    performed_by       VARCHAR(100) DEFAULT 'system',
    details             JSON,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Convenience view for dashboards
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_loan_risk_summary AS
SELECT
    c.customer_id, c.full_name, c.age, c.employment_type, c.annual_income,
    c.credit_score, la.application_id, la.loan_amount, la.loan_purpose,
    la.application_status, ra.debt_to_income_ratio, ra.financial_risk_score,
    p.default_probability, p.risk_score, p.risk_category, p.recommendation,
    la.application_date
FROM customers c
JOIN loan_applications la ON c.customer_id = la.customer_id
LEFT JOIN risk_assessments ra ON la.application_id = ra.application_id
LEFT JOIN predictions p ON la.application_id = p.application_id;
