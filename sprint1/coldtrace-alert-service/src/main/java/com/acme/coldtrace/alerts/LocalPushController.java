package com.acme.coldtrace.alerts;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Base64;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

/** Explicit opt-in emulator endpoint. Do not enable on a public cloud service. */
@RestController
@ConditionalOnProperty(name = "coldtrace.pubsub.local-push-enabled", havingValue = "true")
public class LocalPushController {
  private final IncidentConsumer consumer;
  private final ObjectMapper json;

  public LocalPushController(IncidentConsumer consumer, ObjectMapper json) {
    this.consumer = consumer;
    this.json = json;
  }

  public record Message(String data) {}

  public record Push(Message message) {}

  @PostMapping("/internal/pubsub/events")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void receive(@RequestBody Push push) throws Exception {
    consumer.accept(json.readTree(Base64.getDecoder().decode(push.message().data())));
  }
}
