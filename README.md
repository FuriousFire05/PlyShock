# PlyShock

**Human-Centric Chess Upset Prediction**

PlyShock is a data mining and machine learning project that predicts chess upsets from mid-game positions. An upset is defined as a lower-rated player defeating a higher-rated opponent.

## Academic Title

Dynamic Upset Prediction in Chess Using Mid-Game Human-Centric Features

## Project Motivation

Chess outcomes are often expected to follow player ratings, but real games can shift due to time pressure, positional instability, and human decision-making errors. PlyShock studies these mid-game factors to understand when an upset becomes more likely.

## Planned Pipeline

1. Parse Lichess PGN data
2. Filter valid rated standard games
3. Extract mid-game snapshots
4. Compute Stockfish evaluations
5. Engineer rating, clock, engine, and instability features
6. Perform EDA and preprocessing
7. Train data mining models
8. Compare model performance
9. Build a demo dashboard

## Data Mining Models

The project focuses on classical data mining and machine learning methods:

- Decision Tree
- K-Nearest Neighbors
- Naive Bayes
- Support Vector Machine
- Random Forest

## Tech Stack

- Python
- pandas
- NumPy
- scikit-learn
- python-chess
- Stockfish
- FastAPI
- Next.js
- Docker

## Status

Project setup in progress.