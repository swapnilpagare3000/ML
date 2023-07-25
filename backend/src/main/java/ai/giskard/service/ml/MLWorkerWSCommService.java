package ai.giskard.service.ml;

import ai.giskard.config.WebSocketConfig;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerReplyMessage;
import ai.giskard.ml.MLWorkerReplyType;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
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

    public void notifyMaxReplyPayloadLength(MLWorkerID workerID, int maxPayloadLength) {
        // Prepare the parameters and publish message
        HashMap<String, Object> data = new HashMap<>();
        data.put("config", "MAX_STOMP_ML_WORKER_REPLY_SIZE");
        data.put("value", maxPayloadLength);
        simpMessagingTemplate.convertAndSend(
            String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, workerID.toString(), WebSocketConfig.ML_WORKER_CONFIG_TOPIC),
            data
        );
    }

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param)
            throws NullPointerException, JsonProcessingException {
        // Wait for result during 5 seconds/5000 milliseconds
        return this.performAction(workerID, action, param, 5000);
    }

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds)
            throws NullPointerException, JsonProcessingException {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.getResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        String result = awaitReply(repId, milliseconds);

        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);
            throw new NullPointerException("Received an empty reply for " + action);
        }

        try {
            return parseReplyDTO(action, result);
        } catch (JsonProcessingException e) {
            // Parse error information
            log.warn("Deserialization failed: {}", e.getMessage());
            ObjectMapper objectMapper = new ObjectMapper();
            MLWorkerWSErrorDTO error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
            log.warn("Parsed error: {}", error.getErrorStr());
            throw new NullPointerException(error.getErrorStr());
        }
    }

    public UUID triggerAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.getResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        return repId;
    }

    private void send(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, UUID repId) {
        HashMap<String, Object> data = new HashMap<>();
        data.put("action", action.toString());
        data.put("id", repId.toString());
        data.put("param", param);
        simpMessagingTemplate.convertAndSend(
            String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, workerID.toString(), WebSocketConfig.ML_WORKER_ACTION_TOPIC),
            data
        );
    }

    public boolean isActionFinished(UUID uuid) {
        BlockingQueue<MLWorkerReplyMessage> bq = mlWorkerWSService.getResultWaiter(uuid.toString());
        if (!bq.isEmpty()) {
            MLWorkerReplyMessage message = bq.peek();
            return message.getType() == MLWorkerReplyType.FINISH && message.getMessage() != null;
        }
        return false;
    }

    public MLWorkerWSBaseDTO getFinalReply(UUID uuid, MLWorkerWSAction action) {
        BlockingQueue<MLWorkerReplyMessage> bq = mlWorkerWSService.getResultWaiter(uuid.toString());
        if (!bq.isEmpty()) {
            MLWorkerReplyMessage message = bq.peek();
            if (message.getType() == MLWorkerReplyType.FINISH) {
                String result = message.getMessage();
                ObjectMapper objectMapper = new ObjectMapper();
                try {
                    return parseReplyDTO(action, result);
                } catch (JsonProcessingException e) {
                    // Parse error information
                    log.warn("Deserialization failed: {}", e.getMessage());
                    MLWorkerWSErrorDTO error = null;
                    try {
                        error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
                    } catch (JsonProcessingException ex) {
                        return null;
                    }
                    log.warn("Parsed error: {}", error.getErrorStr());
                    return error;
                }
            }
        }
        return null;
    }

    public MLWorkerWSBaseDTO parseReplyDTO(MLWorkerWSAction action, String result) throws JsonProcessingException {
        ObjectMapper objectMapper = new ObjectMapper();
        return switch (action) {
            case getInfo -> objectMapper.readValue(result, MLWorkerWSGetInfoDTO.class);
            case runAdHocTest -> objectMapper.readValue(result, MLWorkerWSRunAdHocTestDTO.class);
            case datasetProcessing -> objectMapper.readValue(result, MLWorkerWSDatasetProcessingDTO.class);
            case runTestSuite -> objectMapper.readValue(result, MLWorkerWSTestSuiteDTO.class);
            case runModel, stopWorker, generateQueryBasedSlicingFunction -> null;
            case runModelForDataFrame -> objectMapper.readValue(result, MLWorkerWSRunModelForDataFrameDTO.class);
            case explain -> objectMapper.readValue(result, MLWorkerWSExplainDTO.class);
            case explainText -> objectMapper.readValue(result, MLWorkerWSExplainTextDTO.class);
            case echo -> objectMapper.readValue(result, MLWorkerWSEchoMsgDTO.class);
            case generateTestSuite -> objectMapper.readValue(result, MLWorkerWSGenerateTestSuiteDTO.class);
            case getCatalog -> objectMapper.readValue(result, MLWorkerWSCatalogDTO.class);
        };
    }

    public String awaitReply(UUID repId, long milliseconds) {
        String result = null;
        BlockingQueue<MLWorkerReplyMessage> queue = mlWorkerWSService.getResultWaiter(repId.toString());
        try {
            // Waiting for the result
            MLWorkerReplyMessage message = queue.poll(milliseconds, TimeUnit.MILLISECONDS);
            if (message == null) result = null;
            else {
                if (message.getType() == MLWorkerReplyType.FINISH) {
                    result = message.getMessage();
                }
            }
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            Thread.currentThread().interrupt();
        }
        return result;
    }

    public String blockAwaitReply(UUID repId) {
        String result = null;
        BlockingQueue<MLWorkerReplyMessage> queue = mlWorkerWSService.getResultWaiter(repId.toString());
        try {
            // Waiting for the result
            MLWorkerReplyMessage message = queue.take();
            if (message == null) result = null;
            else {
                if (message.getType() == MLWorkerReplyType.FINISH) {
                    result = message.getMessage();
                }
            }
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            Thread.currentThread().interrupt();
        }
        return result;
    }
}
