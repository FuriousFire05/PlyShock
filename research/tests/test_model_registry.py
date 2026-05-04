from plyshock.training.model_registry import build_model_registry
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier


def test_build_model_registry_contains_exact_required_models() -> None:
    registry = build_model_registry(random_state=123)

    assert set(registry) == {
        "decision_tree",
        "knn",
        "naive_bayes",
        "svm",
        "random_forest",
    }


def test_build_model_registry_model_types_and_key_params() -> None:
    registry = build_model_registry(random_state=123)

    assert isinstance(registry["decision_tree"], DecisionTreeClassifier)
    assert isinstance(registry["knn"], Pipeline)
    assert isinstance(registry["naive_bayes"], GaussianNB)
    assert isinstance(registry["svm"], Pipeline)
    assert isinstance(registry["random_forest"], RandomForestClassifier)
    assert registry["decision_tree"].class_weight == "balanced"
    assert registry["random_forest"].n_estimators == 200
    assert registry["random_forest"].class_weight == "balanced"
