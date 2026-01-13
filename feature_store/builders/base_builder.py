from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd


class BaseFeatureBuilder(ABC):
    """
    Abstract base class for all feature builders.

    Each feature builder is responsible for converting cleaned and
    time-aligned source data into semantically meaningful features
    for a specific entity.
    """

    def __init__(self, config: Dict) -> None:
        self.config = config

    @abstractmethod
    def build(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Build features from the input DataFrame.

        Parameters:
        - df: Cleaned and time-aligned source DataFrame

        Returns:
        - DataFrame containing derived and/or aggregated features
        """
        raise NotImplementedError("Feature builders must implement build()")

    @abstractmethod
    def entity(self) -> str:
        """
        Return the entity name this builder produces features for.

        Example: 'machine', 'operator', 'order'
        """
        raise NotImplementedError("Feature builders must define entity()")

    @abstractmethod
    def source(self) -> str:
        """
        Return the source system name.

        Example: 'sap', 'rfid', 'plc', 'excel'
        """
        raise NotImplementedError("Feature builders must define source()")