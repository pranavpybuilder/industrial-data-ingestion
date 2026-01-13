from pathlib import Path
from typing import Dict, List

import pandas as pd

from feature_store.processors.time_aligner import TimeAligner
from feature_store.processors.cleaner import DataCleaner
from feature_store.processors.normalizer import FeatureNormalizer
from feature_store.registry.registry_manager import FeatureRegistryManager
from feature_store.validators.schema_validator import FeatureSchemaValidator
from feature_store.validators.range_validator import FeatureRangeValidator
from feature_store.builders.base_builder import BaseFeatureBuilder


class FeatureStorePipeline:
    """
    Orchestrates the end-to-end Feature Store execution:
    ingestion output → cleaning → time alignment → feature building
    → normalization → validation → persistence.
    """

    def __init__(
        self,
        time_config_path: str,
        normalization_config_path: str,
        registry_path: str,
        normalization_metadata_dir: str,
    ) -> None:
        self.time_aligner = TimeAligner(time_config_path)
        self.cleaner = DataCleaner()
        self.normalizer = FeatureNormalizer(
            normalization_config_path,
            normalization_metadata_dir,
        )
        self.registry = FeatureRegistryManager(registry_path)

    def run(
        self,
        source_data: pd.DataFrame,
        source_name: str,
        builders: List[BaseFeatureBuilder],
        schema: Dict[str, str],
        value_ranges: Dict[str, tuple],
    ) -> pd.DataFrame:
        """
        Execute the Feature Store pipeline for a given data source.
        """
        # 1. Time alignment
        aligned_df = self.time_aligner.apply_alignment(
            source_data,
            source=source_name,
        )

        # 2. Cleaning
        cleaned_df = self.cleaner.clean(aligned_df)

        # 3. Feature building
        feature_frames: List[pd.DataFrame] = []
        for builder in builders:
            features = builder.build(cleaned_df)
            feature_frames.append(features)

        if not feature_frames:
            raise RuntimeError(
                f"No features generated for source '{source_name}'."
            )

        features_df = pd.concat(feature_frames, axis=1)

        # 4. Normalization
        normalized_df = self.normalizer.normalize(features_df)

        # 5. Schema validation
        FeatureSchemaValidator(schema).validate(normalized_df)

        # 6. Range validation
        FeatureRangeValidator(value_ranges).validate(normalized_df)

        return normalized_df