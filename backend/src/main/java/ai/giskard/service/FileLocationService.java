package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.nio.file.Paths;

@Service
@RequiredArgsConstructor
public class FileLocationService {
    private final ApplicationProperties applicationProperties;

    public Path modelsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("models");
    }

    public static Path projectHome(String projectKey) {
        return Paths.get("projects", projectKey);
    }

    public Path datasetsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("datasets");
    }

    public Path resolvedDatasetPath(Dataset dataset) {
        return resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());
    }

    public Path resolvedDatasetPath(String projectKey, String datasetId) {
        return datasetsDirectory(projectKey).resolve(datasetId);
    }

    public Path resolvedModelPath(ProjectModel model) {
        return resolvedModelPath(model.getProject().getKey(), model.getId());
    }

    public Path resolvedModelPath(String projectKey, String modelId) {
        return modelsDirectory(projectKey).resolve(modelId);
    }

    public Path resolvedInspectionPath(String projectKey, Long inspectionId) {
        return modelsDirectory(projectKey).resolve(Paths.get("inspections", inspectionId.toString()));
    }

    public Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
    }

    public Path giskardHome() {
        return applicationProperties.getHome();
    }
}
