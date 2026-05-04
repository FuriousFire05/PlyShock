# PlyShock Literature Notes

## Purpose

This file stores the curated research direction for PlyShock. It is not the final report prose. It is a project memory file used to guide the final literature review, methodology, feature design, report references, and viva preparation.

## Project Focus

PlyShock predicts chess upsets from mid-game snapshots using classical data mining methods.

An upset is defined as:

> A lower-rated player defeating a higher-rated opponent.

The project uses Lichess PGN data, rating metadata, clock/time information, Stockfish evaluations, and mid-game snapshot features.

## Implementation Constraint

This is a Data Mining course project. The implementation should focus on classical ML/data mining methods:

- Decision Tree
- K-Nearest Neighbors
- Naive Bayes
- Support Vector Machine
- Random Forest
- Optional Logistic Regression baseline
- EDA, preprocessing, explainability, and feature importance

Deep learning papers may be cited as related work, but the implementation should not be framed as a CNN/deep-learning project.

---

## Final Curated Paper Set

### Core Chess References

1. Rokach and Shapira, 2026 — Blunder prediction in chess  
   Use for: human error, rating alone being insufficient, error-prone positions.

2. Adhikari, Anatolyev, and Dagaev, 2024 — Do Mistakes Provoke New Mistakes? Evidence from Chess  
   Use for: error propagation, evaluation swings, instability-history features.

3. Carow and Witzig, 2025 — Time pressure and strategic risk-taking in professional chess  
   Use for: clock pressure, time × position interaction features.

4. Russek et al., 2025 — Time Spent Thinking in Online Chess Reflects the Value of Computation  
   Use for: time allocation, clock usage, computation-value framing.

5. Chacoma and Billoni, 2025 — Emergent complexity in the decision-making process of chess players  
   Use for: decision complexity, positional instability, decisiveness features.

6. Tang et al., 2024 — Maia-2: A Unified Model for Human-AI Alignment in Chess  
   Use for: human-like chess modeling and rating-conditioned behavior. Mention as related work only because it is deep-learning based.

7. Tijhuis, Mavromoustakos Blom, and Spronck, 2023 — Predicting Chess Player Rating Based on a Single Game  
   Use for: classical/tabular chess feature-engineering precedent.

8. Chowdhary, Iacopini, and Battiston, 2023 — Quantifying human performance in chess  
   Use for: large-scale human chess performance patterns and rating-linked behavior.

### Cross-Domain Methodology / Explainability References

9. Berrar, Lopes, and Dubitzky, 2024 — A data- and knowledge-driven framework for developing machine learning models to predict soccer match outcomes  
   Use for: classical ML + domain-feature engineering justification.

10. Yeung, Bunker, and Fujii, 2023 — A framework of interpretable match results prediction in football with FIFA ratings and team formation  
   Use for: interpretable prediction and human-usable explanation framing.

11. Ouyang et al., 2024 — Integration of machine learning XGBoost and SHAP models for NBA game outcome prediction and quantitative analysis methodology  
   Use for: stage-wise prediction and explainability analogy. Do not make XGBoost central unless needed.

12. Ni and Lee, 2023 — A Comparative Study of Machine Learning Models for NCAA Men’s Basketball Tournament Games Outcome Prediction  
   Use for: cross-domain upset-style tournament prediction and classical model comparison.

---

## Main Research Gap

Existing chess studies separately examine blunders, error propagation, time pressure, human-like move prediction, rating-related behavior, and decision complexity. Sports analytics studies separately examine match outcome prediction and model interpretability.

However, there is limited verified work that combines:

- rating mismatch,
- mid-game engine evaluation,
- clock/time pressure,
- positional instability,
- and human-centric interaction features

to predict chess upsets where the lower-rated player defeats the higher-rated player.

This gap motivates PlyShock.

---

## Locked Novelty Claims

1. PlyShock reframes chess upset prediction as a mid-game snapshot-based data mining problem instead of a pre-game odds problem or a generic winner prediction task.

2. PlyShock combines rating gap, Stockfish evaluation, clock pressure, and positional instability in one interpretable tabular pipeline.

3. PlyShock uses classical data mining models and feature importance analysis, making it more suitable for a Data Mining course than a deep-learning-heavy chess model.

4. PlyShock studies when an upset becomes visible by comparing snapshots at moves 15, 20, 25, 30, and 35.

5. PlyShock focuses on lower-rated wins, which is a more meaningful surprising-event target than plain win/loss prediction.

---

## Papers to Use Cautiously

Avoid using papers that rely on post-game features such as final game duration, final turn count, final termination, or features unavailable at the mid-game snapshot. These can introduce target leakage.

Use preprints cautiously unless they are strongly relevant and clearly marked.

Older foundational chess papers can be useful as background, but they should not dominate the final literature review because the project rubric prefers recent papers.

---

## Implementation Lessons from Literature

- Rating alone is insufficient.
- Clock pressure should be modeled explicitly.
- Evaluation swings and local instability can represent human-error dynamics.
- Features must be available at or before the snapshot.
- Classical ML can be defensible when paired with strong domain-specific features.
- Interpretability matters for the final report and demo.
- Validation must avoid leakage when multiple snapshots come from the same game.

---

## Report Usage Plan

Final report should include:

- Literature Review table with 12 papers grouped by theme.
- Research gap paragraph based on the locked gap above.
- Feature category table.
- Architecture diagram.
- EDA plots:
  - upset class distribution,
  - rating gap distribution / upset rate,
  - snapshot availability,
  - clock pressure distribution.
- Model comparison table.
- Feature importance plot.
- Confusion matrix.