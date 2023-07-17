package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class MLWorkerWSCommService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSCommService.class.getName());

    private final MLWorkerWSService mlWorkerWSService;

    private final SimpMessagingTemplate simpMessagingTemplate;

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        // Wait for result during 5 seconds/5000 milliseconds
        return this.performAction(workerID, action, param, 5000);
    }

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds) {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        BlockingQueue<String> queue = mlWorkerWSService.getResultWaiter(repId.toString(), true);

        // Prepare the parameters and publish message
        HashMap<String, Object> data = new HashMap<>();
        data.put("action", action.toString());
        data.put("id", repId.toString());
        data.put("param", param);
        simpMessagingTemplate.convertAndSend("/ml-worker/" + workerID + "/action", data);

        String result = null;
        try {
            // Waiting for the result
            result = queue.poll(milliseconds, TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
        }

        try {
            if (result == null) {
                mlWorkerWSService.removeResultWaiter(repId.toString());
                log.warn("Received an empty reply for " + repId);
                return null;
            }

            ObjectMapper objectMapper = new ObjectMapper();
            return switch (action) {
                case getInfo -> objectMapper.readValue(result, MLWorkerWSGetInfoDTO.class);
                case runAdHocTest -> objectMapper.readValue(result, MLWorkerWSRunAdHocTestDTO.class);
                case datasetProcessing -> objectMapper.readValue(result, MLWorkerWSDatasetProcessingDTO.class);
                case runTestSuite -> objectMapper.readValue(result, MLWorkerWSTestSuiteDTO.class);
                case runModel -> null;
                case runModelForDataFrame -> objectMapper.readValue(result, MLWorkerWSRunModelForDataFrameDTO.class);
                case explain -> objectMapper.readValue(result, MLWorkerWSExplainDTO.class);
                case explainText -> objectMapper.readValue(result, MLWorkerWSExplainTextDTO.class);
                case echo -> objectMapper.readValue(result, MLWorkerWSEchoMsgDTO.class);
                case generateTestSuite -> objectMapper.readValue(result, MLWorkerWSGenerateTestSuiteDTO.class);
                case stopWorker -> null;
                case getCatalog -> objectMapper.readValue(result, MLWorkerWSCatalogDTO.class);
                case generateQueryBasedSlicingFunction -> null;
            };
        } catch (JsonMappingException e) {
            log.warn("Unable to deserialize result from ML Worker during mapping");
        } catch (JsonProcessingException e) {
            log.warn("Unable to deserialize result from ML Worker during processing");
        }

        // Parse error
        try {
            if (result != null) {
                ObjectMapper objectMapper = new ObjectMapper();
                MLWorkerWSErrorDTO error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
                log.warn(error.getErrorStr());
                // TODO: Pass it to the frontend
            }
        } catch (JsonMappingException e) {
            log.warn("Unable to deserialize result from ML Worker during mapping");
        } catch (JsonProcessingException e) {
            log.warn("Unable to deserialize result from ML Worker during processing");
        }
        return null;
    }
}
