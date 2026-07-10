-- Optional demo seed data for RiskLens AI
USE risklens_ai;

INSERT INTO customers (full_name, age, occupation, employment_type, years_of_employment, annual_income, credit_score, open_accounts, previous_defaults)
VALUES
('Ravi Kumar', 34, 'Software Engineer', 'Salaried', 8, 1450000, 780, 3, 0),
('Anita Sharma', 45, 'Shop Owner', 'Business Owner', 12, 900000, 610, 5, 1),
('Vikram Singh', 29, 'Freelance Designer', 'Self-Employed', 3, 550000, 560, 6, 2),
('Meera Nair', 52, 'Bank Manager', 'Salaried', 20, 2100000, 810, 2, 0);
