package com.acme.coldtrace.platform.monitoring;
import io.cucumber.spring.CucumberContextConfiguration;
import io.cucumber.java.Before;
import io.cucumber.java.en.*;
import java.util.*;
import static org.assertj.core.api.Assertions.*;
@CucumberContextConfiguration
public class TelemetrySteps extends TelemetryIntegrationTest {
  @Before public void reset() {seed();}
  @Given("a provisioned gateway and one reading") public void provisioned() {}
  @When("the gateway submits the same batch three times") public void retry() {repeatedBatchHasNoDuplicateReadingsOrEvents();}
  @Then("one reading and one outbox event are persisted") public void persisted() {assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM sensor_readings",Long.class)).isEqualTo(1);}
  @When("the gateway submits the batch with an invalid key") public void unauthorized() {wrongGatewayKeyWritesNothing();}
  @Then("the batch is rejected and no reading is persisted") public void rejected() {assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM sensor_readings",Long.class)).isZero();}
  @When("no contact is received for forty seconds") public void silent() {service.ingest(GATEWAY,UUID.randomUUID(),"local-key",List.of(reading(1,NOW,4)),"bdd");org.mockito.Mockito.when(clock.instant()).thenReturn(NOW.plusSeconds(40));gaps.detect();}
  @Then("the asset state is NO_DATA and one gap event is persisted") public void gap() {assertThat(jdbc.queryForObject("SELECT status FROM asset_current_state",String.class)).isEqualTo("NO_DATA");assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM outbox_events WHERE event_type='source.gap'",Long.class)).isEqualTo(1);}
  @When("the gateway replays an older out-of-range reading") public void replay() {replayedHistoryDoesNotRegressCurrentState();}
  @Then("the asset current state remains NORMAL") public void current() {assertThat(jdbc.queryForObject("SELECT status FROM asset_current_state",String.class)).isEqualTo("NORMAL");}
}
