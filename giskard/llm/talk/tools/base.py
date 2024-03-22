from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from abc import ABC, abstractmethod

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

if TYPE_CHECKING:
    from giskard.datasets.base import Dataset
    from giskard.models.base import BaseModel
    from giskard.scanner.report import ScanReport


class BaseTool(ABC):
    """Base class of the Tool object.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = ...
    default_description: str = ...

    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        scan_report: Optional[ScanReport] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Constructor of the class.

        Parameters
        ----------
        model : BaseModel
            The Giskard Model.
        dataset : Dataset
            The Giskard Dataset.
        scan_report : ScanReport, optional
            The Giskard ScanReport object.
        name : str, optional
            The name of the Tool. If not set, the `default_name` is used.
        description : str, optional
            The description of the Tool. If not set, the `default_description` is used.
        """
        self._model = model
        self._dataset = dataset
        self._scan_report = scan_report

        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        """Return the name of the Tool.

        Returns
        -------
        str
            The name of the Tool.
        """
        return self._name

    @property
    def description(self) -> str:
        """Return the description of the Tool.

        Returns
        -------
        str
            The description of the Tool.
        """
        return self._description

    @property
    @abstractmethod
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        """Execute the Tool's functionality.

        Returns
        -------
        str
            The result of the Tool's execution.
        """
        ...


def get_feature_json_type(df: pd.DataFrame) -> dict[str, str]:
    """Get features' JSON type.

    Determine the JSON type of features from the given `dataset`.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe with data.

    Returns
    -------
    dict[str, str]
        The dictionary with columns and related JSON types.
    """
    feature_json_type = dict()

    for col in df:
        if is_bool_dtype(df[col]):
            feature_json_type[col] = "boolean"
        elif is_numeric_dtype(df[col]):
            feature_json_type[col] = "number"
        else:
            # String, datetime and category.
            feature_json_type[col] = "string"

    return feature_json_type
