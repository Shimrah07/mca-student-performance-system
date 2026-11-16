"""
ml/src/mca_compat.py

Environment compatibility helper for scikit-learn on Windows.
When external Windows Application Control policies block specific optional
C-extension DLLs (such as _liblinear, which is only needed for LinearSVC),
this module registers a lightweight stub in sys.modules so that standard
unblocked classifiers (LogisticRegression with lbfgs, DecisionTreeClassifier,
RandomForestClassifier, ColumnTransformer) can load and execute natively.
"""

import sys
import types


def ensure_sklearn_compat():
    """Ensure sklearn optional C-extension stubs are registered if blocked by host OS policy."""
    if "sklearn.svm._liblinear" not in sys.modules:
        try:
            import sklearn.svm._liblinear  # type: ignore # noqa: F401
        except ImportError as exc:
            if "Application Control policy" in str(exc) or "DLL load failed" in str(exc):
                stub = types.ModuleType("sklearn.svm._liblinear")
                stub.set_verbosity_wrap = lambda x: None  # type: ignore
                sys.modules["sklearn.svm._liblinear"] = stub


# Run on module import
ensure_sklearn_compat()
