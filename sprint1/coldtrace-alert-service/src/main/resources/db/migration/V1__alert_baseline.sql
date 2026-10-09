CREATE TABLE processed_events (
  event_id CHAR(36) NOT NULL PRIMARY KEY,
  processed_at DATETIME(6) NOT NULL
);
CREATE TABLE incidents (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  asset_id BIGINT NOT NULL,
  device_id BIGINT NULL,
  reading_id BIGINT NULL,
  source_event_id CHAR(36) NOT NULL UNIQUE,
  type VARCHAR(40) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,
  detected_at DATETIME(6) NOT NULL,
  resolved_at DATETIME(6) NULL,
  INDEX ix_incident_org (organization_id,id)
);
CREATE TABLE notifications (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  incident_id BIGINT NOT NULL,
  organization_id BIGINT NOT NULL,
  channel VARCHAR(30) NOT NULL,
  status VARCHAR(30) NOT NULL,
  deep_link VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  CONSTRAINT uk_incident_notification UNIQUE (incident_id,channel)
);
CREATE TABLE outbox_events (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  event_id CHAR(36) NOT NULL UNIQUE,
  event_type VARCHAR(100) NOT NULL,
  aggregate_id BIGINT NOT NULL,
  organization_id BIGINT NOT NULL,
  correlation_id VARCHAR(64) NULL,
  payload JSON NOT NULL,
  occurred_at DATETIME(6) NOT NULL,
  published_at DATETIME(6) NULL,
  attempts INT NOT NULL DEFAULT 0
);
