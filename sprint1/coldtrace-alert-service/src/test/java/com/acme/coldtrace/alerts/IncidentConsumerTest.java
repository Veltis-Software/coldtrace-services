package com.acme.coldtrace.alerts;

import static org.assertj.core.api.Assertions.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

@SpringBootTest(
    properties = {
      "spring.datasource.url=jdbc:h2:mem:alert;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1",
      "spring.datasource.username=sa",
      "spring.datasource.password=",
      "spring.datasource.driver-class-name=org.h2.Driver"
    })
class IncidentConsumerTest {
  @Autowired IncidentConsumer consumer;
  @Autowired JdbcTemplate jdbc;
  @Autowired ObjectMapper json;

  @BeforeEach
  void clean() {
    for (String table : List.of("notifications", "outbox_events", "incidents", "processed_events"))
      jdbc.update("DELETE FROM " + table);
  }

  private com.fasterxml.jackson.databind.JsonNode event(String type, Map<String, Object> payload) {
    return json.valueToTree(
        Map.of(
            "eventId",
            UUID.randomUUID().toString(),
            "eventType",
            type,
            "version",
            1,
            "organizationId",
            1,
            "occurredAt",
            "2026-10-09T20:00:00Z",
            "payload",
            payload));
  }

  @Test
  void duplicateDeliveryCreatesOneIncidentNotificationAndOutboxEvent() {
    var event =
        event(
            "threshold.breached",
            Map.of("assetId", 1, "readingId", 2, "iotDeviceId", 3, "severity", "WARNING"));
    consumer.accept(event);
    consumer.accept(event);
    for (String table : List.of("incidents", "notifications", "outbox_events", "processed_events"))
      assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM " + table, Long.class)).isEqualTo(1);
  }

  @Test
  void gapClosedResolvesOnlyTheSameOrganizationsAsset() {
    consumer.accept(event("source.gap", Map.of("assetId", 1, "state", "OPENED")));
    consumer.accept(event("source.gap", Map.of("assetId", 2, "state", "OPENED")));
    consumer.accept(event("source.gap", Map.of("assetId", 1, "state", "CLOSED")));
    assertThat(jdbc.queryForObject("SELECT status FROM incidents WHERE asset_id=1", String.class))
        .isEqualTo("RESOLVED");
    assertThat(jdbc.queryForObject("SELECT status FROM incidents WHERE asset_id=2", String.class))
        .isEqualTo("OPEN");
  }

  @Test
  void notificationFailureRollsBackProcessedMarkerAndIncident() {
    // A deterministic DB constraint failure after incident insertion must roll back the whole
    // operation.
    jdbc.execute("ALTER TABLE notifications ADD CONSTRAINT reject_new CHECK (organization_id<>1)");
    try {
      assertThatThrownBy(
              () ->
                  consumer.accept(
                      event("threshold.breached", Map.of("assetId", 1, "severity", "WARNING"))))
          .isInstanceOf(org.springframework.dao.DataIntegrityViolationException.class);
      assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM processed_events", Long.class)).isZero();
      assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM incidents", Long.class)).isZero();
    } finally {
      jdbc.execute("ALTER TABLE notifications DROP CONSTRAINT reject_new");
    }
  }

  @Test
  void invalidEnvelopeLeavesNoWrites() {
    assertThatThrownBy(
            () ->
                consumer.accept(
                    event("threshold.breached", Map.of("assetId", 1, "severity", "UNKNOWN"))))
        .isInstanceOf(IllegalArgumentException.class);
    assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM processed_events", Long.class)).isZero();
  }

  @Test
  void delayedCloseCannotResolveANewerGap() {
    consumer.accept(event("source.gap", Map.of("assetId", 1, "state", "OPENED")));
    var close =
        (com.fasterxml.jackson.databind.node.ObjectNode)
            event("source.gap", Map.of("assetId", 1, "state", "CLOSED"));
    close.put("occurredAt", "2026-10-09T19:59:00Z");
    consumer.accept(close);
    assertThat(jdbc.queryForObject("SELECT status FROM incidents WHERE asset_id=1", String.class))
        .isEqualTo("OPEN");
  }
}
