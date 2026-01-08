 
DROP TABLE IF EXISTS `Address` ;

CREATE TABLE IF NOT EXISTS `Address` (
  `IdAddress` INT NOT NULL AUTO_INCREMENT,
  `Cep` VARCHAR(45) NULL,
  `City` VARCHAR(250) NULL,
  `Estate` VARCHAR(250) NULL,
  `Adress` VARCHAR(245) NULL,
  `Number` INT NULL,
  `Neighborhood` VARCHAR(250) NULL,
  `Complement` VARCHAR(250) NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdAddress`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `BusinessPartner`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `BusinessPartner` ;

CREATE TABLE IF NOT EXISTS `BusinessPartner` (
  `IdBusinessPartner` INT NOT NULL AUTO_INCREMENT,
  `RazaoSocial` VARCHAR(450) NOT NULL,
  `NomeFantasia` VARCHAR(450) NOT NULL,
  `CNPJ` VARCHAR(45) NOT NULL,
  `InscricaoEstadual` VARCHAR(45) NULL,
  `InscricaoMunicipal` VARCHAR(45) NULL,
  `CNAE` VARCHAR(45) NULL,
  `Suframa` VARCHAR(45) NULL,
  `RegimeEspecial` TINYINT NOT NULL,
  `SugestaoLimiteCredito` DECIMAL(13,2) NOT NULL,
  `Email` VARCHAR(45) NULL,
  `Phone` VARCHAR(45) NULL,
  `Observation` VARCHAR(5000) NULL,
  `AddressId` INT NOT NULL, 
  `CompanyId` INT NOT NULL,
  `SynchronizationStatusId` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdBusinessPartner`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company` ;

CREATE TABLE IF NOT EXISTS `Company` (
  `IdCompany` INT NOT NULL,
  `RazaoSocial` VARCHAR(450) NOT NULL,
  `NomeFantasia` VARCHAR(450) NOT NULL,
  `CNPJ` VARCHAR(45) NOT NULL,
  `Email` VARCHAR(45) NULL,
  `Phone` VARCHAR(45) NULL,
  `AddressId` INT NOT NULL,
  `CompanyAPIConfigurationId` INT NOT NULL,
  `CompanyPlanConfigurationId` INT NOT NULL, 
  `SynchronizationStatusId` INT NULL,
  `Active` TINYINT NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `CompanyAPIConfiguration`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CompanyAPIConfiguration` ;

CREATE TABLE IF NOT EXISTS `CompanyAPIConfiguration` (
  `IdCompanyAPIConfiguration` INT NOT NULL AUTO_INCREMENT,
  `Token` VARCHAR(5000) NOT NULL,
  `AccessJSON` JSON NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompanyAPIConfiguration`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `CompanyPlanConfiguration`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CompanyPlanConfiguration` ;

CREATE TABLE IF NOT EXISTS `CompanyPlanConfiguration` (
  `IdCompanyPlanConfiguration` INT NOT NULL AUTO_INCREMENT,
  `MaxSolicitation` INT NULL,
  `ValidUntil` DATETIME NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompanyPlanConfiguration`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_Branch`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_Branch` ;

CREATE TABLE IF NOT EXISTS `Company_Branch` (
  `IdCompany_Branch` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(250) NOT NULL,
  `Code` VARCHAR(250) NOT NULL,
  `Company_IdCompany` INT NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_Branch`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_Freight`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_Freight` ;

CREATE TABLE IF NOT EXISTS `Company_Freight` (
  `IdCompany_Freight` INT NOT NULL,
  `Name` VARCHAR(250) NOT NULL,
  `Code` VARCHAR(250) NOT NULL,
  `Company_IdCompany` INT NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_Freight`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_PaymentMethod`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_PaymentMethod` ;

CREATE TABLE IF NOT EXISTS `Company_PaymentMethod` (
  `IdCompany_PaymentMethod` INT NOT NULL,
  `Name` VARCHAR(250) NOT NULL,
  `Code` VARCHAR(250) NOT NULL,
  `Company_IdCompany` INT NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_PaymentMethod`, `Company_IdCompany`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_PaymentTerm`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_PaymentTerm` ;

CREATE TABLE IF NOT EXISTS `Company_PaymentTerm` (
  `IdCompany_PaymentTerm` INT NOT NULL,
  `Name` VARCHAR(250) NOT NULL,
  `Code` VARCHAR(250) NOT NULL,
  `Company_IdCompany` INT NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_PaymentTerm`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_Product`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_Product` ;

CREATE TABLE IF NOT EXISTS `Company_Product` (
  `IdProduct` INT NOT NULL AUTO_INCREMENT,
  `Code` VARCHAR(250) NULL,
  `Name` VARCHAR(250) NULL,
  `Weigth` DECIMAL(13,2) NULL,
  `Size` DECIMAL(13,2) NULL,
  `Company_IdCompany` INT NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdProduct`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_Product_Stock`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_Product_Stock` ;

CREATE TABLE IF NOT EXISTS `Company_Product_Stock` (
  `IdCompany_Product_Stock` INT NOT NULL AUTO_INCREMENT,
  `Quantity` DECIMAL(13,2) NOT NULL,
  `CodeProduct` DECIMAL(13,2) NOT NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `Company_Product_IdProduct` INT NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_Product_Stock`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_Utilization`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_Utilization` ;

CREATE TABLE IF NOT EXISTS `Company_Utilization` (
  `IdCompany_Utilization` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(250) NOT NULL,
  `Code` VARCHAR(250) NOT NULL,
  `Company_IdCompany` INT NOT NULL,
  `Company_Utilization` VARCHAR(45) NULL,
  `SincronizationStatus_IdSincronizationStatus` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_Utilization`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Company_has_User`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Company_has_User` ;

CREATE TABLE IF NOT EXISTS `Company_has_User` (
  `IdCompany_has_User` INT NOT NULL AUTO_INCREMENT,
  `Company_IdCompany` INT NULL,
  `User_IdUser` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdCompany_has_User`))
ENGINE = InnoDB;




-- -----------------------------------------------------
-- Table `SalesOrder`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `SalesOrder` ;

CREATE TABLE IF NOT EXISTS `SalesOrder` (
  `IdSalesOrder` INT NOT NULL AUTO_INCREMENT,
  `Redespacho` TINYINT NOT NULL,
  `DataLancamento` DATETIME NOT NULL,
  `DataEntrega` DATETIME NOT NULL,
  `Discount` DECIMAL(13,2) NULL,
  `Observation` VARCHAR(5000) NULL,
  `CompanyId` INT NOT NULL,
  `BusinessPartnerId` INT NOT NULL,
  `SynchronizationStatusId` INT NULL,
  `PaymentMethodId` INT NOT NULL,
  `PaymentTermId` INT NOT NULL,
  `UtilizationId` INT NOT NULL,
  `BranchId` INT NOT NULL,
  `FreightId` INT NOT NULL,
  `RedespachoSalesOrderId` INT NOT NULL,
  `SalesOrder_IdSalesOrder` INT NOT NULL,
  `CreatedByUserId` INT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdSalesOrder`, `SalesOrder_IdSalesOrder`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `SalesOrder_Product`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `SalesOrder_Product` ;

CREATE TABLE IF NOT EXISTS `SalesOrder_Product` (
  `IdProduct` INT NOT NULL AUTO_INCREMENT,
  `Code` VARCHAR(250) NOT NULL,
  `Name` VARCHAR(250) NOT NULL,
  `DataLancamento` DATETIME NOT NULL,
  `DataEntrega` DATETIME NOT NULL, 
  `Weight` DECIMAL(13,2) NULL,
  `Size` DECIMAL(13,2) NULL,
  `Quantity` DECIMAL(13,2) NOT NULL,
  `Discount` DECIMAL(13,2) NULL,
  `Price` DECIMAL(13,2) NOT NULL,
  `Estoque` DECIMAL(13,2) NULL,
  `SalesOrder_IdSalesOrder` INT NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdProduct`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `SalesOrder_Redespacho`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `SalesOrder_Redespacho` ;

CREATE TABLE IF NOT EXISTS `SalesOrder_Redespacho` (
  `IdSalesOrder_Redespacho` INT NOT NULL AUTO_INCREMENT,
  `CNPJ` VARCHAR(45) NOT NULL,
  `Nome_Transportadora` VARCHAR(250) NULL,
  `Address_IdAddress` INT NOT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdSalesOrder_Redespacho`, `Address_IdAddress`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `SincronizationStatus`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `SincronizationStatus` ;

CREATE TABLE IF NOT EXISTS `SincronizationStatus` (
  `IdSincronizationStatus` INT NOT NULL AUTO_INCREMENT,
  `Status` VARCHAR(45) NULL,
  `Error` VARCHAR(45) NULL,
  `CodeError` VARCHAR(45) NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdSincronizationStatus`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `User`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `User` ;

CREATE TABLE IF NOT EXISTS `User` (
  `IdUser` INT NOT NULL AUTO_INCREMENT,
  `UserName` VARCHAR(250) NULL,
  `Password` VARCHAR(450) NOT NULL,
  `Email` VARCHAR(250) NOT NULL,
  `Phone` VARCHAR(45) NULL,
  `Token` VARCHAR(5000) NULL, 
  `Address_IdAddress` INT NULL, 
  `Active` TINYINT NULL,
  `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`IdUser`))
ENGINE = InnoDB;

 
 