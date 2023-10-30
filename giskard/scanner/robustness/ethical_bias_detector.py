from typing import Sequence

from .base_detector import BaseTextPerturbationDetector
from .text_transformations import TextTransformation
from ..decorators import detector
from ..issues import Ethical
from ...datasets.base import Dataset
from ...models.base import BaseModel


@detector(
    name="ethical_bias",
    tags=["ethical_bias", "robustness", "classification", "regression"],
)
class EthicalBiasDetector(BaseTextPerturbationDetector):
    _issue_group = Ethical

    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        from .text_transformations import (
            TextGenderTransformation,
            TextNationalityTransformation,
            TextReligionTransformation,
        )

        return [
            TextGenderTransformation,
            TextReligionTransformation,
            TextNationalityTransformation,
        ]
