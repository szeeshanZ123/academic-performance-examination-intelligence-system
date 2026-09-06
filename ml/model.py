"""
ml/model.py

Defines the Machine Learning pipeline architecture for External Examination Marks Prediction.
Combines feature preprocessing (categorical encoding) with a RandomForestRegressor.
"""

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Feature configuration
NUMERICAL_FEATURES = ["Internal", "Attendance", "Semester"]
CATEGORICAL_FEATURES = ["Subject"]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_FEATURE = "External"


def build_regression_pipeline(
    n_estimators: int = 200,
    random_state: int = 42,
) -> Pipeline:
    """
    Constructs an end-to-end scikit-learn Pipeline.

    Architecture:
    1. Preprocessing:
       - Categorical 'Subject' is one-hot encoded (handle_unknown='ignore'
         handles unseen subjects safely during inference).
       - Numerical features ('Internal', 'Attendance', 'Semester') pass through.
    2. Model:
       - RandomForestRegressor trained to predict 'External' examination marks.

    Returns:
        Pipeline: Untrained scikit-learn Pipeline object.
    """
    # ColumnTransformer applies specific transformations to feature subsets
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            (
                "num",
                "passthrough",
                NUMERICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    # RandomForestRegressor for non-linear mark prediction
    regressor = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
    )

    # Assemble into unified Pipeline
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )

    return pipeline
