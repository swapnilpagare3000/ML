import csv
import os
import uuid
from logging import warning
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.settings import settings

NaN = float("NaN")

CACHE_CSV_FILENAME = "giskard-model-cache.csv"


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


class ModelCache:
    id: Optional[str] = None
    prediction_cache: Dict[str, Any] = None

    vectorized_get_cache_or_na = None

    def __init__(self, model_type: SupportedModelTypes, id: Optional[str] = None, cache_dir: Optional[Path] = None):
        self.id = id or str(uuid.uuid4())
        self.prediction_cache = dict()
        self.cache_dir = cache_dir or Path(
            settings.home_dir / settings.cache_dir / "global" / "prediction_cache" / self.id
        )
        self.cache_file = self.cache_dir / CACHE_CSV_FILENAME
        self.vectorized_get_cache_or_na = np.vectorize(self.get_cache_or_na, otypes=[object])
        self.model_type = model_type
        self._warmed_up = False

    def warm_up_from_disk(self):
        if id is None or not self.cache_file.exists():
            return

        try:
            with self.cache_file.open("r", newline="") as pred_f:
                reader = csv.reader(pred_f)
                for row in reader:
                    if self.model_type == SupportedModelTypes.TEXT_GENERATION:
                        # Text generation models output should be a single string
                        self.prediction_cache[row[0]] = row[1]
                    elif self.model_type == SupportedModelTypes.REGRESSION:
                        # Regression models output is always casted to float
                        self.prediction_cache[row[0]] = float(row[1])
                    else:
                        # Classification models return list of probabilities
                        self.prediction_cache[row[0]] = [float(i) for i in row[1:]]
        except Exception as e:
            warning(f"Failed to load cache from disk for model {self.id}: {e}")

    def get_cache_or_na(self, key: str):
        return self.prediction_cache.get(key, NaN)

    def read_from_cache(self, keys: pd.Series):
        if self.id and not self._warmed_up:
            self.warm_up_from_disk()
            self._warmed_up = True

        return pd.Series(self.vectorized_get_cache_or_na(keys), index=keys.index)

    def set_cache(self, keys: pd.Series, values: List[Any]):
        for i in range(len(keys)):
            self.prediction_cache[keys.iloc[i]] = values[i]

        if self.id:
            os.makedirs(self.cache_dir, exist_ok=True)
            with self.cache_file.open("a", newline="") as pred_f:
                writer = csv.writer(pred_f)
                for i in range(len(keys)):
                    writer.writerow(flatten([keys.iloc[i], values[i]]))

    def _to_df(self):
        index = [key for key, values in self.prediction_cache.items()]
        data = np.array([list(flatten([values])) for key, values in self.prediction_cache.items()])

        if len(data) > 0:
            return pd.DataFrame(data, index=index)
        else:
            return pd.DataFrame({})
