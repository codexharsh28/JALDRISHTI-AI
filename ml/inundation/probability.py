"""
Probabilistic Calibration & Uncertainty Evaluation Module for Inundation Extent.
Implements:
1. Platt Scaling (Logistic Sigmoid Calibration)
2. Isotonic Calibration
3. Expected Calibration Error (ECE)
4. Brier Score
5. Reliability Diagrams / Calibration Bins
"""

from typing import Dict, Any, List, Tuple
import numpy as np

class PlattCalibrator:
    """
    Platt Scaling Calibrator: Fits a logistic regression model P(y=1 | f(x)) = 1 / (1 + exp(A * f(x) + B))
    to convert raw surrogate continuous scores into well-calibrated posterior probabilities.
    """
    def __init__(self, a: float = -3.2, b: float = 0.4):
        self.a = a
        self.b = b
        self._fitted = False

    def fit(self, raw_scores: np.ndarray, y_true_binary: np.ndarray):
        """
        Fits parameters A and B via maximum likelihood on validation fold.
        """
        # Optimize using scipy or closed-form logistic regression
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(solver="lbfgs")
        X = raw_scores.reshape(-1, 1)
        lr.fit(X, y_true_binary)
        self.a = float(lr.coef_[0][0])
        self.b = float(lr.intercept_[0])
        self._fitted = True

    def calibrate(self, raw_scores: np.ndarray) -> np.ndarray:
        """
        Calculates calibrated probabilities in [0.0, 1.0].
        """
        logits = self.a * raw_scores + self.b
        # Numerical stability clip
        logits = np.clip(logits, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-logits))

class IsotonicCalibrator:
    """
    Non-parametric isotonic regression calibrator for flexible, monotonicity-preserving calibration.
    """
    def __init__(self):
        self._isotonic = None
        self._fitted = False

    def fit(self, raw_scores: np.ndarray, y_true_binary: np.ndarray):
        from sklearn.isotonic import IsotonicRegression
        self._isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self._isotonic.fit(raw_scores.ravel(), y_true_binary.ravel())
        self._fitted = True

    def calibrate(self, raw_scores: np.ndarray) -> np.ndarray:
        if self._isotonic is None:
            # Fallback identity min-max clip
            return np.clip(raw_scores, 0.0, 1.0)
        return self._isotonic.predict(raw_scores.ravel()).reshape(raw_scores.shape)

def compute_brier_score(y_true_binary: np.ndarray, y_prob: np.ndarray) -> float:
    """
    Computes Brier Score: Mean squared difference between predicted probabilities and actual binary outcomes.
    BS = (1/N) * sum((p_i - y_i)^2)
    Lower is better (0.0 is perfect).
    """
    y_t = np.asarray(y_true_binary).ravel()
    y_p = np.asarray(y_prob).ravel()
    return float(np.mean((y_p - y_t) ** 2))

def compute_expected_calibration_error(
    y_true_binary: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE) across uniform confidence bins.
    ECE = sum_{b=1}^B (|B_b| / N) * |acc(B_b) - conf(B_b)|
    """
    y_t = np.asarray(y_true_binary).ravel()
    y_p = np.asarray(y_prob).ravel()
    n = len(y_t)
    if n == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower, bin_upper = bins[i], bins[i+1]
        mask = (y_p >= bin_lower) & (y_p <= bin_upper) if i == n_bins - 1 else (y_p >= bin_lower) & (y_p < bin_upper)
        bin_count = np.sum(mask)
        if bin_count > 0:
            bin_acc = np.mean(y_t[mask])
            bin_conf = np.mean(y_p[mask])
            ece += (bin_count / n) * np.abs(bin_acc - bin_conf)

    return float(ece)

def compute_reliability_diagram(
    y_true_binary: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Computes bin-level observed empirical accuracy, mean predicted confidence, and bin weight.
    """
    y_t = np.asarray(y_true_binary).ravel()
    y_p = np.asarray(y_prob).ravel()
    n = len(y_t)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    diagram_bins = []

    for i in range(n_bins):
        bin_lower, bin_upper = bins[i], bins[i+1]
        mask = (y_p >= bin_lower) & (y_p <= bin_upper) if i == n_bins - 1 else (y_p >= bin_lower) & (y_p < bin_upper)
        bin_count = int(np.sum(mask))
        if bin_count > 0:
            bin_acc = float(np.mean(y_t[mask]))
            bin_conf = float(np.mean(y_p[mask]))
        else:
            bin_acc = 0.0
            bin_conf = (bin_lower + bin_upper) / 2.0

        diagram_bins.append({
            "bin_index": i,
            "bin_range": [round(bin_lower, 2), round(bin_upper, 2)],
            "count": bin_count,
            "fraction_of_total": round(bin_count / max(1, n), 4),
            "mean_predicted_prob": round(bin_conf, 4),
            "observed_positive_rate": round(bin_acc, 4)
        })

    ece = compute_expected_calibration_error(y_t, y_p, n_bins=n_bins)
    brier = compute_brier_score(y_t, y_p)

    return {
        "n_bins": n_bins,
        "sample_size": n,
        "expected_calibration_error_ece": round(ece, 4),
        "brier_score": round(brier, 4),
        "bins": diagram_bins
    }
