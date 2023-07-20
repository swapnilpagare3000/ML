package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSDatasetProcessFunctionMetaDTO implements MLWorkerWSBaseDTO {
    private String uuid;

    private String name;

    private String displayName;

    private Integer version;

    private String module;

    private String doc;

    private String moduleDoc;

    private List<MLWorkerWSTestFunctionArgumentDTO> args;

    private List<String> tags;

    private String code;

    private String type;

    private Boolean cellLevel;

    private String columnType;

    private String processType;
}
