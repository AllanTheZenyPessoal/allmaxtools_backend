-- Create SalesOrder table
CREATE TABLE IF NOT EXISTS `SalesOrder` (
    `IdSalesOrder` INT AUTO_INCREMENT PRIMARY KEY,
    `Redespacho` INT DEFAULT 0,
    `DataLancamento` DATE NULL,
    `DataEntrega` DATE NULL,
    `Discount` FLOAT DEFAULT 0,
    `Observation` TEXT NULL,
    `Company_IdCompany` INT NULL,
    `BusinessPartner_IdBusinessPartner` INT NULL,
    `CompanyPaymentMethod_IdCompanyPaymentMethod` INT NULL,
    `CompanyPaymentTerm_IdCompanyPaymentTerm` INT NULL,
    `CompanyUtilization_IdCompanyUtilization` INT NULL,
    `CompanyBranch_IdCompanyBranch` INT NULL,
    `CompanyFreight_IdCompanyFreight` INT NULL,
    `SalesOrderRedespacho_IdSalesOrderRedespacho` INT NULL,
    `SincronizationStatus_IdSincronizationStatus` INT NULL,
    `CreatedByUserId` INT NULL,
    `CreatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes for better performance
CREATE INDEX idx_salesorder_company ON `SalesOrder` (`Company_IdCompany`);
CREATE INDEX idx_salesorder_createdby ON `SalesOrder` (`CreatedByUserId`);
CREATE INDEX idx_salesorder_datalancamento ON `SalesOrder` (`DataLancamento`);
CREATE INDEX idx_salesorder_businesspartner ON `SalesOrder` (`BusinessPartner_IdBusinessPartner`);
