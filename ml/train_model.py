"""
ml/train_model.py

Trains and evaluates the External Examination Marks prediction model.
Phase 10.1: Academic Performance and Examination Intelligence System.

Workflow:
1. Load marks.csv and attendance.csv.
2. Merge datasets on [Roll_No, Semester, Subject].
3. Clean and validate features (strictly excluding Total, Grade, SGPI to prevent data leakage).
4. Perform Train/Test split (80/20).
5. Inspect & report student overlap limitation.
6. Train RandomForestRegressor with OneHotEncoder pipeline.
7. Evaluate using MAE, RMSE, and R2 score.
8. Save trained pipeline to ml/models/external_marks_model.joblib.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from ml.model import ALL_FEATURES, NUMERICAL_FEATURES, TARGET_FEATURE, build_regression_pipeline
except ImportError:
    from model import ALL_FEATURES, NUMERICAL_FEATURES, TARGET_FEATURE, build_regression_pipeline

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "ml" / "models"
MODEL_SAVE_PATH = MODELS_DIR / "external_marks_model.joblib"


def load_and_merge_data() -> pd.DataFrame:
    """
    Loads marks.csv and attendance.csv, then merges them on
    ['Roll_No', 'Semester', 'Subject'].
    """
    marks_file = DATA_DIR / "marks.csv"
    attendance_file = DATA_DIR / "attendance.csv"

    if not marks_file.exists():
        raise FileNotFoundError(f"Marks file not found at: {marks_file}")
    if not attendance_file.exists():
        raise FileNotFoundError(f"Attendance file not found at: {attendance_file}")

    print(f"Loading marks from: {marks_file}")
    marks_df = pd.read_csv(marks_file)

    print(f"Loading attendance from: {attendance_file}")
    attendance_df = pd.read_csv(attendance_file)

    # Merge on natural primary composite key
    merged_df = pd.merge(
        marks_df,
        attendance_df,
        on=["Roll_No", "Semester", "Subject"],
        how="inner",
    )

    return merged_df


def prepare_ml_dataset(df: pd.DataFrame):
    """
    Cleans dataset, enforces data types, and separates feature matrix X and target y.
    Strictly avoids data leakage by excluding Total, Grade, and SGPI.
    """
    required_cols = ["Roll_No"] + ALL_FEATURES + [TARGET_FEATURE]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Select only required columns and drop any null/NaN rows
    ml_df = df[required_cols].dropna().copy()

    # Ensure numeric types
    for num_col in NUMERICAL_FEATURES + [TARGET_FEATURE]:
        ml_df[num_col] = pd.to_numeric(ml_df[num_col], errors="coerce")

    # Drop any rows that failed conversion
    ml_df = ml_df.dropna().reset_index(drop=True)

    # Dataset profile
    total_usable = len(ml_df)
    unique_students = ml_df["Roll_No"].nunique()
    unique_subjects = ml_df["Subject"].nunique()
    unique_semesters = ml_df["Semester"].nunique()

    print("\n" + "=" * 50)
    print("DATASET PROFILE")
    print("=" * 50)
    print(f"Number of usable records : {total_usable}")
    print(f"Feature columns          : {ALL_FEATURES}")
    print(f"Target column            : {TARGET_FEATURE}")
    print(f"Number of unique students: {unique_students}")
    print(f"Number of unique subjects: {unique_subjects}")
    print(f"Number of semesters      : {unique_semesters}")
    print("=" * 50 + "\n")

    X = ml_df[ALL_FEATURES]
    y = ml_df[TARGET_FEATURE]
    student_ids = ml_df["Roll_No"]

    return X, y, student_ids


def train_and_evaluate():
    """
    Executes the training and evaluation workflow.
    """
    # 1. Load and merge datasets
    raw_df = load_and_merge_data()

    # 2. Extract features and target
    X, y, student_ids = prepare_ml_dataset(raw_df)

    # 3. Train/Test split
    # An 80/20 train/test split evaluates the model's ability to generalize to unseen test instances.
    # We use random_state=42 for deterministic and reproducible evaluation.
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X,
        y,
        student_ids,
        test_size=0.20,
        random_state=42,
    )

    # Inspect student overlap between train and test sets
    train_students = set(id_train)
    test_students = set(id_test)
    overlap_students = train_students.intersection(test_students)

    print("TRAIN / TEST SPLIT SUMMARY:")
    print(f"  - Training records: {len(X_train)} (80%)")
    print(f"  - Testing records : {len(X_test)} (20%)")
    print("\n[DATASET CHARACTERISTIC / LIMITATION REPORT]")
    print(
        f"  - Unique students in Training set: {len(train_students)}\n"
        f"  - Unique students in Testing set : {len(test_students)}\n"
        f"  - Students appearing in BOTH sets: {len(overlap_students)}\n"
        f"  * Note: Because each student possesses multiple subject/semester records,\n"
        f"    random row-level splitting distributes subject records of the same student\n"
        f"    across both train and test partitions. This baseline model evaluates\n"
        f"    subject-level mark prediction given prior internal marks and attendance."
    )
    print("-" * 50)

    # Leakage Check Assertion
    for forbidden in ["Total", "Grade", "SGPI", "Attendance_Status", "Academic_Risk"]:
        assert forbidden not in X.columns, f"Data leakage detected! '{forbidden}' found in feature matrix."
    assert y.name == TARGET_FEATURE, f"Target must be {TARGET_FEATURE}, got {y.name}"

    # 4. Build and train model pipeline
    print("\nTraining RandomForestRegressor model (n_estimators=200, random_state=42)...")
    pipeline = build_regression_pipeline(n_estimators=200, random_state=42)
    pipeline.fit(X_train, y_train)
    print("Model training completed successfully.")

    # 5. Baseline Model Comparison (Predicting training set mean)
    train_mean_external = y_train.mean()
    baseline_predictions = np.full_like(y_test, fill_value=train_mean_external)
    baseline_mae = mean_absolute_error(y_test, baseline_predictions)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_predictions))

    # Evaluate ML model
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    mae_improvement_pct = ((baseline_mae - mae) / baseline_mae) * 100

    print("\n" + "=" * 50)
    print("ML MODEL PERFORMANCE — UPDATED DATASET")
    print("=" * 50)
    print(f"Total Records   : {len(X)}")
    print(f"Training Records: {len(X_train)} (80%)")
    print(f"Testing Records : {len(X_test)} (20%)")
    print(f"\nFeatures        : {ALL_FEATURES}")
    print(f"Target          : {TARGET_FEATURE}")
    print(f"Model           : RandomForestRegressor (n_estimators=200, random_state=42)")
    print("-" * 50)
    print(f"Mean External Mark (Train Set): {train_mean_external:.2f}")
    print(f"Baseline MAE (Mean Predictor) : {baseline_mae:.4f}")
    print(f"ML Model MAE (Random Forest)  : {mae:.4f}")
    print(f"RMSE                          : {rmse:.4f}")
    print(f"R² Score                      : {r2:.4f}")
    print(f"MAE Error Reduction vs Baseline: {mae_improvement_pct:.2f}%")
    print("=" * 50)

    # 6. Model Comparison (Old vs New Dataset)
    print("\n" + "=" * 60)
    print("MODEL COMPARISON (OLD DATASET vs NEW LONGITUDINAL DATASET)")
    print("=" * 60)
    print(f"{'Metric':<18} | {'Old Model (1,440 records)':<26} | {'New Model (5,040 records)':<26}")
    print("-" * 60)
    print(f"{'Total Records':<18} | {'1,440':<26} | {len(X):<26}")
    print(f"{'Train / Test':<18} | {'1,152 / 288':<26} | {f'{len(X_train)} / {len(X_test)}':<26}")
    print(f"{'Baseline MAE':<18} | {'8.8438':<26} | {baseline_mae:<26.4f}")
    print(f"{'ML MAE':<18} | {'4.7247':<26} | {mae:<26.4f}")
    print(f"{'RMSE':<18} | {'5.7713':<26} | {rmse:<26.4f}")
    print(f"{'R² Score':<18} | {'0.7129':<26} | {r2:<26.4f}")
    print("=" * 60)

    # 7. Sample Predictions vs Actuals
    sample_comparison = pd.DataFrame(
        {
            "Subject": X_test["Subject"].values[:10],
            "Semester": X_test["Semester"].values[:10],
            "Internal": X_test["Internal"].values[:10],
            "Attendance": X_test["Attendance"].values[:10],
            "Actual External": y_test.values[:10],
            "Predicted External": np.round(y_pred[:10], 2),
            "Difference": np.round(np.abs(y_test.values[:10] - y_pred[:10]), 2),
        }
    )

    print("\nSAMPLE PREDICTIONS (First 10 Test Records):")
    print(sample_comparison.to_string(index=False))
    print("=" * 50 + "\n")

    # 8. Save model pipeline
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_SAVE_PATH, compress=3)
    print(f"Trained ML Pipeline successfully saved to: {MODEL_SAVE_PATH}\n")

    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "model_path": str(MODEL_SAVE_PATH),
    }


if __name__ == "__main__":
    train_and_evaluate()
