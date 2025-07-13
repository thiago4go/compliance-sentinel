-- Compliance Sentinel Database Initialization
-- This script sets up the core tables for the compliance management system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    size VARCHAR(50), -- SMB, Enterprise, etc.
    country VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance frameworks
CREATE TABLE compliance_frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(50),
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default frameworks
INSERT INTO compliance_frameworks (name, description, version) VALUES
('GDPR', 'General Data Protection Regulation', '2018'),
('ISO 27001', 'Information Security Management Systems', '2022'),
('SOX', 'Sarbanes-Oxley Act', '2002'),
('HIPAA', 'Health Insurance Portability and Accountability Act', '1996'),
('PCI DSS', 'Payment Card Industry Data Security Standard', '4.0');

-- Compliance assessments
CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    framework_id UUID REFERENCES compliance_frameworks(id),
    status VARCHAR(50) DEFAULT 'in_progress', -- in_progress, completed, failed
    score DECIMAL(5,2), -- Overall compliance score
    risk_level VARCHAR(20), -- low, medium, high, critical
    assessment_data JSONB, -- Detailed assessment results
    recommendations TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100) -- Agent or user identifier
);

-- Compliance requirements
CREATE TABLE compliance_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID REFERENCES compliance_frameworks(id),
    requirement_id VARCHAR(50) NOT NULL, -- e.g., "GDPR-7.1", "ISO-A.5.1"
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    implementation_guidance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Assessment results for individual requirements
CREATE TABLE assessment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID REFERENCES compliance_assessments(id),
    requirement_id UUID REFERENCES compliance_requirements(id),
    status VARCHAR(50), -- compliant, non_compliant, partial, not_applicable
    score DECIMAL(5,2),
    evidence TEXT,
    gaps TEXT[],
    recommendations TEXT[],
    remediation_effort VARCHAR(20), -- low, medium, high
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent workflow logs
CREATE TABLE agent_workflow_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    activity_name VARCHAR(100),
    status VARCHAR(50), -- started, completed, failed, retrying
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit trail for all compliance activities
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- assessment, requirement, etc.
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- created, updated, deleted
    changes JSONB, -- What changed
    performed_by VARCHAR(100), -- Agent or user
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Indexes for performance
CREATE INDEX idx_companies_name ON companies USING gin(name gin_trgm_ops);
CREATE INDEX idx_assessments_company ON compliance_assessments(company_id);
CREATE INDEX idx_assessments_framework ON compliance_assessments(framework_id);
CREATE INDEX idx_assessments_status ON compliance_assessments(status);
CREATE INDEX idx_assessments_created ON compliance_assessments(created_at);
CREATE INDEX idx_requirements_framework ON compliance_requirements(framework_id);
CREATE INDEX idx_results_assessment ON assessment_results(assessment_id);
CREATE INDEX idx_workflow_logs_workflow ON agent_workflow_logs(workflow_id);
CREATE INDEX idx_workflow_logs_agent ON agent_workflow_logs(agent_name);
CREATE INDEX idx_audit_entity ON audit_trail(entity_type, entity_id);

-- Update triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for demo
INSERT INTO companies (name, industry, size, country) VALUES
('TechStart Inc.', 'Technology', 'SMB', 'United States'),
('HealthCare Solutions', 'Healthcare', 'SMB', 'Canada'),
('FinanceFirst Ltd.', 'Financial Services', 'SMB', 'United Kingdom');

-- Sample compliance requirements for GDPR
INSERT INTO compliance_requirements (framework_id, requirement_id, title, description, category, priority) 
SELECT 
    cf.id,
    'GDPR-7.1',
    'Data Protection by Design and by Default',
    'Implement appropriate technical and organisational measures to ensure data protection principles are integrated into processing activities',
    'Data Protection',
    'high'
FROM compliance_frameworks cf WHERE cf.name = 'GDPR';

INSERT INTO compliance_requirements (framework_id, requirement_id, title, description, category, priority) 
SELECT 
    cf.id,
    'GDPR-32.1',
    'Security of Processing',
    'Implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk',
    'Security',
    'critical'
FROM compliance_frameworks cf WHERE cf.name = 'GDPR';

-- Sample ISO 27001 requirements
INSERT INTO compliance_requirements (framework_id, requirement_id, title, description, category, priority) 
SELECT 
    cf.id,
    'ISO-A.5.1',
    'Information Security Policies',
    'A set of policies for information security shall be defined, approved by management, published and communicated',
    'Governance',
    'high'
FROM compliance_frameworks cf WHERE cf.name = 'ISO 27001';

COMMIT;
