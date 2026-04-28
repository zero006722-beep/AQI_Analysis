# AQI Analysis Dashboard

An interactive **Air Quality Index** dashboard built with Streamlit and Plotly, ready to deploy on [Render](https://render.com).

## 📁 File Structure

```
├── app.py                  # Main Streamlit application
├── air_quality.csv         # Dataset (copy from your repo)
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment blueprint
└── .streamlit/
    └── config.toml         # Streamlit server config
```

## 🚀 Deploy on Render

### Option A — Auto-deploy with render.yaml (recommended)

1. Push all these files **plus `air_quality.csv`** to your GitHub repo.
2. Go to [render.com](https://render.com) → **New → Blueprint**.
3. Connect your GitHub repo (`AQI_Analysis`).
4. Render will detect `render.yaml` and auto-configure everything.
5. Click **Apply** — your app will be live in ~2 minutes.

### Option B — Manual Web Service

1. Push all files to GitHub.
2. Render → **New → Web Service** → connect your repo.
3. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Click **Create Web Service**.

## ⚠️ Important

Make sure `air_quality.csv` is in the **root of the repo** alongside `app.py`. The app reads it with `pd.read_csv("air_quality.csv")`.

## 📊 Features

- KPI cards (avg / max / min AQI, city count)
- AQI histogram with category coloring
- Average AQI bar chart per city
- Time-series trend with AQI band reference lines
- Pollutant box plots, correlation heatmap, scatter vs AQI
- AQI category pie chart
- Top 10 worst records table
- Raw data viewer + CSV download
- City & date range filters in sidebar
