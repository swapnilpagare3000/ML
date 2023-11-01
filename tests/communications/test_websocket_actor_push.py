import uuid
import pytest

from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.websocket import listener
from giskard.models.base.model import BaseModel

from tests import utils
from tests.test_push import EXPECTED_COUNTS


# For each kind
EXPECTED_COUNTS_GERMAN_CREDIT_PUSH_KIND_SAMPLE_INDEX = [
    ("contribution", 3),
    ("overconfidence", 17),
    ("perturbation", 35),
    ("borderline", 31),
]


@pytest.mark.parametrize("model,data", [
    ("hotel_text_model", "hotel_text_data"),
    ("enron_model", "enron_data"),
])
def test_websocket_actor_get_push_do_nothing(model, data, request):
    model: BaseModel = request.getfixturevalue(model)
    dataset: Dataset = request.getfixturevalue(data)

    project_key = str(uuid.uuid4())
    with utils.MockedClient(mock_all=False) as (client, mr), utils.MockedProjectCacheDir(project_key):
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

        # Pick the first row
        first_row = dataset.df.iloc[0]
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in first_row.items()
                }),
            ],
        )

        params = websocket.GetPushParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
            push_kind=None,
            cta_kind=None,
            rowIdx=0,
        )
        reply = listener.get_push(client=client, params=params)
        assert isinstance(reply, websocket.GetPushResponse)
        assert not reply.action


@pytest.mark.parametrize("cta_kind",[
    kind for kind in websocket.CallToActionKind
])
def test_websocket_actor_get_push_no_push_kind(cta_kind, request):
    model: BaseModel = request.getfixturevalue("enron_model")
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4())
    with utils.MockedClient(mock_all=False) as (client, mr), utils.MockedProjectCacheDir(project_key):
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

        # Pick the first row
        first_row = dataset.df.iloc[0]
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in first_row.items()
                }),
            ],
        )

        params = websocket.GetPushParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
            push_kind=None,
            cta_kind=cta_kind,
            rowIdx=0,
        )
        reply = listener.get_push(client=client, params=params)
        assert isinstance(reply, websocket.GetPushResponse)
        assert not reply.action


@pytest.mark.parametrize("push_kind",[
    kind for kind in websocket.PushKind
])
def test_websocket_actor_get_push_no_cta_kind(push_kind, request):
    model: BaseModel = request.getfixturevalue("enron_model")
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4())
    with utils.MockedClient(mock_all=False) as (client, mr), utils.MockedProjectCacheDir(project_key):
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

        # Pick the first row
        first_row = dataset.df.iloc[0]
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in first_row.items()
                }),
            ],
        )

        params = websocket.GetPushParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
            push_kind=push_kind,
            cta_kind=None,
            rowIdx=0,
        )
        reply = listener.get_push(client=client, params=params)
        assert isinstance(reply, websocket.GetPushResponse)
        assert not reply.action


@pytest.mark.parametrize("cta_kind",[
    kind for kind in websocket.CallToActionKind
])
def test_websocket_actor_get_push_invalid_push_kind(cta_kind, request):
    model: BaseModel = request.getfixturevalue("enron_model")
    dataset: Dataset = request.getfixturevalue("enron_data")

    project_key = str(uuid.uuid4())
    with utils.MockedClient(mock_all=False) as (client, mr), utils.MockedProjectCacheDir(project_key):
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

        # Pick the first row
        first_row = dataset.df.iloc[0]
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in first_row.items()
                }),
            ],
        )

        params = websocket.GetPushParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
            push_kind=websocket.PushKind.INVALID,
            cta_kind=cta_kind,
            rowIdx=0,
        )
        with pytest.raises(ValueError):
            listener.get_push(client=client, params=params)


@pytest.mark.parametrize("kind,row", EXPECTED_COUNTS_GERMAN_CREDIT_PUSH_KIND_SAMPLE_INDEX)
def test_websocket_actor_get_push_no_action(kind, row, german_credit_model, german_credit_data):
    assert EXPECTED_COUNTS["german_credit_model"][kind][row] != 0
    push_kind = websocket.PushKind[kind.upper()]

    model = german_credit_model
    dataset = german_credit_data

    project_key = str(uuid.uuid4())
    with utils.MockedClient(mock_all=False) as (client, mr), utils.MockedProjectCacheDir(project_key):
        utils.local_save_model_under_giskard_home_cache(model, project_key)
        utils.local_save_dataset_under_giskard_home_cache(dataset, project_key)

        utils.register_uri_for_model_meta_info(mr, model, project_key)
        utils.register_uri_for_dataset_meta_info(mr, dataset, project_key)

        # Pick the given row
        given_row = dataset.df.iloc[row]
        dataframe = websocket.DataFrame(
            rows=[
                websocket.DataRow(columns={
                    str(k): str(v) for k, v in given_row.items()
                }),
            ],
        )

        params = websocket.GetPushParam(
            model=websocket.ArtifactRef(project_key=project_key, id=str(model.id)),
            dataset=websocket.ArtifactRef(project_key=project_key, id=str(dataset.id)),
            dataframe=dataframe,
            target=dataset.target,
            column_types=dataset.column_types,
            column_dtypes=dataset.column_dtypes,
            push_kind=push_kind,
            cta_kind=websocket.CallToActionKind.NONE,
            rowIdx=row,
        )
        reply = listener.get_push(client=client, params=params)
        assert isinstance(reply, websocket.GetPushResponse)
        assert reply.__dict__[kind] # The given push should not be `None`
        assert not reply.action
