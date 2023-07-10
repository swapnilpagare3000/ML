package ai.giskard.service;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.InspectionSettings;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ModelService {
    private final DatasetRepository datasetRepository;
    final FeedbackRepository feedbackRepository;
    final ModelRepository modelRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final InspectionRepository inspectionRepository;
    private final Logger log = LoggerFactory.getLogger(ModelService.class);
    private final MLWorkerService mlWorkerService;
    private final FileLocationService fileLocationService;
    private final GRPCMapper grpcMapper;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;


    public MLWorkerWSRunModelForDataFrameDTO predict(ProjectModel model, Dataset dataset, Map<String, String> features) {
        MLWorkerWSRunModelForDataFrameDTO response = null;
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            response = getRunModelForDataFrameResponse(model, dataset, features);
        }
        return response;
    }

    private MLWorkerWSRunModelForDataFrameDTO getRunModelForDataFrameResponse(ProjectModel model, Dataset dataset, Map<String, String> features) {
        MLWorkerWSRunModelForDataFrameDTO response = null;

        // Initialize the parameters and build the Data Frame
        MLWorkerWSArtifactRefDTO modelRef = new MLWorkerWSArtifactRefDTO();
        modelRef.setProjectKey(model.getProject().getKey());
        modelRef.setId(model.getId().toString());

        MLWorkerWSDataFrameDTO dataframe = new MLWorkerWSDataFrameDTO();
        ArrayList<MLWorkerWSDataRowDTO> rows = new ArrayList<>(1);
        MLWorkerWSDataRowDTO row = new MLWorkerWSDataRowDTO();
        row.setColumns(features.entrySet().stream()
            .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)));
        rows.add(row);
        dataframe.setRows(rows);

        MLWorkerWSRunModelForDataFrameParamDTO param = new MLWorkerWSRunModelForDataFrameParamDTO();
        param.setModel(modelRef);
        param.setDataframe(dataframe);

        if (dataset.getTarget() != null) {
            param.setTarget(dataset.getTarget());
        }
        if (dataset.getColumnTypes() != null) {
            param.setColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
        }
        if (dataset.getColumnDtypes() != null) {
            param.setColumnDtypes(dataset.getColumnDtypes());
        }

        // Perform the runModelForDataFrame action and parse the reply
        MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
            model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL,
            MLWorkerWSAction.runModelForDataFrame,
            param
        );
        if (result != null && result instanceof MLWorkerWSRunModelForDataFrameDTO) {
            response = (MLWorkerWSRunModelForDataFrameDTO) result;
        }
        return response;
    }

    public boolean shouldDrop(String columnDtype, String value) {
        return Objects.isNull(value) ||
            ((columnDtype.startsWith("int") || columnDtype.startsWith("float")) && Strings.isBlank(value));
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> features) {
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            ExplainRequest request = ExplainRequest.newBuilder()
                .setModel(grpcMapper.createRef(model))
                .setDataset(grpcMapper.createRef(dataset, false))
                .putAllColumns(features.entrySet().stream()
                    .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)))
                .build();

            return client.getBlockingStub().explain(request);
        }
    }

    public ExplainTextResponse explainText(ProjectModel model, Dataset dataset, InspectionSettings inspectionSettings, String featureName, Map<String, String> features) throws IOException {
        ExplainTextResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            response = client.getBlockingStub().explainText(
                ExplainTextRequest.newBuilder()
                    .setModel(grpcMapper.createRef(model))
                    .setFeatureName(featureName)
                    .putAllColumns(features)
                    .putAllColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName))
                    .setNSamples(inspectionSettings.getLimeNumberSamples())
                    .build()
            );
        }
        return response;
    }

    public Inspection createInspection(String name, UUID modelId, UUID datasetId, boolean sample) {
        log.info("Creating inspection for model {} and dataset {}", modelId, datasetId);
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());

        Inspection inspection = new Inspection();

        if (name == null || name.isEmpty())
            inspection.setName("Unnamed session");
        else
            inspection.setName(name);

        inspection.setDataset(dataset);
        inspection.setModel(model);
        inspection.setSample(sample);

        inspection = inspectionRepository.save(inspection);

        predictSerializedDataset(model, dataset, inspection.getId(), sample);
        return inspection;
    }

    protected void predictSerializedDataset(ProjectModel model, Dataset dataset, Long inspectionId, boolean sample) {
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            // Initialize params
            MLWorkerWSArtifactRefDTO modelRef = new MLWorkerWSArtifactRefDTO();
            modelRef.setId(model.getId().toString());
            modelRef.setProjectKey(model.getProject().getKey());

            MLWorkerWSArtifactRefDTO datasetRef = new MLWorkerWSArtifactRefDTO();
            datasetRef.setId(dataset.getId().toString());
            datasetRef.setProjectKey(dataset.getProject().getKey());
            datasetRef.setSample(sample);

            MLWorkerWSRunModelParamDTO param = new MLWorkerWSRunModelParamDTO();
            param.setModel(modelRef);
            param.setDataset(datasetRef);
            param.setInspectionId(inspectionId);
            param.setProjectKey(model.getProject().getKey());

            // Execute runModel action
            mlWorkerWSCommService.performAction(workerID, MLWorkerWSAction.runModel, param);
        }
    }
}
