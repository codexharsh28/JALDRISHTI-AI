"""
Inundation 6-Source Ablation Experiment Script for JALDRISHTI AI.
Executes systematic feature tier evaluation and outputs ml/evaluation/inundation_source_ablation.json.
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.inundation.ablation import InundationFeatureAblation

def run_inundation_source_ablation():
    print("==================================================")
    print("RUNNING INUNDATION 6-SOURCE FEATURE ABLATION")
    print("==================================================")

    train_path = "data/simulation/inundation_samples_train.csv"
    val_path = "data/simulation/inundation_samples_val.csv"

    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)

    ablation_engine = InundationFeatureAblation()
    results = ablation_engine.run_ablation(df_train, df_val)

    output = {
        "study_title": "JALDRISHTI AI 2D Inundation Feature Source Ablation Study",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "training_dataset": train_path,
        "evaluation_dataset": val_path,
        "total_configurations": len(results),
        "configurations": results
    }

    os.makedirs("ml/evaluation", exist_ok=True)
    out_file = Path("ml/evaluation/inundation_source_ablation.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Inundation source ablation complete. Results saved to {out_file}")
    for k, v in results.items():
        print(f" - {v['name']}: IoU={v['iou']:.3f}, F1={v['f1']:.3f}, Brier={v['brier_score']:.4f}, Depth RMSE={v['depth_rmse_m']:.3f}m")

    return output

if __name__ == "__main__":
    run_inundation_source_ablation()
