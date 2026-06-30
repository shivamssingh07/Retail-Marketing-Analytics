"""
06_customer_segmentation.py
-----------------------------
Stage 6 of the analytics pipeline: Unsupervised Customer Segmentation.

While rfm_analysis.py produces *rule-based* RFM segments (Champions, At Risk,
etc.), this module builds a complementary, *data-driven* segmentation using
K-Means clustering on standardized RFM features. This is the version
recruiters expect to see when a job description says "customer segmentation
using machine learning / clustering".

Pipeline:
    1. Load RFM table (output of rfm_analysis.py).
    2. Standardize Recency, Frequency, Monetary (StandardScaler).
    3. Determine the optimal k using the Elbow Method (inertia) AND the
       Silhouette Score, saving a comparison chart.
    4. Fit final KMeans model with the chosen k.
    5. Profile each cluster (mean RFM, size, % of revenue) and assign a
       human-readable business name (VIP / Loyal / At Risk / Lost, etc.)
       based on the cluster's relative RFM profile.
    6. Save cluster assignments, a PCA 2D projection for visualization,
       and the fitted scaler + model artifacts for reuse (e.g. scoring new
       customers in the Streamlit app).

Run:
    python -m src.customer_segmentation
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src import config
from src.utils import get_logger, load_csv, save_csv, save_fig, setup_plot_style

logger = get_logger(__name__)

FEATURES = ["Recency", "Frequency", "Monetary"]


def load_rfm() -> pd.DataFrame:
    return load_csv(config.RFM_FILE)


def scale_features(rfm: pd.DataFrame):
    scaler = StandardScaler()
    X = scaler.fit_transform(rfm[FEATURES])
    return X, scaler


def find_optimal_k(X, k_range=range(2, config.KMEANS_MAX_CLUSTERS_TO_TEST + 1)):
    """Evaluate inertia (elbow) and silhouette score across a range of k values."""
    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=config.KMEANS_RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X)
        results.append({
            "k": k,
            "inertia": km.inertia_,
            "silhouette": silhouette_score(X, labels),
            "davies_bouldin": davies_bouldin_score(X, labels),
        })
    results_df = pd.DataFrame(results)
    logger.info("K-selection metrics:\n%s", results_df.to_string(index=False))
    return results_df


def plot_optimal_k(results_df: pd.DataFrame):
    import matplotlib.pyplot as plt

    setup_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].plot(results_df["k"], results_df["inertia"], marker="o", color="#2563eb")
    axes[0].set_title("Elbow Method (Inertia)")
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia")

    axes[1].plot(results_df["k"], results_df["silhouette"], marker="o", color="#16a34a")
    axes[1].set_title("Silhouette Score by k")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")

    fig.suptitle("K-Means Cluster Count Selection", fontsize=15, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "18_optimal_clusters.png")


def fit_final_model(X, n_clusters: int = config.KMEANS_N_CLUSTERS):
    model = KMeans(n_clusters=n_clusters, random_state=config.KMEANS_RANDOM_STATE, n_init=10)
    labels = model.fit_predict(X)
    sil = silhouette_score(X, labels)
    logger.info("Final KMeans fit: k=%d, silhouette=%.3f", n_clusters, sil)
    return model, labels, sil


def name_clusters(rfm: pd.DataFrame) -> dict:
    """Rank clusters by a composite RFM value and map them to business names.

    Clusters are ranked by mean Monetary value (descending) combined with
    Recency (ascending = more recent = better) to decide ordering, then
    mapped onto a fixed set of business-friendly labels. This keeps the
    naming logic deterministic regardless of which integer label KMeans
    happens to assign to which group on a given run.
    """
    profile = rfm.groupby("Cluster")[FEATURES].mean()
    # Composite score: higher Monetary & Frequency, lower Recency => better
    profile["composite"] = (
        profile["Monetary"].rank(ascending=True)
        + profile["Frequency"].rank(ascending=True)
        + profile["Recency"].rank(ascending=False)
    )
    ranked = profile.sort_values("composite", ascending=False).index.tolist()

    label_pool = ["VIP Customers", "Loyal Customers", "At Risk", "Lost / Dormant"]
    # If k != 4, fall back to generic tiered names
    if len(ranked) != len(label_pool):
        label_pool = [f"Tier {i+1}" for i in range(len(ranked))]

    return {cluster_id: label_pool[i] for i, cluster_id in enumerate(ranked)}


def profile_clusters(rfm: pd.DataFrame) -> pd.DataFrame:
    total_revenue = rfm["Monetary"].sum()
    profile = rfm.groupby("Cluster_Name").agg(
        Customer_Count=("Customer_ID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean"),
        Total_Revenue=("Monetary", "sum"),
    ).reset_index()
    profile["Pct_of_Customers"] = (profile["Customer_Count"] / len(rfm) * 100).round(2)
    profile["Pct_of_Revenue"] = (profile["Total_Revenue"] / total_revenue * 100).round(2)
    return profile.sort_values("Total_Revenue", ascending=False)


def plot_clusters_pca(X, labels, names: pd.Series):
    import matplotlib.pyplot as plt

    setup_plot_style()
    pca = PCA(n_components=2, random_state=config.KMEANS_RANDOM_STATE)
    coords = pca.fit_transform(X)

    fig, ax = plt.subplots(figsize=(9, 7))
    scatter = ax.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="viridis", alpha=0.6, s=25)
    ax.set_title("Customer Segments — PCA Projection (2D)")
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    legend = ax.legend(*scatter.legend_elements(), title="Cluster", loc="best")
    ax.add_artist(legend)
    fig.tight_layout()
    save_fig(fig, "19_customer_segments_pca.png")


def run():
    rfm = load_rfm()
    X, scaler = scale_features(rfm)

    k_results = find_optimal_k(X)
    plot_optimal_k(k_results)

    model, labels, sil = fit_final_model(X)
    rfm["Cluster"] = labels

    cluster_name_map = name_clusters(rfm)
    rfm["Cluster_Name"] = rfm["Cluster"].map(cluster_name_map)

    profile = profile_clusters(rfm)
    logger.info("Cluster profile:\n%s", profile.to_string(index=False))

    plot_clusters_pca(X, labels, rfm["Cluster_Name"])

    save_csv(rfm, config.SEGMENTS_FILE)
    save_csv(profile, config.REPORTS_DIR / "cluster_profile.csv")

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, config.MODELS_DIR / "kmeans_segmentation_model.pkl")
    joblib.dump(scaler, config.MODELS_DIR / "rfm_scaler.pkl")
    joblib.dump(cluster_name_map, config.MODELS_DIR / "cluster_name_map.pkl")

    logger.info("Segmentation complete. Silhouette score: %.3f", sil)
    logger.info("Saved cluster assignments to %s", config.SEGMENTS_FILE)
    return rfm, profile


if __name__ == "__main__":
    run()
