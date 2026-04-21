import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils import shuffle

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

# ----------------------------
# Load Data
# ----------------------------
df = pd.read_excel(r"d:\ESG_platform\nlp\synthetic_greenwash_train_with_has_number.xlsx")

# Ensure correct types
df["claim_sentence"] = df["claim_sentence"].astype(str)
df["label"] = df["label"].astype(str)
df["has_number"] = df["has_number"].astype(int)

print(df["label"].value_counts())

# ----------------------------
# Features & Target
# ----------------------------
X = df[["claim_sentence", "has_number"]]
y = df["label"]

# Shuffle
X, y = shuffle(X, y, random_state=42)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ----------------------------
# Preprocessing (IMPORTANT FIX)
# ----------------------------
preprocessor = ColumnTransformer([
    ("text", TfidfVectorizer(), "claim_sentence"),
    ("num", "passthrough", ["has_number"])
])

# ----------------------------
# Pipeline
# ----------------------------
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("svc", SVC(probability=True, class_weight="balanced"))
])

# ----------------------------
# Hyperparameter Space (SAFE)
# ----------------------------
param_dist = {
    "preprocessor__text__max_features": [3000, 5000],
    "preprocessor__text__ngram_range": [(1,1), (1,2)],
    "preprocessor__text__min_df": [1, 2],
    "preprocessor__text__max_df": [0.9, 1.0],

    "svc__C": [1, 10],
    "svc__kernel": ["linear", "rbf"],
    "svc__gamma": ["scale"]
}

# ----------------------------
# K-Fold
# ----------------------------
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ----------------------------
# Randomized Search
# ----------------------------
random_search = RandomizedSearchCV(
    estimator=pipeline,
    param_distributions=param_dist,
    n_iter=10,
    cv=kfold,
    scoring="f1_weighted",
    n_jobs=-1,
    verbose=2,
    random_state=42,
    error_score="raise"   # helps debugging
)

# ----------------------------
# Train
# ----------------------------
random_search.fit(X_train, y_train)

best_model = random_search.best_estimator_

print("\nBest Parameters:")
print(random_search.best_params_)

# ----------------------------
# Evaluation
# ----------------------------
y_pred = best_model.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# ----------------------------
# Cross-validation score (optional)
# ----------------------------
from sklearn.model_selection import cross_val_score

cv_scores = cross_val_score(
    best_model, X, y,
    cv=kfold,
    scoring="f1_weighted"
)

print("\nCross-validation scores:", cv_scores)
print("Mean CV F1:", np.mean(cv_scores))

from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

# ----------------------------
# ROC-AUC Curve
# ----------------------------

# Get class labels
classes = best_model.classes_

# Binarize labels (important for multi-class)
y_test_bin = label_binarize(y_test, classes=classes)

# Predict probabilities
y_score = best_model.predict_proba(X_test)

# Compute ROC curve and AUC for each class
fpr = dict()
tpr = dict()
roc_auc = dict()

for i in range(len(classes)):
    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# ----------------------------
# Plot ROC Curve
# ----------------------------
plt.figure()

for i in range(len(classes)):
    plt.plot(fpr[i], tpr[i], label=f"Class {classes[i]} (AUC = {roc_auc[i]:.3f})")

plt.plot([0, 1], [0, 1], linestyle="--")  # random baseline

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC-AUC Curve")
plt.legend(loc="lower right")

plt.show()