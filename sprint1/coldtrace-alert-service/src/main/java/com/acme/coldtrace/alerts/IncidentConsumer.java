package com.acme.coldtrace.alerts;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.acme.coldtrace.shared.EventEnvelope;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.sql.*;
import java.time.Instant;
import java.util.*;

@Service
public class IncidentConsumer {
  private final JdbcTemplate jdbc;private final ObjectMapper json;
  public IncidentConsumer(JdbcTemplate jdbc,ObjectMapper json) {this.jdbc=jdbc;this.json=json;}
  @Transactional
  public void accept(JsonNode envelope) {
    UUID event=UUID.fromString(envelope.path("eventId").asText());
    long org=envelope.path("organizationId").asLong();
    String type=envelope.path("eventType").asText();var payload=envelope.path("payload");
    Instant occurred=Instant.parse(envelope.path("occurredAt").asText());
    long asset=payload.path("assetId").asLong();
    if(envelope.path("version").asInt()!=1 || org<=0 || asset<=0 || !Set.of("threshold.breached","source.gap").contains(type)) throw new IllegalArgumentException("Unsupported event envelope");
    String severity=type.equals("source.gap")?"WARNING":payload.path("severity").asText();
    if(!Set.of("WARNING","CRITICAL").contains(severity)) throw new IllegalArgumentException("Invalid severity");
    String gap=payload.path("state").asText();
    if(type.equals("source.gap") && !Set.of("OPENED","CLOSED").contains(gap)) throw new IllegalArgumentException("Invalid gap state");
    int fresh=jdbc.update("INSERT IGNORE INTO processed_events(event_id,processed_at) VALUES (?,?)",event.toString(),Timestamp.from(Instant.now()));
    if(fresh==0) return;
    if(type.equals("source.gap") && gap.equals("CLOSED")) {
      jdbc.update("UPDATE incidents SET status='RESOLVED',resolved_at=? WHERE organization_id=? AND asset_id=? AND type='NO_DATA' AND status='OPEN' AND detected_at<=?",Timestamp.from(occurred),org,asset,Timestamp.from(occurred));
      return;
    }
    var holder=new GeneratedKeyHolder();
    jdbc.update(connection->{
      var statement=connection.prepareStatement("INSERT INTO incidents(organization_id,asset_id,device_id,reading_id,source_event_id,type,severity,status,detected_at) VALUES (?,?,?,?,?,?,?,'OPEN',?)",Statement.RETURN_GENERATED_KEYS);
      Object[] values={org,asset,payload.hasNonNull("iotDeviceId")?payload.get("iotDeviceId").asLong():null,
          payload.hasNonNull("readingId")?payload.get("readingId").asLong():null,event.toString(),type.equals("source.gap")?"NO_DATA":"THRESHOLD_BREACHED",severity,Timestamp.from(occurred)};
      for(int i=0;i<values.length;i++) statement.setObject(i+1,values[i]);return statement;
    },holder);
    long id=Objects.requireNonNull(holder.getKey()).longValue();
    // A durable in-app notification is verifiable; no email/SMS delivery is claimed.
    jdbc.update("INSERT INTO notifications(incident_id,organization_id,channel,status,deep_link,created_at) VALUES (?,?,'IN_APP','AVAILABLE',?,?)",id,org,"/alerts/"+id,Timestamp.from(Instant.now()));
    var opened=new EventEnvelope(UUID.randomUUID(),"incident.opened",1,Instant.now(),org,
        envelope.path("correlationId").asText("alert-consumer"),"alert-service",Map.of("incidentId",id,"assetId",asset,"severity",severity,"type",type.equals("source.gap")?"NO_DATA":"THRESHOLD_BREACHED"));
    try {jdbc.update("INSERT INTO outbox_events(event_id,event_type,aggregate_id,organization_id,correlation_id,payload,occurred_at) VALUES (?,?,?,?,?,?,?)",opened.eventId().toString(),opened.eventType(),id,org,opened.correlationId(),json.writeValueAsString(opened),Timestamp.from(opened.occurredAt()));}
    catch(Exception failure) {throw new IllegalStateException("Cannot persist incident event",failure);}
  }
}
