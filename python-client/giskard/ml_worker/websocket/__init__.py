from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class WorkerReply(BaseModel):
    pass


class Empty(WorkerReply):
    pass


class ArtifactRef(BaseModel):
    project_key: str
    id: str
    sample: Optional[bool] = None


class TestFunctionArgument(BaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


class FunctionMeta(BaseModel):
    uuid: str
    name: str
    displayName: str
    version: Optional[int] = None
    module: str
    doc: str
    moduleDoc: Optional[str] = None
    args: List[TestFunctionArgument]
    tags: List[str]
    code: str
    type: str


class DatasetProcessFunctionMeta(BaseModel):
    uuid: str
    name: str
    displayName: str
    version: Optional[int] = None  # For backward compatibility
    module: str
    doc: Optional[str] = None
    moduleDoc: Optional[str] = None
    args: List[TestFunctionArgument]
    tags: List[str]
    code: str
    type: str
    cellLevel: bool
    columnType: Optional[str] = None
    processType: str


class Catalog(WorkerReply):
    tests: Dict[str, FunctionMeta]
    slices: Dict[str, DatasetProcessFunctionMeta]
    transformations: Dict[str, DatasetProcessFunctionMeta]


class DataRow(BaseModel):
    columns: Dict[str, str]


class DataFrame(BaseModel):
    rows: List[DataRow]


class DatasetRowModificationResult(BaseModel):
    rowId: int
    modifications: Dict[str, str]


class DatasetProcessing(WorkerReply):
    datasetId: str
    totalRows: int
    filteredRows: List[int]
    modifications: List[DatasetRowModificationResult]


class FuncArgument(BaseModel):
    name: str
    model: Optional[ArtifactRef] = None
    dataset: Optional[ArtifactRef] = None
    float_arg: Optional[float] = Field(None, alias="float")
    int_arg: Optional[int] = Field(None, alias="int")
    str_arg: Optional[str] = Field(None, alias="str")
    bool_arg: Optional[bool] = Field(None, alias="bool")
    slicingFunction: Optional[ArtifactRef] = None
    transformationFunction: Optional[ArtifactRef] = None
    kwargs: Optional[str] = None
    args: Optional[List["FuncArgument"]] = None
    is_none: bool = Field(..., alias="none")


class DatasetProcessingFunction(BaseModel):
    slicingFunction: Optional[ArtifactRef] = None
    transformationFunction: Optional[ArtifactRef] = None
    arguments: List[FuncArgument]


class DatesetProcessingParam(BaseModel):
    dataset: ArtifactRef
    functions: List[DatasetProcessingFunction]


class EchoMsg(WorkerReply):
    msg: str


class Explanation(BaseModel):
    per_feature: Dict[str, float]


class Explain(WorkerReply):
    explanations: Dict[str, Explanation]


class ExplainParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    columns: Dict[str, str]


class WeightsPerFeature(BaseModel):
    weights: List[float]


class ExplainText(WorkerReply):
    words: List[str]
    weights: Dict[str, WeightsPerFeature]


class ExplainTextParam(BaseModel):
    model: ArtifactRef
    feature_name: str
    columns: Dict[str, str]
    column_types: Dict[str, str]
    n_samples: int


class GeneratedTestInput(BaseModel):
    name: str
    value: str
    is_alias: bool


class GeneratedTestSuite(BaseModel):
    test_uuid: str
    inputs: List[GeneratedTestInput]


class GenerateTestSuite(WorkerReply):
    tests: List[GeneratedTestSuite]


class ModelMeta(BaseModel):
    model_type: Optional[str] = None


class DatasetMeta(BaseModel):
    target: Optional[str] = None


class SuiteInput(BaseModel):
    name: str
    type: str
    modelMeta: Optional[ModelMeta] = None
    datasetMeta: Optional[DatasetMeta] = None


class GenerateTestSuiteParam(BaseModel):
    project_key: str
    inputs: List[SuiteInput]


class Platform(BaseModel):
    machine: str
    node: str
    processor: str
    release: str
    system: str
    version: str


class GetInfo(WorkerReply):
    platform: Platform
    interpreter: str
    interpreterVersion: str
    installedPackages: Dict[str, str]
    internalGrpcAddress: str
    isRemote: bool
    pid: int
    processStartTime: int
    giskardClientVersion: str


class GetInfoParam(BaseModel):
    list_packages: bool


class TestMessageType(Enum):
    ERROR = 1
    INFO = 2


class TestMessage(BaseModel):
    type: TestMessageType
    text: str


class PartialUnexpectedCounts(BaseModel):
    value: List[int]
    count: int


class SingleTestResult(BaseModel):
    passed: bool
    is_error: Optional[bool] = None
    messages: Optional[List[TestMessage]] = None
    props: Optional[Dict[str, str]] = None
    metric: Optional[float] = None
    missing_count: Optional[int] = None
    missing_percent: Optional[float] = None
    unexpected_count: Optional[int] = None
    unexpected_percent: Optional[float] = None
    unexpected_percent_total: Optional[float] = None
    unexpected_percent_nonmissing: Optional[float] = None
    partial_unexpected_index_list: Optional[List[int]] = None
    partial_unexpected_counts: Optional[List[PartialUnexpectedCounts]] = None
    unexpected_index_list: Optional[List[int]] = None
    output_df: Optional[bytes] = None
    number_of_perturbed_rows: Optional[int] = None
    actual_slices_size: Optional[List[int]] = None
    reference_slices_size: Optional[List[int]] = None


class IdentifierSingleTestResult(BaseModel):
    id: int
    result: SingleTestResult


class NamedSingleTestResult(BaseModel):
    testUuid: str
    result: SingleTestResult


class RunAdHocTest(WorkerReply):
    results: List[NamedSingleTestResult]


class RunAdHocTestParam(BaseModel):
    testUuid: str
    arguments: List[FuncArgument]


class RunModelForDataFrame(WorkerReply):
    all_predictions: Optional[DataFrame] = None
    prediction: List[str]
    probabilities: Optional[List[float]] = None
    raw_prediction: Optional[List[float]] = None


class RunModelForDataFrameParam(BaseModel):
    model: ArtifactRef
    dataframe: DataFrame
    target: str
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]


class RunModelParam(BaseModel):
    model: ArtifactRef
    dataset: ArtifactRef
    inspectionId: int
    project_key: str


class SuiteTestArgument(BaseModel):
    id: int
    testUuid: str
    arguments: List[FuncArgument]


class TestFunctionArgument(BaseModel):
    name: str
    type: str
    optional: bool
    default: str
    argOrder: int


class TestSuite(WorkerReply):
    is_error: bool
    is_pass: bool
    results: IdentifierSingleTestResult
    logs: str


class TestSuiteParam(BaseModel):
    tests: List[SuiteTestArgument]
    globalArguments: List[FuncArgument]
