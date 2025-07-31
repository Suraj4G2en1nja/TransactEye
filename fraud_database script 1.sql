CREATE DATABASE fraud_detection;
USE fraud_detection;


CREATE TABLE Transactions (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    TransactionType ENUM('payment', 'transfer', 'cash_out', 'deposit') NOT NULL,
    Amount DECIMAL(12, 2) NOT NULL,
    OldBalanceSender DECIMAL(12, 2),
    NewBalanceSender DECIMAL(12, 2),
    OldBalanceReceiver DECIMAL(12, 2),
    NewBalanceReceiver DECIMAL(12, 2),
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_fraud BOOLEAN DEFAULT 0,
    fraud_reason VARCHAR(255),
    fraud_score DECIMAL(5, 2)
);


INSERT INTO Transactions (
    TransactionType, Amount,
    OldBalanceSender, NewBalanceSender,
    OldBalanceReceiver, NewBalanceReceiver,
    is_fraud, fraud_reason, fraud_score
) VALUES (
    'transfer', 1500.00, 5400.00, 3900.00, 150.00, 1650.00, 1, 'anomaly_detected', 0.87
);


SELECT * FROM Transactions;

DELETE FROM Transactions WHERE TransactionID = 1;

UPDATE Transactions
SET is_fraud = 0, fraud_reason = NULL, fraud_score = NULL
WHERE TransactionID = 2;





