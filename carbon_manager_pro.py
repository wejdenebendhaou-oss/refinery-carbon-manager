import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


APP_TITLE = "Refinery Carbon Manager"
APP_SUBTITLE = "Operational GHG accounting platform for refinery assets"
HOURS_PER_YEAR = 8760

DEFAULT_FACTORS = {
    "fuel_gas": 2.7016,
    "fuel_oil": 3.1533,
    "electricity": 0.530,
}

SCOPE3_CATEGORIES = {
    "cat1": {
        "label": "Category 1 - Purchased Goods and Services",
        "short": "Cat 1",
        "description": "Purchased refinery products and other purchased goods, calculated with well-to-gate factors.",
        "item_column": "Product",
    },
    "cat4": {
        "label": "Category 4 - Upstream Transportation and Distribution",
        "short": "Cat 4",
        "description": "Inbound transport of crude oil, feedstock and purchased products before refinery ownership.",
        "item_column": "Route",
    },
    "cat6": {
        "label": "Category 6 - Business Travel",
        "short": "Cat 6",
        "description": "Fuel consumption from business travel vehicles and other company travel activity.",
        "item_column": "Vehicle",
    },
    "cat7": {
        "label": "Category 7 - Employee Commuting",
        "short": "Cat 7",
        "description": "Employee commute activity, including buses and other recurring transport modes.",
        "item_column": "Vehicle",
    },
    "cat9": {
        "label": "Category 9 - Downstream Transportation and Distribution",
        "short": "Cat 9",
        "description": "Outbound transport and distribution of sold refinery products after refinery gate.",
        "item_column": "Product / Route",
    },
    "cat11": {
        "label": "Category 11 - Use of Sold Products",
        "short": "Cat 11",
        "description": "Combustion emissions from the final use of refinery products sold to customers.",
        "item_column": "Product",
    },
}


def configure_page():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            :root {
                --bg: #f6f8fb;
                --panel: #ffffff;
                --ink: #111827;
                --muted: #64748b;
                --line: #e2e8f0;
                --primary: #0f766e;
                --primary-soft: #ccfbf1;
                --accent: #f59e0b;
                --danger: #dc2626;
            }

            .main .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2.4rem;
                max-width: 1400px;
            }

            h1, h2, h3 {
                letter-spacing: 0;
                color: var(--ink);
            }

            .app-header {
                padding: 20px 22px;
                border: 1px solid var(--line);
                border-radius: 8px;
                background: linear-gradient(135deg, #ffffff 0%, #eefdf9 100%);
                margin-bottom: 18px;
            }

            .app-header h1 {
                margin: 0;
                font-size: 34px;
                font-weight: 780;
            }

            .app-header p {
                margin: 6px 0 0 0;
                color: var(--muted);
                font-size: 15px;
            }

            div[data-testid="metric-container"] {
                background-color: var(--panel);
                border: 1px solid var(--line);
                padding: 16px 18px;
                border-radius: 8px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
            }

            [data-testid="stMetricLabel"] {
                color: var(--muted);
                font-size: 13px;
            }

            [data-testid="stMetricValue"] {
                color: var(--ink);
                font-size: 25px;
                font-weight: 760;
            }

            [data-testid="stSidebar"] {
                background: #0f172a;
            }

            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }

            [data-testid="stSidebar"] input {
                color: #111827;
            }

            [data-testid="stSidebar"] .stNumberInput label,
            [data-testid="stSidebar"] .stRadio label {
                color: #f8fafc;
            }

            .section-note {
                color: var(--muted);
                font-size: 14px;
                margin-top: -4px;
                margin-bottom: 12px;
            }

            .status-pill {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 999px;
                background: var(--primary-soft);
                color: #115e59;
                font-size: 13px;
                font-weight: 700;
            }

            .stButton > button {
                border-radius: 6px;
                border: 1px solid #0f766e;
                color: #0f766e;
                font-weight: 650;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    defaults = {
        "authenticated": False,
        "scope1_total": 0.0,
        "scope2_total": 0.0,
        "scope3_total": 0.0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def login_screen():
    left, center, right = st.columns([1.2, 1, 1.2])
    with center:
        st.markdown(
            """
            <div class="app-header">
                <h1>Refinery Carbon Manager</h1>
                <p>Secure access for refinery GHG inventory management.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="stir2025")
        if st.button("Sign in", use_container_width=True):
            if username == "admin" and password == "stir2025":
                st.session_state.authenticated = True
                st.rerun()
            st.error("Invalid username or password.")


def app_header(title, subtitle):
    st.markdown(
        f"""
        <div class="app-header">
            <span class="status-pill">2026 Inventory Workspace</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_tonnes(value):
    return f"{value:,.1f}"


def format_mt(value):
    return f"{value / 1_000_000:,.1f}"


def format_number(value):
    return f"{value:,.1f}"


def decimal_column_config(df):
    return {
        column: st.column_config.NumberColumn(column, format="%.1f")
        for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
    }


def sidebar_controls():
    with st.sidebar:
        st.title("Refinery Carbon")
        st.caption("Corporate GHG accounting")
        st.divider()

        page = st.radio(
            "Workspace",
            ["Executive Dashboard", "Scope 1 and 2", "Scope 3", "Reports"],
        )

        st.divider()
        st.subheader("Emission Factors")
        fuel_gas = st.number_input(
            "Fuel gas EF (kgCO2e/kg)",
            min_value=0.0,
            value=DEFAULT_FACTORS["fuel_gas"],
            step=0.0001,
            format="%.4f",
        )
        fuel_oil = st.number_input(
            "Fuel oil EF (kgCO2e/kg)",
            min_value=0.0,
            value=DEFAULT_FACTORS["fuel_oil"],
            step=0.0001,
            format="%.4f",
        )
        electricity = st.number_input(
            "Electricity EF (kgCO2e/kWh)",
            min_value=0.0,
            value=DEFAULT_FACTORS["electricity"],
            step=0.001,
            format="%.3f",
        )

        st.divider()
        if st.button("Sign out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    return page, {
        "fuel_gas": fuel_gas,
        "fuel_oil": fuel_oil,
        "electricity": electricity,
    }


def default_scope1():
    return pd.DataFrame(
        {
            "Process Area": [
                "Utilities CH101-CH102",
                "Topping and LPG",
                "Platforming",
                "Flare System",
            ],
            "Fuel Oil kg/h": [0.0, 1940.0, 0.0, 0.0],
            "Fuel Gas kg/h": [2070.0, 790.0, 1340.0, 150.0],
            "Operating Hours": [HOURS_PER_YEAR] * 4,
        }
    )


def default_scope2():
    return pd.DataFrame(
        {
            "Facility": ["Operations", "Site Reservoir"],
            "Electricity kWh/year": [1_213_167, 226_449],
        }
    )


def default_scope3_tables():
    return {
        "cat1": pd.DataFrame(
            {
                "Product": [
                    "LPG",
                    "Unleaded Gasoline",
                    "Marine Diesel Oil (GOM)",
                    "Ultra-Low Sulfur Diesel (GOSS)",
                ],
                "Quantity t": [61_733.034, 655_722.413, 305_527.220, 106_480.850],
                "WtG EF tCO2e/t": [0.3527, 0.6183, 0.5728, 0.5812],
            }
        ),
        "cat4": pd.DataFrame(
            {
                "Route": ["Zarzaitine", "Essider (Libya)", "Azeri (Azerbaijan)"],
                "Loading Port": ["Skhira, Tunisia", "Ras Lanuf, Libya", "Ceyhan, Turkey"],
                "Cargo t": [160_009.681, 187_651.194, 618_051.110],
                "Distance km": [648.2, 833.4, 3055.8],
                "EF tCO2e/t.km": [0.006 / 1000, 0.003 / 1000, 0.003 / 1000],  # Facteurs convertis en tCO2e/t.km
            }
        ),
        "cat9": pd.DataFrame(
            {
                "Product / Route": [
                    "Domestic Kerosene - Road",
                    "Gas Oil - Road",
                    "Denatured White Spirit - Road",
                    "Low Sulfur Fuel Oil - Road to Gabes Chemical Group",
                    "Unleaded Gasoline - Road",
                    "Industrial Kerosene - Road",
                    "Sulfur-Free Diesel - Road",
                    "Premium Sulfur-Free Diesel - Road",
                    "Unleaded Gasoline - Sotrapil Pipeline",
                    "Domestic Kerosene - Sotrapil Pipeline",
                    "Motor Gas Oil (GOM) - Sotrapil Pipeline",
                    "Sulfur-Free Diesel (GOSS) - Sotrapil Pipeline",
                ],
                "Tonnage t": [
                    2_128.463,
                    98_628.972,
                    8_705.251,
                    4_349.020,
                    29_297.929,
                    3_624.203,
                    21_949.584,
                    113.824,
                    636_354.348,
                    11_001.414,
                    543_217.543,
                    99_798.792,
                ],
                "Distance km": [100, 100, 100, 470, 100, 100, 100, 100, 71, 71, 71, 71],
                "EF kgCO2e/t.km": [0.062, 0.062, 0.062, 0.062, 0.062, 0.062, 0.062, 0.062, 0.010, 0.010, 0.010, 0.010],
            }
        ),
        "cat11": pd.DataFrame(
            {
                "Product": [
                    "LPG",
                    "Unleaded Gasoline",
                    "Domestic / Industrial Kerosene",
                    "Denatured White Spirit",
                    "Ordinary Gas Oil (GOM)",
                    "Sulfur-Free Diesel (GO SS)",
                    "Low Sulfur Fuel Oil",
                ],
                "Sales t": [14_211.900, 665_652.277, 13_129.877, 8_705.251, 641_846.515, 121_862.183, 4_349.020],
                "Density t/kL": [0.550, 0.746, 0.807, 0.780, 0.849, 0.849, 0.949],
                "EF kgCO2/L": [1.55, 2.33, 2.54, 2.46, 2.68, 2.68, 2.96],
            }
        ),
        "cat6": pd.DataFrame(
            {
                "Vehicle": ["Minibus Otokar 2", "Car 1", "Car 2", "Car 3", "Car 4"],
                "Transport Type": ["Minibus", "Car", "Car", "Car", "Car"],
                "Fuel": ["Diesel", "Gasoline", "Gasoline", "Gasoline", "Gasoline"],
                "Distance km": [10_683, 45_557, 39_720, 54_751, 29_383],
                "Consumption L/100km": [25.45, 7.20, 7.24, 7.38, 8.17],
                "Fuel EF kgCO2e/L": [2.79, 3.17, 3.17, 3.17, 3.17],
            }
        ),
        "cat7": pd.DataFrame(
            {
                "Vehicle": ["Minibus HYUNDAI 09-366979", "Minibus Otokar 1"],
                "Transport Type": ["Minibus", "Minibus"],
                "Distance km": [73_014, 4_098],
                "Consumption L/100km": [13.75, 36.31],
                "Fuel EF kgCO2e/L": [2.79, 2.79],
            }
        ),
    }


def init_scope3_data():
    for key, value in default_scope3_tables().items():
        st.session_state.setdefault(f"scope3_{key}", value)


def calculate_scope1(df, factors):
    result = df.copy()
    result["Emissions tCO2e/h"] = (
        (result["Fuel Oil kg/h"] * factors["fuel_oil"])
        + (result["Fuel Gas kg/h"] * factors["fuel_gas"])
    ) / 1000
    result["Emissions tCO2e/year"] = (
        (result["Fuel Oil kg/h"] * factors["fuel_oil"])
        + (result["Fuel Gas kg/h"] * factors["fuel_gas"])
    ) * result["Operating Hours"] / 1000
    return result


def calculate_scope2(df, factors):
    result = df.copy()
    result["Emissions tCO2e/year"] = result["Electricity kWh/year"] * factors["electricity"] / 1000
    return result


def calculate_scope3(tables):
    cat1 = tables["cat1"].copy()
    cat1["Emissions tCO2e"] = cat1["Quantity t"] * cat1["WtG EF tCO2e/t"]

    cat4 = tables["cat4"].copy()
    cat4["Emissions tCO2e"] = cat4["Cargo t"] * cat4["Distance km"] * cat4["EF tCO2e/t.km"]

    cat9 = tables["cat9"].copy()
    cat9["Emissions tCO2e"] = cat9["Tonnage t"] * cat9["Distance km"] * cat9["EF kgCO2e/t.km"] / 1000

    cat11 = tables["cat11"].copy()
    cat11["Emissions tCO2e"] = (cat11["Sales t"] / cat11["Density t/kL"]) * cat11["EF kgCO2/L"]

    cat6 = tables["cat6"].copy()
    cat6["Emissions tCO2e"] = (
        cat6["Distance km"] * (cat6["Consumption L/100km"] / 100) * cat6["Fuel EF kgCO2e/L"] / 1000
    )

    cat7 = tables["cat7"].copy()
    cat7["Emissions tCO2e"] = (
        cat7["Distance km"] * (cat7["Consumption L/100km"] / 100) * cat7["Fuel EF kgCO2e/L"] / 1000
    )

    calculated = {
        "cat1": cat1,
        "cat4": cat4,
        "cat6": cat6,
        "cat7": cat7,
        "cat9": cat9,
        "cat11": cat11,
    }
    totals = {name: df["Emissions tCO2e"].sum() for name, df in calculated.items()}
    return calculated, totals


def metric_row(scope1, scope2, scope3):
    total = scope1 + scope2 + scope3
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scope 1 (tCO2e)", format_tonnes(scope1), help="Direct combustion and refinery operating sources")
    c2.metric("Scope 2 (tCO2e)", format_tonnes(scope2), help="Purchased electricity")
    c3.metric("Scope 3 (MtCO2e)", format_mt(scope3), help="Value chain emissions")
    c4.metric("Total Footprint (MtCO2e)", format_mt(total), help="Scope 1 + Scope 2 + Scope 3")
    return total


def executive_dashboard():
    app_header("Executive Dashboard", "Carbon footprint overview across direct operations, power and value chain.")
    s1 = st.session_state.scope1_total
    s2 = st.session_state.scope2_total
    s3 = st.session_state.scope3_total
    total = metric_row(s1, s2, s3)

    st.divider()
    left, right = st.columns([1.2, 1])

    with left:
        waterfall = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "total"],
                x=["Scope 1", "Scope 2", "Scope 3", "Total"],
                y=[s1, s2, s3, total],
                text=[format_tonnes(s1), format_tonnes(s2), format_mt(s3), format_mt(total)],
                connector={"line": {"color": "#94a3b8"}},
                increasing={"marker": {"color": "#0f766e"}},
                totals={"marker": {"color": "#111827"}},
            )
        )
        waterfall.update_layout(
            title="Corporate Footprint Bridge",
            yaxis_title="tCO2e",
            height=420,
            margin=dict(l=20, r=20, t=55, b=20),
        )
        st.plotly_chart(waterfall, use_container_width=True)

    with right:
        mix_df = pd.DataFrame(
            {
                "Scope": ["Scope 1", "Scope 2", "Scope 3"],
                "Emissions tCO2e": [s1, s2, s3],
            }
        )
        donut = px.pie(
            mix_df,
            names="Scope",
            values="Emissions tCO2e",
            hole=0.55,
            color="Scope",
            color_discrete_map={
                "Scope 1": "#0f766e",
                "Scope 2": "#f59e0b",
                "Scope 3": "#334155",
            },
        )
        donut.update_layout(title="Emission Mix", height=420, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(donut, use_container_width=True)

    st.info("Tip: enter or update operational data in Scope 1 and 2, then Scope 3, to refresh this dashboard.")


def scope_1_2_page(factors):
    app_header("Scope 1 and Scope 2", "Manage refinery direct emissions and purchased electricity.")
    tab_scope1, tab_scope2 = st.tabs(["Scope 1 - Direct Operations", "Scope 2 - Purchased Electricity"])

    with tab_scope1:
        st.subheader("Input Data")
        st.markdown('<p class="section-note">Edit process areas, fuel flow rates and annual operating hours.</p>', unsafe_allow_html=True)
        edited = st.data_editor(
            default_scope1(),
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="scope1_editor",
            column_config=decimal_column_config(default_scope1()),
        )
        calculated = calculate_scope1(edited, factors)
        total = calculated["Emissions tCO2e/year"].sum()
        st.session_state.scope1_total = total

        st.subheader("Output Results")
        hourly_total = calculated["Emissions tCO2e/h"].sum()
        m1, m2 = st.columns(2)
        m1.metric("Scope 1 Rate (tCO2e/h)", format_number(hourly_total))
        m2.metric("Scope 1 Annual (tCO2e/year)", format_tonnes(total))
        scope1_results = calculated[["Process Area", "Emissions tCO2e/h", "Emissions tCO2e/year"]].copy()
        scope1_results["Emissions tCO2e/h"] = scope1_results["Emissions tCO2e/h"].round(1)
        scope1_results["Emissions tCO2e/year"] = scope1_results["Emissions tCO2e/year"].round(1)
        fig = px.bar(
            scope1_results,
            x="Process Area",
            y="Emissions tCO2e/year",
            color="Process Area",
            title="Scope 1 Emissions by Process Area",
        )
        fig.update_layout(showlegend=False, height=390, margin=dict(l=20, r=20, t=55, b=80))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            scope1_results,
            hide_index=True,
            use_container_width=True,
            column_config=decimal_column_config(scope1_results),
        )

    with tab_scope2:
        st.subheader("Input Data")
        st.markdown('<p class="section-note">Track annual grid electricity and apply the selected grid emission factor.</p>', unsafe_allow_html=True)
        edited = st.data_editor(
            default_scope2(),
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="scope2_editor",
            column_config=decimal_column_config(default_scope2()),
        )
        calculated = calculate_scope2(edited, factors)
        total = calculated["Emissions tCO2e/year"].sum()
        st.session_state.scope2_total = total

        st.subheader("Output Results")
        st.metric("Total Scope 2 (tCO2e/year)", format_tonnes(total))
        scope2_results = calculated[["Facility", "Emissions tCO2e/year"]].copy()
        scope2_results["Emissions tCO2e/year"] = scope2_results["Emissions tCO2e/year"].round(1)
        fig = px.bar(
            scope2_results,
            x="Facility",
            y="Emissions tCO2e/year",
            color="Facility",
            title="Scope 2 Emissions by Facility",
        )
        fig.update_layout(showlegend=False, height=390, margin=dict(l=20, r=20, t=55, b=60))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            scope2_results,
            hide_index=True,
            use_container_width=True,
            column_config=decimal_column_config(scope2_results),
        )


def scope3_page():
    app_header("Scope 3 Value Chain", "GHG Protocol categories for refinery supplier, logistics and product-use emissions.")
    init_scope3_data()
    tables = {key: st.session_state[f"scope3_{key}"] for key in SCOPE3_CATEGORIES}
    calculated, totals = calculate_scope3(tables)

    total_scope3 = sum(totals.values())
    st.session_state.scope3_total = total_scope3

    c1, c2, c3 = st.columns(3)
    c1.metric("Scope 3 Total (MtCO2e)", format_mt(total_scope3))
    largest_key = max(totals, key=totals.get)
    c2.metric("Largest Category", SCOPE3_CATEGORIES[largest_key]["short"])
    c3.metric("Categories Tracked", str(len(totals)))

    st.divider()
    summary_df = pd.DataFrame(
        {
            "Category": [SCOPE3_CATEGORIES[key]["label"] for key in totals],
            "Emissions tCO2e": [round(value, 1) for value in totals.values()],
        }
    ).sort_values("Emissions tCO2e", ascending=False)
    fig = px.bar(
        summary_df,
        x="Emissions tCO2e",
        y="Category",
        orientation="h",
        title="Scope 3 Hotspots",
        color="Emissions tCO2e",
        color_continuous_scale=["#ccfbf1", "#0f766e", "#111827"],
    )
    fig.update_layout(height=430, margin=dict(l=20, r=20, t=55, b=20), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Category Workspace")
    category_options = {config["label"]: key for key, config in SCOPE3_CATEGORIES.items()}
    selected_label = st.selectbox("GHG Protocol category", list(category_options.keys()))
    selected_key = category_options[selected_label]
    selected_config = SCOPE3_CATEGORIES[selected_key]

    st.markdown(f'<p class="section-note">{selected_config["description"]}</p>', unsafe_allow_html=True)

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Input Data")
        edited = st.data_editor(
            st.session_state[f"scope3_{selected_key}"],
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{selected_key}",
            column_config=decimal_column_config(st.session_state[f"scope3_{selected_key}"]),
        )
        st.session_state[f"scope3_{selected_key}"] = edited

    updated_tables = {key: st.session_state[f"scope3_{key}"] for key in SCOPE3_CATEGORIES}
    updated_calculated, updated_totals = calculate_scope3(updated_tables)
    st.session_state.scope3_total = sum(updated_totals.values())
    selected_results = updated_calculated[selected_key]
    item_column = selected_config["item_column"]

    result_view = selected_results[[item_column, "Emissions tCO2e"]].copy()
    result_view = result_view.rename(columns={item_column: "Source", "Emissions tCO2e": "Emissions"})
    result_view["Emissions"] = result_view["Emissions"].round(2)

    with right:
        st.subheader("Output Results")
        st.metric(f"{selected_config['short']} Total (tCO2e)", format_tonnes(updated_totals[selected_key]))
        mini_fig = px.bar(
            result_view,
            x="Emissions",
            y="Source",
            orientation="h",
            title="Emission Contribution",
            color="Emissions",
            color_continuous_scale=["#ccfbf1", "#0f766e", "#111827"],
        )
        mini_fig.update_layout(
            height=360,
            margin=dict(l=20, r=20, t=55, b=20),
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
        )
        st.plotly_chart(mini_fig, use_container_width=True)
        st.dataframe(
            result_view,
            hide_index=True,
            use_container_width=True,
            column_config=decimal_column_config(result_view),
        )


def reports_page():
    app_header("Reports", "Export a clean emissions summary for internal review.")
    data = pd.DataFrame(
        {
            "Scope": ["Scope 1", "Scope 2", "Scope 3", "Total"],
            "Unit": ["tCO2e", "tCO2e", "MtCO2e", "MtCO2e"],
            "Value": [
                round(st.session_state.scope1_total, 1),
                round(st.session_state.scope2_total, 1),
                round(st.session_state.scope3_total / 1_000_000, 1),
                round(
                    (st.session_state.scope1_total + st.session_state.scope2_total + st.session_state.scope3_total)
                    / 1_000_000,
                    1,
                ),
            ],
        }
    )
    st.dataframe(data, hide_index=True, use_container_width=True, column_config=decimal_column_config(data))
    st.download_button(
        "Download CSV report",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="refinery_carbon_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Inventory Notes")
    st.text_area(
        "Management notes",
        value=(
            "Scope 1 includes fuel gas, fuel oil and flare combustion sources. "
            "Scope 2 uses the selected grid electricity factor. "
            "Scope 3 includes purchased products, logistics, sold product use, business travel and commuting."
        ),
        height=130,
    )


def main():
    configure_page()
    init_state()

    if not st.session_state.authenticated:
        login_screen()
        return

    page, factors = sidebar_controls()
    if page == "Executive Dashboard":
        executive_dashboard()
    elif page == "Scope 1 and 2":
        scope_1_2_page(factors)
    elif page == "Scope 3":
        scope3_page()
    elif page == "Reports":
        reports_page()


if __name__ == "__main__":
    main()