import pytest

from giskard.testing import test_overconfidence_rate, test_underconfidence_rate


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_confidence(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)

    result_overconfidence = test_overconfidence_rate(model=model, dataset=dataset, threshold=0).execute()
    overconfidence_predictions = model.predict(
        dataset.slice(lambda x: x.loc[result_overconfidence.failed_indexes[str(dataset.original_id)]], row_level=False)
    )

    rest_dataset_overconfidence = dataset.copy()
    rest_dataset_overconfidence.df = rest_dataset_overconfidence.df.drop(
        result_overconfidence.failed_indexes[str(dataset.original_id)]
    )
    rest_predictions_overconfidence = model.predict(rest_dataset_overconfidence)

    assert len(result_overconfidence.failed_indexes[str(dataset.original_id)]) == 59
    assert min(overconfidence_predictions.probabilities) > min(rest_predictions_overconfidence.probabilities)

    result_underconfidence = test_underconfidence_rate(model=model, dataset=dataset, threshold=0, debug=True).execute()
    underconfidence_predictions = model.predict(
        dataset.slice(lambda x: x.loc[result_underconfidence.failed_indexes[str(dataset.original_id)]], row_level=False)
    )

    rest_dataset_underconfidence = dataset.copy()
    rest_dataset_underconfidence.df = rest_dataset_underconfidence.df.drop(
        result_underconfidence.failed_indexes[str(dataset.original_id)]
    )
    rest_predictions_underconfidence = model.predict(rest_dataset_underconfidence)

    assert len(result_underconfidence.failed_indexes[str(dataset.original_id)]) == 45
    assert 0.45 < underconfidence_predictions.probabilities.mean()
    assert 0.55 > underconfidence_predictions.probabilities.mean()
    assert max(underconfidence_predictions.probabilities) < min(rest_predictions_underconfidence.probabilities)

    assert (
        not test_underconfidence_rate(model=model, dataset=rest_dataset_overconfidence, threshold=0, debug=True)
        .execute()
        .passed
    )

    assert (
        not test_overconfidence_rate(model=model, dataset=rest_dataset_underconfidence, threshold=0, debug=True)
        .execute()
        .passed
    )
