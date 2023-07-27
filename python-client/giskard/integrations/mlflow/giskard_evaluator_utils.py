import inspect
import re
import logging

import langchain.chains.base

from giskard import Model, Dataset, scan
from giskard.core.core import SupportedModelTypes
from giskard.core.model_validation import ValidationFlags
from giskard.models.pyfunc import PyFuncModel

logger = logging.getLogger(__name__)

gsk_model_types = {
    "classifier": SupportedModelTypes.CLASSIFICATION,
    "regressor": SupportedModelTypes.REGRESSION,
    "text": SupportedModelTypes.TEXT_GENERATION
}
alphanumeric_map = {
    ">=": "greater than or equal to",
    ">": "greater than",
    "<=": "less than or equal to",
    "<": "less than",
    "==": "equal to",
    "=": "equal to",
    "!=": "different of",
}


def unwrap_python_model_from_pyfunc(pyfunc_model):
    """
    An alternative to https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html?highlight=pyfunc#mlflow.pyfunc.PyFuncModel.unwrap_python_model
    :param pyfunc_model: the pyfunc model
    :return: unwrapped model
    """
    import importlib
    module = pyfunc_model.metadata.flavors["python_function"]["loader_module"]
    flavor = importlib.import_module(module)
    return flavor.load_model(pyfunc_model.metadata.get_model_info().model_uri)


def process_text(some_string):
    for k, v in alphanumeric_map.items():
        some_string = some_string.replace(k, v)
    some_string = some_string.replace("data slice", "data slice -")
    some_string = re.sub(r'[^A-Za-z0-9_\-. /]+', '', some_string)

    return some_string


def setup_dataset(dataset, evaluator_config):
    data = dataset.features_data.copy()
    data[dataset.targets_name] = dataset.labels_data
    dataset_config = evaluator_config.get("dataset_config", None)
    if dataset_config is None:
        return Dataset(df=data, target=dataset.targets_name, name=dataset.name)
    else:
        config_set = set(dataset_config.keys())
        sign = inspect.signature(Dataset)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            if "target" not in config_set:
                dataset_config["target"] = dataset.targets_name
            if "name" not in config_set:
                dataset_config["name"] = dataset.name

            return Dataset(df=data, **dataset_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in dataset_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.Dataset "
                             f"(see https://docs.giskard.ai/en/latest/reference/datasets).")


def setup_model(model, model_type, feature_names, evaluator_config):
    model_config = evaluator_config.get("model_config", None)

    # Special case scenario since we're currently using `rewrite_prompt` that needs access to the unwrapped model iff
    # the latter is a langchain model
    if model_type == "text":
        unwrapped_model = unwrap_python_model_from_pyfunc(model)
        if isinstance(unwrapped_model, langchain.chains.base.Chain):
            model = unwrapped_model

    if model_config is None:
        return Model(model=model,
                     model_type=gsk_model_types[model_type],
                     feature_names=feature_names)
    else:
        config_set = set(model_config.keys())
        sign = inspect.signature(Model)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            if "model_type" not in config_set:
                model_config["model_type"] = gsk_model_types[model_type]
            if "feature_names" not in config_set:
                model_config["feature_names"] = feature_names

            return Model(model=model,
                         **model_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in model_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.Model "
                             f"(see https://docs.giskard.ai/en/latest/reference/models).")


def setup_scan(giskard_model, giskard_dataset, evaluator_config):
    validation_flags = ValidationFlags()
    validation_flags.model_loading_and_saving = False

    scan_config = evaluator_config.get("scan_config", None)
    if scan_config is None:
        return scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags)
    else:
        config_set = set(scan_config.keys())
        sign = inspect.signature(scan)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            return scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags, **scan_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in scan_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.scan.")
