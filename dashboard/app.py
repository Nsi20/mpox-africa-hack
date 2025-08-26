# dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------------------------------------------------
# DATA & HELPERS
# ---------------------------------------------------------
DATA = Path(__file__).parents[1] / "data" / "processed" / "mpox_clean.csv"
df = pd.read_csv(DATA)

pop2024 = {
    "Sierra Leone": 8.2, "Uganda": 48.6, "DR Congo": 115.0, "Nigeria": 223.8,
    "Ghana": 34.0, "Cameroon": 28.6, "Burundi": 13.2, "Liberia": 5.4,
    "Guinea": 14.2, "Togo": 9.0, "Sudan": 48.1, "South Sudan": 11.4,
    "Ethiopia": 126.5, "Tanzania": 67.4, "Kenya": 55.1, "Mozambique": 34.5,
    "Zambia": 20.6
}
df["pop_millions"] = df["Country"].map(pop2024)
latest = df.sort_values("Report_Date").groupby("Country", as_index=False).tail(1)

# derived
latest["gap_doses"] = ((latest["pop_millions"] * 0.05 * 2) - latest["Vaccine_Dose_Deployed"]).round(0).fillna(0).astype(int)
latest["labs_per_10M"] = (latest["Testing_Laboratories"] / latest["pop_millions"] * 10).round(1)
latest["load_per_lab"] = (latest["Suspected_Cases"] / latest["Testing_Laboratories"]).round(1)
latest["ratio"] = (latest["Suspected_Cases"] / latest["Confirmed_Cases"]).round(1)
latest["wastage_pct"] = ((latest["Vaccine_Dose_Allocated"] - latest["Vaccine_Dose_Deployed"]) / latest["Vaccine_Dose_Allocated"] * 100).round(1)
latest["chw_per_100k"] = (latest["Trained_CHWs"] / latest["pop_millions"] * 100_000).round(1)
latest["deploy_ratio"] = (latest["Deployed_CHWs"] / latest["Trained_CHWs"]).round(2)

st.set_page_config(page_title="Data-Drive: Mpox Top-5 Report", layout="wide")
st.title("🌍 Data-Drive: Mpox Top-5 Report")

# ---------------------------------------------------------
# KPI BAR
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Total Gap Doses", f"{latest.gap_doses.sum()/1e6:.1f} M")
c2.metric("Median CFR", f"{latest.Case_Fatality_Rate.median()*100:.1f} %")
c3.metric("Avg Lab Load", f"{latest.load_per_lab.median():.0f}")

# ---------------------------------------------------------
# VISUAL FACTORY
# ---------------------------------------------------------
def bar_chart(data, x, y, title, color_scale="Blues", orientation="h"):
    fig = px.bar(
        data, x=x, y=y, orientation=orientation,
        color=x, color_continuous_scale=color_scale, text=x, title=title
    )
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# ---------------------------------------------------------
# Q1 – Highest Cases
# ---------------------------------------------------------
q1 = df.groupby("Country")["Confirmed_Cases"].sum().sort_values(ascending=False).reset_index().head(5)
st.plotly_chart(bar_chart(q1, "Confirmed_Cases", "Country", "Top-5 Total Confirmed Cases", "Blues"), use_container_width=True)
st.markdown("**Key Finding:** Nigeria, Uganda, and Sierra Leone carry the highest cumulative Mpox burden across Africa.")

# ---------------------------------------------------------
# Q3 – Weekly Peaks
# ---------------------------------------------------------
q3 = df.groupby("Country")["Weekly_New_Cases"].max().sort_values(ascending=False).reset_index().head(5)
fig_q3 = px.line(q3, x="Country", y="Weekly_New_Cases", markers=True, title="Top-5 Weekly New-Case Peaks")
st.plotly_chart(fig_q3, use_container_width=True)
st.markdown("**Key Finding:** Sierra Leone and Uganda recorded the sharpest weekly surges (>600 cases).")

# ---------------------------------------------------------
# Q5 – Lab Load
# ---------------------------------------------------------
q5 = latest.sort_values("load_per_lab", ascending=False).head(5)
fig_q5 = px.bar(q5, x="Country", y="load_per_lab", color="load_per_lab", text="load_per_lab",
                color_continuous_scale="Viridis", title="Top-5 Diagnostic Load per Lab")
st.plotly_chart(fig_q5, use_container_width=True)
st.markdown("**Key Finding:** Togo & Sierra Leone labs face heavy loads, handling >1,000 suspected cases per lab.")

# ---------------------------------------------------------
# Q6 – Cases/Lab Ratio
# ---------------------------------------------------------
q6 = latest.sort_values("ratio", ascending=False).head(5)
fig_q6 = px.scatter(q6, x="Country", y="ratio", size="ratio", color="Country",
                    title="Top-5 Suspected/Confirmed Ratios")
st.plotly_chart(fig_q6, use_container_width=True)
st.markdown("**Key Finding:** High ratios (e.g., Togo, South Sudan) indicate under-testing or limited confirmatory capacity.")

# ---------------------------------------------------------
# Q7 – CHW Density
# ---------------------------------------------------------
q7 = latest.sort_values("chw_per_100k", ascending=False).head(5)
fig_q7 = px.bar(q7, x="chw_per_100k", y="Country", orientation="h", color="chw_per_100k",
                color_continuous_scale="Teal", text="chw_per_100k", title="Top-5 CHWs per 100k Population")
st.plotly_chart(fig_q7, use_container_width=True)
st.markdown("**Key Finding:** Nigeria has the largest CHW training numbers, but deployment ratios remain below 80%.")

# ---------------------------------------------------------
# Q8 – Vaccine Gap
# ---------------------------------------------------------
q8 = latest.sort_values("gap_doses", ascending=False).head(5)
fig_q8 = px.bar(q8, x="gap_doses", y="Country", orientation="h", color="gap_doses",
                color_continuous_scale="Reds", text="gap_doses", title="Top-5 Vaccine Dose Gaps")
st.plotly_chart(fig_q8, use_container_width=True)
st.markdown("**Key Finding:** Nigeria, DR Congo, and Uganda require >19 million additional doses to close immunity gaps.")

# ---------------------------------------------------------
# Q9 – Wastage
# ---------------------------------------------------------
q9 = latest.sort_values("wastage_pct", ascending=False).head(5)
fig_q9 = px.bar(q9, x="wastage_pct", y="Country", orientation="h", color="wastage_pct",
                color_continuous_scale="Oranges", text="wastage_pct", title="Top-5 Vaccine Wastage (%)")
st.plotly_chart(fig_q9, use_container_width=True)
st.markdown("**Key Finding:** Burundi & Cameroon waste ≥17% of allocated doses — requiring urgent cold-chain strengthening.")

# ---------------------------------------------------------
# MAP – Vaccine Gap Across Africa
# ---------------------------------------------------------
fig_map = px.choropleth(
    latest,
    locations="Country",
    locationmode="country names",
    color="gap_doses",
    color_continuous_scale="Reds",
    title="🌍 Vaccine Gap Across Africa (All Countries)",
    hover_name="Country",
    hover_data={"gap_doses": True, "pop_millions": True},
)
fig_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_map, use_container_width=True)
st.markdown("**Key Finding:** Vaccine gaps cluster in West & Central Africa — especially Nigeria and DR Congo — highlighting urgent procurement needs.")
