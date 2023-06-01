import pytest

import giskard.ml_worker.testing.tests.statistical as statistical
from giskard.ml_worker.testing.registry.slice_function import SliceFunction


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.1, 0.20, 500),
        ("german_credit_data", "german_credit_model", 1, 0.5, 0.80, 500),
        ("enron_data", "enron_model", 0, 0.1, 0.32, 25),
    ],
)
def test_statistical(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = statistical.test_right_label(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        model=model,
        classification_label=model.meta.classification_labels[label],
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.3, 0.40, 10),
        ("german_credit_data", "german_credit_model", 1, 0.5, 0.60, 10),
        ("enron_data", "enron_model", 0, 0.01, 0.1, 10),
    ],
)
def test_statistical_filtered(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)

    results = statistical.test_right_label(
        actual_slice=data.slice(lambda df: df.head(10), row_level=False),
        model=model,
        classification_label=model.meta.classification_labels[label],
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,label,threshold,expected_metric,actual_slices_size",
    [
        ("german_credit_data", "german_credit_model", 0, 0.1, 0.34, 500),
        ("german_credit_data", "german_credit_model", 1, 0.1, 0.34, 500),
        ("enron_data", "enron_model", 0, 0.1, 0.32, 25),
    ],
)
def test_output_in_range_clf(data, model, threshold, label, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = statistical.test_output_in_range(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        model=model,
        classification_label=model.meta.classification_labels[label],
        min_range=0.3,
        max_range=0.7,
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model,threshold,expected_metric,actual_slices_size",
    [("diabetes_dataset_with_target", "linear_regression_diabetes", 0.1, 0.28, 221)],
)
def test_output_in_range_reg(data, model, threshold, expected_metric, actual_slices_size, request):
    data = request.getfixturevalue(data)
    results = statistical.test_output_in_range(
        actual_slice=data.slice(lambda df: df.head(len(df) // 2), row_level=False),
        model=request.getfixturevalue(model),
        min_range=100,
        max_range=150,
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == actual_slices_size
    assert round(results.metric, 2) == expected_metric
    assert results.passed


@pytest.mark.parametrize(
    "data,model",
    [("german_credit_data", "german_credit_model")],
)
def test_disparate_impact(data, model, request):
    data = request.getfixturevalue(data)
    model = request.getfixturevalue(model)
    results = statistical.test_disparate_impact(
        gsk_dataset=data,
        protected_slice=SliceFunction(lambda df: df[df.sex == "female"], row_level=False),
        unprotected_slice=SliceFunction(lambda df: df[df.sex == "male"], row_level=False),
        model=model,
        positive_outcome="Not default",
    )
    assert results.passed, f"DI = {results.metric}"
