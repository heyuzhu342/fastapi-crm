-- FastAPI CRM MySQL 初始化脚本
-- MySQL 5.7 兼容

CREATE DATABASE IF NOT EXISTS `fastapi_crm`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `fastapi_crm`;

-- 时间戳函数兼容（MySQL 5.7 不支持 CURRENT_TIMESTAMP 多个）
-- 由 SQLAlchemy server_default 处理
