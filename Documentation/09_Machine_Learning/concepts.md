# 09. Machine Learning Concepts

This chapter outlines the core machine learning algorithms, dataset balancing techniques, and evaluation metrics used in this project.

---

## 🌲 1. Random Forest Classifier

The system uses a **Random Forest Classifier** as the core model. Random Forest is an ensemble learning method that builds multiple decision trees during training and outputs the majority vote class for predictions:

```mermaid
graph TD
    Input[Input Features] --> Tree1[Decision Tree 1]
    Input --> Tree2[Decision Tree 2]
    Input --> TreeN[Decision Tree N]
    
    Tree1 --> Predict1[Class 0]
    Tree2 --> Predict2[Class 1]
    TreeN --> PredictN[Class 0]
    
    Predict1 --> Voting[Majority Voting]
    Predict2 --> Voting
    PredictN --> Voting
    
    Voting --> Final[Final Prediction: Class 0]
```

### Why Random Forest?
*   **Handles Mixed Data Types**: Easily handles binary, integer, and scaled float columns.
*   **Resistant to Overfitting**: By averaging predictions across trees, it reduces variance compared to individual decision trees.
*   **Non-Linear Boundaries**: Can capture complex, non-linear interactions between variables (such as relations between Age, Vintage, and Previous Insurance status) without manual feature engineering.

### Hyperparameters Configured
*   `n_estimators = 200`: Number of decision trees in the forest. More trees improve stability but increase training time.
*   `max_depth = 10`: Limits tree depth to prevent overfitting.
*   `min_samples_split = 7`: Minimum samples required to split an internal node.
*   `min_samples_leaf = 6`: Minimum samples required at a leaf node, smoothing predictions near boundaries.
*   `criterion = 'entropy'`: Measures split quality based on information gain.

---

## ⚖️ 2. Resolving Class Imbalance (SMOTEENN)

With only 12% positive cases in the raw dataset, a standard classifier will bias towards the majority class (`Response = 0`). The project resolves this by applying **SMOTEENN** (SMOTE + Edited Nearest Neighbors):

### 1. Oversampling (SMOTE)
*   SMOTE (Synthetic Minority Over-sampling Technique) fits a K-Nearest Neighbors model on the minority class (`Response = 1`).
*   It draws a line segment between a minority sample and its nearest neighbors.
*   Synthetic samples are created along these line segments, balancing the representation of both classes.

### 2. Under-sampling & Cleaning (ENN)
*   Oversampling can create noisy, overlapping regions where synthetic class 1 points bleed into class 0 clusters.
*   ENN (Edited Nearest Neighbors) examines the K-Nearest Neighbors of each sample in the dataset.
*   If a sample's class differs from the majority class of its neighbors, it is dropped. This cleans up decision boundaries, making it easier for the Random Forest to identify the class boundary.

### Visual: SMOTEENN Pipeline Flow

```mermaid
flowchart LR
    subgraph Before
        Raw["Imbalanced Data\n88% Class 0\n12% Class 1"]
    end

    subgraph "Step 1: SMOTE"
        Raw --> SMOTE["Synthetic Oversampling"]
        SMOTE --> Mid["Balanced Data\n~50% Class 0\n~50% Class 1\n+ Noise at boundaries"]
    end

    subgraph "Step 2: ENN"
        Mid --> ENN["Edited Nearest Neighbors"]
        ENN --> Clean["Clean Balanced Data\nNoise Removed\nClear Decision Boundary"]
    end

    style Raw fill:#e74c3c,stroke:#c0392b,color:#fff
    style Mid fill:#f39c12,stroke:#e67e22,color:#fff
    style Clean fill:#2ecc71,stroke:#27ae60,color:#fff
```

---

## 📊 3. Classification Evaluation Metrics

Evaluating an imbalanced dataset requires metrics beyond raw accuracy:

```mermaid
classDiagram
    class ConfusionMatrix {
        +True Positive (TP) : Correctly predicted interested
        +False Positive (FP) : Incorrectly predicted interested
        +True Negative (TN) : Correctly predicted not interested
        +False Negative (FN) : Incorrectly predicted not interested
    }
```

### 1. Precision
Measures the accuracy of positive predictions:
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
*   *Business Context*: High precision ensures that when the system predicts a customer is interested, they actually are, minimizing wasted outreach resources.

### 2. Recall (Sensitivity)
Measures the proportion of actual positives identified:
$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
*   *Business Context*: High recall ensures that the company doesn't miss potential customers who would have bought insurance.

### 3. F1-Score
The harmonic mean of Precision and Recall:
$$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
*   *ML Context*: Provides a single metric to balance Precision and Recall, making it the primary metric for model evaluation.

---

## 🔬 4. Model Experimentation Insights

Reviewing the research findings in `notebook/experiment_notebook.ipynb`:

1.  **Baseline Failure**: Initially, models trained without resampling had high accuracy (87.7%) but an F1-score of **0.00** for the minority class (`Response = 1`). The classifier was predicting `0` for all inputs due to the class imbalance.
2.  **Hyperparameter Tuning**: Hyperparameters were tuned using `RandomizedSearchCV` across a parameter grid (evaluating options for `n_estimators`, `max_depth`, `min_samples_leaf`, and `min_samples_split` over 4-fold cross-validation).
3.  **Tuning Results**: Tuning selected `max_depth = 3` with `n_estimators = 300`. However, limiting the depth to 3 restricted model capacity, leading to poor recall on class 1.
4.  **Production Adjustment**: The production pipeline uses a depth limit of 10 (`max_depth = 10`) combined with SMOTEENN resampling. This balance maintains model stability while improving minority class predictions.

---

## 🌳 5. Decision Tree Split Visualization

Each tree in the Random Forest makes decisions by splitting features at threshold values. Here is a simplified representation of how a single decision tree within the forest might classify a sample:

```mermaid
graph TD
    Root{"Previously_Insured <= 0.5?"}
    Root -->|Yes: Not insured| B{"Vehicle_Damage_Yes <= 0.5?"}
    Root -->|No: Already insured| Leaf1["🔴 Class 0\nNot Interested"]

    B -->|Yes: No damage| Leaf2["🔴 Class 0\nNot Interested"]
    B -->|No: Has damage| C{"Age <= 35?"}

    C -->|Yes: Young driver| D{"Annual_Premium <= 30000?"}
    C -->|No: Older driver| Leaf3["🟢 Class 1\nInterested"]

    D -->|Yes: Low premium| Leaf4["🟢 Class 1\nInterested"]
    D -->|No: High premium| Leaf5["🔴 Class 0\nNot Interested"]

    style Leaf1 fill:#e74c3c,stroke:#c0392b,color:#fff
    style Leaf2 fill:#e74c3c,stroke:#c0392b,color:#fff
    style Leaf5 fill:#e74c3c,stroke:#c0392b,color:#fff
    style Leaf3 fill:#2ecc71,stroke:#27ae60,color:#fff
    style Leaf4 fill:#2ecc71,stroke:#27ae60,color:#fff
```

In a Random Forest with `n_estimators = 200`, 200 such trees are constructed on random subsets of features and data, and the final prediction is determined by majority voting across all trees.
