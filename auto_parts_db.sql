-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema auto_parts_db
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema auto_parts_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `auto_parts_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `auto_parts_db` ;

-- -----------------------------------------------------
-- Table `auto_parts_db`.`Customer`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`Customer` (
  `customer_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `address` VARCHAR(200) NULL DEFAULT NULL,
  `phone` VARCHAR(20) NULL DEFAULT NULL,
  `email` VARCHAR(100) NULL DEFAULT NULL,
  `username` VARCHAR(50) NULL DEFAULT NULL,
  `password` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`customer_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`Store`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`Store` (
  `store_id` INT NOT NULL AUTO_INCREMENT,
  `store_name` VARCHAR(100) NOT NULL,
  `location` VARCHAR(150) NULL DEFAULT NULL,
  PRIMARY KEY (`store_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`Employee`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`Employee` (
  `employee_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `role` VARCHAR(50) NULL DEFAULT NULL,
  `username` VARCHAR(50) NULL DEFAULT NULL,
  `password` VARCHAR(100) NULL DEFAULT NULL,
  `store_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`employee_id`),
  INDEX `idx_employee_store` (`store_id` ASC) VISIBLE,
  CONSTRAINT `fk_employee_store`
    FOREIGN KEY (`store_id`)
    REFERENCES `auto_parts_db`.`Store` (`store_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`AutoPart`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`AutoPart` (
  `part_id` INT NOT NULL AUTO_INCREMENT,
  `part_name` VARCHAR(120) NOT NULL,
  `category` VARCHAR(80) NULL DEFAULT NULL,
  `price` DECIMAL(10,2) NULL DEFAULT NULL,
  `stock_qty` INT NULL DEFAULT NULL,
  `condition` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`part_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`Order`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`Order` (
  `order_id` INT NOT NULL AUTO_INCREMENT,
  `order_date` DATE NULL DEFAULT NULL,
  `delivery_date` DATE NULL DEFAULT NULL,
  `customer_id` INT NULL DEFAULT NULL,
  `employee_id` INT NULL DEFAULT NULL,
  `store_id` INT NULL DEFAULT NULL,
  `total_amount` DECIMAL(12,2) NULL DEFAULT NULL,
  `payment_status` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  INDEX `idx_order_customer` (`customer_id` ASC) VISIBLE,
  INDEX `idx_order_employee` (`employee_id` ASC) VISIBLE,
  INDEX `idx_order_store` (`store_id` ASC) VISIBLE,
  CONSTRAINT `fk_order_customer`
    FOREIGN KEY (`customer_id`)
    REFERENCES `auto_parts_db`.`Customer` (`customer_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_order_employee`
    FOREIGN KEY (`employee_id`)
    REFERENCES `auto_parts_db`.`Employee` (`employee_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_order_store`
    FOREIGN KEY (`store_id`)
    REFERENCES `auto_parts_db`.`Store` (`store_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`OrderDetail`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`OrderDetail` (
  `order_id` INT NOT NULL,
  `part_id` INT NOT NULL,
  `quantity` INT NOT NULL,
  `subtotal` DECIMAL(12,2) NULL DEFAULT NULL,
  PRIMARY KEY (`order_id`, `part_id`),
  INDEX `idx_orderdetail_part` (`part_id` ASC) VISIBLE,
  CONSTRAINT `fk_orderdetail_order`
    FOREIGN KEY (`order_id`)
    REFERENCES `auto_parts_db`.`Order` (`order_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_orderdetail_part`
    FOREIGN KEY (`part_id`)
    REFERENCES `auto_parts_db`.`AutoPart` (`part_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `auto_parts_db`.`Payment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `auto_parts_db`.`Payment` (
  `payment_id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NULL DEFAULT NULL,
  `method` VARCHAR(50) NULL DEFAULT NULL,
  `card_type` VARCHAR(50) NULL DEFAULT NULL,
  `card_number` VARCHAR(50) NULL DEFAULT NULL,
  `billing_address` VARCHAR(200) NULL DEFAULT NULL,
  `amount` DECIMAL(12,2) NULL DEFAULT NULL,
  PRIMARY KEY (`payment_id`),
  INDEX `idx_payment_order` (`order_id` ASC) VISIBLE,
  CONSTRAINT `fk_payment_order`
    FOREIGN KEY (`order_id`)
    REFERENCES `auto_parts_db`.`Order` (`order_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
