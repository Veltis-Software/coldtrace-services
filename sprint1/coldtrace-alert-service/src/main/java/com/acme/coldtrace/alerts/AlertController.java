package com.acme.coldtrace.alerts;

import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

@RestController
public class AlertController {
  private final JdbcTemplate jdbc;
  private final RestClient identity;

  public AlertController(JdbcTemplate jdbc, @Value("${coldtrace.identity.url}") String url) {
    this.jdbc = jdbc;
    var factory =
        new org.springframework.http.client.JdkClientHttpRequestFactory(
            java.net.http.HttpClient.newBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(2))
                .build());
    factory.setReadTimeout(java.time.Duration.ofSeconds(3));
    identity = RestClient.builder().baseUrl(url).requestFactory(factory).build();
  }

  private long organization(String bearer) {
    if (bearer == null || !bearer.startsWith("Bearer "))
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED);
    try {
      var context =
          identity
              .get()
              .uri("/api/v1/session/context")
              .header("Authorization", bearer)
              .retrieve()
              .body(Session.class);
      if (context == null || context.organizationId() == null)
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED);
      return context.organizationId();
    } catch (org.springframework.web.client.HttpClientErrorException failure) {
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED);
    } catch (org.springframework.web.client.RestClientException failure) {
      throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE);
    }
  }

  public record Session(Long userId, Long organizationId) {}

  @GetMapping("/api/v1/alerts")
  public List<Map<String, Object>> list(
      @RequestHeader(value = "Authorization", required = false) String bearer) {
    return jdbc.queryForList(
        "SELECT id,asset_id,type,severity,status,detected_at FROM incidents WHERE organization_id=?"
            + " ORDER BY id DESC LIMIT 100",
        organization(bearer));
  }

  @GetMapping("/api/v1/alerts/{id}")
  public Map<String, Object> detail(
      @PathVariable long id,
      @RequestHeader(value = "Authorization", required = false) String bearer) {
    long org = organization(bearer);
    var rows =
        jdbc.queryForList("SELECT * FROM incidents WHERE id=? AND organization_id=?", id, org);
    if (rows.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
    var result = new LinkedHashMap<>(rows.get(0));
    result.put(
        "notifications",
        jdbc.queryForList(
            "SELECT channel,status,deep_link FROM notifications WHERE incident_id=? AND"
                + " organization_id=?",
            id,
            org));
    return result;
  }
}
