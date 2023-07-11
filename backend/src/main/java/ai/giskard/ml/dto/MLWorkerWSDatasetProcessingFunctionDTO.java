package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSDatasetProcessingFunctionDTO implements MLWorkerWSBaseDTO {
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO slicingFunction;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO transformationFunction;

    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
