import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


APP_TITLE = "Carbon Manager"
APP_SUBTITLE = "Industrial carbon accounting and refinery GHG intelligence"
HOURS_PER_YEAR = 8760

DEFAULT_FACTORS = {
    "fuel_gas": 2.7016,
    "fuel_oil": 3.1533,
    "natural_gas_scope1": 2.7500,
    "electricity": 0.530,
    "purchased_natural_gas": 0.2020,
}

PAGES = ["scope1", "scope2", "scope3", "results", "report"]
PAGE_LABELS = {
    "scope1": "Scope 1",
    "scope2": "Scope 2",
    "scope3": "Scope 3",
    "results": "Results",
    "report": "Report",
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
        "description": "Inbound transport of crude oil, feedstock and purchased products before refinery ownership. Factors are automatically scaled (/1000).",
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
        page_icon=":factory:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
            :root {
                --bg: #e8edf2;
                --panel: #ffffff;
                --ink: #0b1f3a;
                --muted: #58708d;
                --line: #cfd8e3;
                --brand: #a83b18;
                --brand-dark: #7c2d12;
                --primary: #0f766e;
                --primary-soft: #dff8f3;
                --blue: #d8e3ef;
                --green: #16a34a;
                --red: #ef4444;
            }

            .stApp {
                background: var(--bg);
            }

            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 2.4rem;
                max-width: 1760px;
            }

            header[data-testid="stHeader"],
            div[data-testid="stToolbar"],
            #MainMenu,
            footer {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }

            h1, h2, h3 {
                color: var(--ink);
                letter-spacing: 0;
            }

            section[data-testid="stSidebar"],
            div[data-testid="stSidebar"],
            div[data-testid="stSidebarCollapsedControl"],
            [data-testid="collapsedControl"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
            }

            .top-shell {
                display: flex;
                justify-content: space-between;
                gap: 20px;
                align-items: center;
                margin-bottom: 22px;
            }

            .brand-lockup {
                display: flex;
                gap: 12px;
                align-items: center;
                min-width: 420px;
            }

            .brand-mark {
                width: 66px;
                height: 66px;
                border: 2px solid var(--brand);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
                position: relative;
                overflow: hidden;
            }

            .brand-mark.carbon-logo {
                background:
                    radial-gradient(circle at 66% 22%, #dcfce7 0 8px, transparent 9px),
                    linear-gradient(#334155, #334155) 33px 11px / 4px 28px no-repeat,
                    linear-gradient(#a83b18, #a83b18) 24px 22px / 8px 27px no-repeat,
                    linear-gradient(#d97706, #d97706) 12px 29px / 8px 20px no-repeat,
                    linear-gradient(#334155, #334155) 42px 31px / 7px 18px no-repeat,
                    linear-gradient(115deg, transparent 0 27%, #0b1f3a 28% 35%, transparent 36% 100%) 8px 29px / 39px 15px no-repeat,
                    linear-gradient(#7c2d12, #7c2d12) 8px 48px / 44px 3px no-repeat,
                    linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
            }

            .brand-mark.carbon-logo::before {
                content: "";
                position: absolute;
                left: 12px;
                top: 12px;
                width: 36px;
                height: 36px;
                border: 3px solid rgba(15, 118, 110, 0.88);
                border-right-color: transparent;
                border-radius: 50%;
                transform: rotate(-28deg);
            }

            .brand-mark.carbon-logo::after {
                content: "";
                position: absolute;
                right: 15px;
                top: 8px;
                width: 19px;
                height: 12px;
                border-radius: 100% 0 100% 0;
                background: #16a34a;
                transform: rotate(20deg);
                box-shadow: -14px 30px 0 -6px rgba(15, 118, 110, 0.22);
            }

            .brand-title {
                margin: 0;
                font-size: 15px;
                line-height: 1.05;
                font-weight: 900;
                color: var(--ink);
                letter-spacing: 0.5px;
                white-space: nowrap;
            }

            .page-title {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 18px;
                margin: 12px 0 18px;
                border-bottom: 1px solid var(--line);
                padding-bottom: 15px;
            }

            .page-title h2 {
                margin: 0;
                font-size: 28px;
            }

            .page-title p {
                margin: 4px 0 0;
                color: var(--muted);
            }

            .metric-card {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 18px 16px;
                min-height: 116px;
            }

            .metric-label {
                color: var(--ink);
                font-size: 15px;
                margin-bottom: 8px;
            }

            .metric-value {
                color: #020617;
                font-size: 32px;
                line-height: 1.1;
            }

            .metric-chip {
                display: inline-block;
                margin-top: 10px;
                border-radius: 999px;
                padding: 4px 9px;
                color: #15803d;
                background: #dcfce7;
                font-size: 13px;
            }

            .section-note {
                color: var(--muted);
                font-size: 14px;
                margin-top: -4px;
                margin-bottom: 12px;
            }

            .soft-panel {
                background: rgba(255,255,255,.55);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 18px;
                margin-bottom: 16px;
            }

            .report-panel {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 18px;
            }

            .right-action {
                display: flex;
                justify-content: flex-end;
                margin-top: 18px;
            }

            div[data-testid="stButton"] > button {
                border-radius: 8px;
                border: 1px solid #aab7c5;
                background: #f8fafc;
                color: #0b1f3a;
                min-height: 52px;
                font-size: 18px;
                font-weight: 600;
            }

            div[data-testid="stButton"] > button:hover {
                border-color: #8aa0ba;
                color: #0b1f3a;
            }

            .stDownloadButton > button {
                border-radius: 8px;
                min-height: 52px;
                font-size: 18px;
                font-weight: 600;
            }

            .run-button button {
                background: #dcfce7 !important;
                border-color: #16a34a !important;
                color: #14532d !important;
            }

            .next-button button {
                min-width: 190px;
                background: #d8e3ef !important;
            }

            .status-bar {
                color: var(--muted);
                font-size: 14px;
                margin: 8px 0 16px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
            "Natural Gas kg/h": [0.0, 0.0, 0.0, 0.0],
            "Operating Hours": [HOURS_PER_YEAR] * 4,
        }
    )


def default_scope2():
    return pd.DataFrame(
        {
            "Facility": ["Operations", "Site Reservoir"],
            "Electricity kWh/year": [1_213_167, 226_449],
            "Purchased Natural Gas kWh/year": [0.0, 0.0],
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
                "EF tCO2e/t.km": [0.006, 0.003, 0.003],
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


def init_state():
    defaults = {
        "authenticated": False,
        "page": "scope1",
        "report_notes": "Scope 1 includes fuel gas, fuel oil and flare combustion sources. Scope 2 uses the default grid electricity factor. Scope 3 includes purchased products, logistics, sold product use, business travel and commuting.",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    st.session_state.setdefault("scope1_data", default_scope1())
    st.session_state.setdefault("scope2_data", default_scope2())
    for key, value in default_scope3_tables().items():
        st.session_state.setdefault(f"scope3_{key}", value)
    ensure_case_schema()


def ensure_columns(df, template):
    result = df.copy()
    for column in template.columns:
        if column not in result.columns:
            if pd.api.types.is_numeric_dtype(template[column]):
                result[column] = 0.0
            else:
                result[column] = ""
    return result[template.columns]


def ensure_case_schema():
    st.session_state.scope1_data = ensure_columns(st.session_state.scope1_data, default_scope1())
    st.session_state.scope2_data = ensure_columns(st.session_state.scope2_data, default_scope2())


def reset_case():
    st.session_state.scope1_data = default_scope1()
    st.session_state.scope2_data = default_scope2()
    for key, value in default_scope3_tables().items():
        st.session_state[f"scope3_{key}"] = value
    st.session_state.report_notes = (
        "Scope 1 includes fuel gas, fuel oil and flare combustion sources. "
        "Scope 2 uses the default grid electricity factor. "
        "Scope 3 includes purchased products, logistics, sold product use, business travel and commuting."
    )
    st.session_state.page = "scope1"


def build_case_json():
    case = {
        "app": APP_TITLE,
        "scope1_data": st.session_state.scope1_data.to_dict(orient="records"),
        "scope2_data": st.session_state.scope2_data.to_dict(orient="records"),
        "scope3_data": {
            key: st.session_state[f"scope3_{key}"].to_dict(orient="records")
            for key in SCOPE3_CATEGORIES
        },
        "report_notes": st.session_state.report_notes,
    }
    return json.dumps(case, indent=2).encode("utf-8")


def login_screen():
    left, center, right = st.columns([1.2, 1, 1.2])
    with center:
        st.markdown(
            """
            <div class="top-shell" style="justify-content:center;">
                <div class="brand-lockup" style="min-width:auto;">
                    <div class="brand-mark carbon-logo" aria-label="Industrial carbon manager logo"></div>
                    <div>
                        <h1 class="brand-title">CARBON<br>MANAGER</h1>
                    </div>
                </div>
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


def top_header():
    st.markdown(
        f"""
        <div class="top-shell">
            <div class="brand-lockup">
                <div class="brand-mark carbon-logo" aria-label="Industrial carbon manager logo"></div>
                <div>
                    <h1 class="brand-title">CARBON<br>MANAGER</h1>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_cols = st.columns([1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.95])
    for col, page_key in zip(nav_cols[:5], PAGES):
        label = PAGE_LABELS[page_key]
        active = st.session_state.page == page_key
        if col.button(label, use_container_width=True, disabled=active):
            st.session_state.page = page_key
            st.rerun()

    nav_cols[5].download_button(
        "Save",
        data=build_case_json(),
        file_name="carbon_manager_case.json",
        mime="application/json",
        use_container_width=True,
    )

    if nav_cols[6].button("New case", use_container_width=True):
        reset_case()
        st.rerun()


def page_title(title, subtitle, action=None):
    action_html = action or ""
    st.markdown(
        f"""
        <div class="page-title">
            <div>
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
            <div>{action_html}</div>
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
        column: st.column_config.NumberColumn(column, format="%.3f" if "EF " in column else "%.1f")
        for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
    }


def calculate_scope1(df, factors=DEFAULT_FACTORS):
    result = df.copy()
    direct_emissions_kg_per_h = (
        (result["Fuel Oil kg/h"] * factors["fuel_oil"])
        + (result["Fuel Gas kg/h"] * factors["fuel_gas"])
        + (result["Natural Gas kg/h"] * factors["natural_gas_scope1"])
    )
    result["Emissions tCO2e/h"] = (
        direct_emissions_kg_per_h / 1000
    )
    result["Emissions tCO2e/year"] = direct_emissions_kg_per_h * result["Operating Hours"] / 1000
    return result


def calculate_scope2(df, factors=DEFAULT_FACTORS):
    result = df.copy()
    result["Electricity Emissions tCO2e/year"] = result["Electricity kWh/year"] * factors["electricity"] / 1000
    result["Purchased Natural Gas Emissions tCO2e/year"] = (
        result["Purchased Natural Gas kWh/year"] * factors["purchased_natural_gas"] / 1000
    )
    result["Emissions tCO2e/year"] = (
        result["Electricity Emissions tCO2e/year"]
        + result["Purchased Natural Gas Emissions tCO2e/year"]
    )
    return result


def calculate_scope3(tables):
    cat1 = tables["cat1"].copy()
    cat1["Emissions tCO2e"] = cat1["Quantity t"] * cat1["WtG EF tCO2e/t"]

    # --- MODIFICATION DEMANDÉE : DIVISION DE LA CATÉGORIE 4 PAR 1000 ---
    cat4 = tables["cat4"].copy()
    cat4["Emissions tCO2e"] = (cat4["Cargo t"] * cat4["Distance km"] * cat4["EF tCO2e/t.km"]) / 1000

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


def get_results():
    scope1 = calculate_scope1(st.session_state.scope1_data)
    scope2 = calculate_scope2(st.session_state.scope2_data)
    scope3_tables = {key: st.session_state[f"scope3_{key}"] for key in SCOPE3_CATEGORIES}
    scope3, scope3_totals = calculate_scope3(scope3_tables)
    totals = {
        "Scope 1": float(scope1["Emissions tCO2e/year"].sum()),
        "Scope 2": float(scope2["Emissions tCO2e/year"].sum()),
        "Scope 3": float(sum(scope3_totals.values())),
    }
    totals["Total"] = totals["Scope 1"] + totals["Scope 2"] + totals["Scope 3"]
    return scope1, scope2, scope3, scope3_totals, totals


def metric_card(label, value, chip=None):
    chip_html = f'<div class="metric-chip">{chip}</div>' if chip else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {chip_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def wizard_nav(back_page=None, next_page=None, back_label="Back", next_label="Next"):
    left, middle, right = st.columns([0.55, 1.4, 0.65])
    with left:
        if st.button(back_label, use_container_width=True, disabled=back_page is None, key=f"back_{st.session_state.page}"):
            st.session_state.page = back_page
            st.rerun()
    with right:
        if st.button(next_label, use_container_width=True, disabled=next_page is None, key=f"next_{st.session_state.page}"):
            st.session_state.page = next_page
            st.rerun()


def scope1_page():
    page_title("Page 1 - Scope 1 Input Data", "Direct refinery emissions from fuel oil, fuel gas, natural gas and operating hours.")
    st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
    st.subheader("Input Data")
    edited = st.data_editor(
        st.session_state.scope1_data,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="scope1_editor",
        column_config=decimal_column_config(st.session_state.scope1_data),
    )
    st.session_state.scope1_data = edited
    st.markdown("</div>", unsafe_allow_html=True)

    wizard_nav(next_page="scope2", next_label="Next -> Scope 2")


def scope2_page():
    page_title("Page 2 - Scope 2 Input Data", "Purchased electricity and purchased natural gas energy for refinery facilities.")
    st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
    st.subheader("Input Data")
    edited = st.data_editor(
        st.session_state.scope2_data,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="scope2_editor",
        column_config=decimal_column_config(st.session_state.scope2_data),
    )
    st.session_state.scope2_data = edited
    st.markdown("</div>", unsafe_allow_html=True)

    wizard_nav(back_page="scope1", next_page="scope3", back_label="<- Back", next_label="Next -> Scope 3")


def scope3_page():
    title_left, title_right = st.columns([4, 0.85])
    with title_left:
        page_title("Page 3 - Scope 3 Input Data", "Value-chain categories for suppliers, logistics, travel, commuting and product use.")
    with title_right:
        st.markdown('<div class="run-button" style="padding-top:16px;">', unsafe_allow_html=True)
        if st.button("-> RUN", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    category_options = {config["label"]: key for key, config in SCOPE3_CATEGORIES.items()}
    selected_label = st.selectbox("GHG Protocol category", list(category_options.keys()))
    selected_key = category_options[selected_label]
    selected_config = SCOPE3_CATEGORIES[selected_key]
    st.markdown(f'<p class="section-note">{selected_config["description"]}</p>', unsafe_allow_html=True)

    edited = st.data_editor(
        st.session_state[f"scope3_{selected_key}"],
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key=f"editor_{selected_key}",
        column_config=decimal_column_config(st.session_state[f"scope3_{selected_key}"]),
    )
    st.session_state[f"scope3_{selected_key}"] = edited
    wizard_nav(back_page="scope2", next_page="results", back_label="<- Back", next_label="Next -> Results")


def dashboard_results(scope1, scope2, scope3, scope3_totals, totals):
    metric_cols = st.columns(4)
    with metric_cols[0]:
        metric_card("Scope 1 (tCO2e)", format_tonnes(totals["Scope 1"]), "Direct combustion")
    with metric_cols[1]:
        metric_card("Scope 2 (tCO2e)", format_tonnes(totals["Scope 2"]), "Purchased power")
    with metric_cols[2]:
        metric_card("Scope 3 (MtCO2e)", format_mt(totals["Scope 3"]), "Value chain")
    with metric_cols[3]:
        metric_card("Total Footprint (MtCO2e)", format_mt(totals["Total"]), "All scopes")

    st.divider()
    left, right = st.columns([1.25, 1])

    with left:
        waterfall = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "total"],
                x=["Scope 1", "Scope 2", "Scope 3", "Total"],
                y=[totals["Scope 1"], totals["Scope 2"], totals["Scope 3"], totals["Total"]],
                text=[
                    format_tonnes(totals["Scope 1"]),
                    format_tonnes(totals["Scope 2"]),
                    format_mt(totals["Scope 3"]),
                    format_mt(totals["Total"]),
                ],
                connector={"line": {"color": "#94a3b8"}},
                increasing={"marker": {"color": "#0f766e"}},
                totals={"marker": {"color": "#111827"}},
            )
        )
        waterfall.update_layout(
            title="Corporate Footprint Bridge",
            yaxis_title="tCO2e",
            height=430,
            margin=dict(l=20, r=20, t=55, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(waterfall, use_container_width=True)

    with right:
        mix_df = pd.DataFrame(
            {
                "Scope": ["Scope 1", "Scope 2", "Scope 3"],
                "Emissions tCO2e": [totals["Scope 1"], totals["Scope 2"], totals["Scope 3"]],
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
        donut.update_layout(
            title="Emission Mix",
            height=430,
            margin=dict(l=20, r=20, t=55, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(donut, use_container_width=True)

    st.subheader("Results by Scope")
    tab1, tab2, tab3 = st.tabs(["Scope 1", "Scope 2", "Scope 3"])
    with tab1:
        scope1_view = scope1[["Process Area", "Emissions tCO2e/h", "Emissions tCO2e/year"]].copy()
        scope1_view["Emissions tCO2e/h"] = scope1_view["Emissions tCO2e/h"].round(1)
        scope1_view["Emissions tCO2e/year"] = scope1_view["Emissions tCO2e/year"].round(1)
        fig = px.bar(scope1_view, x="Process Area", y="Emissions tCO2e/year", color="Process Area", title="Scope 1 Emissions by Process Area")
        fig.update_layout(showlegend=False, height=360, margin=dict(l=20, r=20, t=55, b=80))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(scope1_view, hide_index=True, use_container_width=True, column_config=decimal_column_config(scope1_view))

    with tab2:
        scope2_view = scope2[
            [
                "Facility",
                "Electricity Emissions tCO2e/year",
                "Purchased Natural Gas Emissions tCO2e/year",
                "Emissions tCO2e/year",
            ]
        ].copy()
        scope2_view = scope2_view.rename(
            columns={
                "Electricity Emissions tCO2e/year": "Electricity tCO2e/year",
                "Purchased Natural Gas Emissions tCO2e/year": "Natural Gas tCO2e/year",
            }
        )
        scope2_view["Electricity tCO2e/year"] = scope2_view["Electricity tCO2e/year"].round(1)
        scope2_view["Natural Gas tCO2e/year"] = scope2_view["Natural Gas tCO2e/year"].round(1)
        scope2_view["Emissions tCO2e/year"] = scope2_view["Emissions tCO2e/year"].round(1)
        fig = px.bar(scope2_view, x="Facility", y="Emissions tCO2e/year", color="Facility", title="Scope 2 Emissions by Facility")
        fig.update_layout(showlegend=False, height=360, margin=dict(l=20, r=20, t=55, b=60))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(scope2_view, hide_index=True, use_container_width=True, column_config=decimal_column_config(scope2_view))

    with tab3:
        scope3_summary = pd.DataFrame(
            {
                "Category": [SCOPE3_CATEGORIES[key]["label"] for key in scope3_totals],
                "Emissions tCO2e": [round(value, 1) for value in scope3_totals.values()],
            }
        ).sort_values("Emissions tCO2e", ascending=False)
        fig = px.bar(
            scope3_summary,
            x="Emissions tCO2e",
            y="Category",
            orientation="h",
            title="Scope 3 Hotspots",
            color="Emissions tCO2e",
            color_continuous_scale=["#ccfbf1", "#0f766e", "#111827"],
        )
        fig.update_layout(height=410, margin=dict(l=20, r=20, t=55, b=20), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(scope3_summary, hide_index=True, use_container_width=True, column_config=decimal_column_config(scope3_summary))


# --- RECONSTRUCTION DE LA FIN DU CODE (QUI ÉTAIT COUPÉ) ---

def results_page():
    page_title("Results Dashboard", "Consolidated carbon inventory assessment and asset visualization.")
    scope1, scope2, scope3, scope3_totals, totals = get_results()
    dashboard_results(scope1, scope2, scope3, scope3_totals, totals)
    
    st.markdown("<br>", unsafe_allow_html=True)
    wizard_nav(back_page="scope3", next_page="report", back_label="<- Back to Inputs", next_label="Next -> View Report")


def report_page():
    page_title("Compiled Inventory Report", "Audit-ready greenhouse gas asset statement and summary export.")
    scope1, scope2, scope3, scope3_totals, totals = get_results()
    
    st.markdown('<div class="report-panel">', unsafe_allow_html=True)
    st.subheader("Executive Audit Notes")
    st.session_state.report_notes = st.text_area("Observations and Methodology Documentation", value=st.session_state.report_notes, height=120)
    
    st.subheader("Carbon Accounting Summary Statement")
    summary_df = pd.DataFrame({
        "Accounting Boundary Scope": ["Scope 1 (Direct Emissions)", "Scope 2 (Indirect Emissions)", "Scope 3 (Value Chain)", "Total Corporate Footprint"],
        "Annual Metrics (tCO2e/year)": [totals["Scope 1"], totals["Scope 2"], totals["Scope 3"], totals["Total"]]
    })
    st.dataframe(summary_df, hide_index=True, use_container_width=True, column_config=decimal_column_config(summary_df))
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    wizard_nav(back_page="results", back_label="<- Back to Dashboard")


def main():
    configure_page()
    init_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        top_header()
        if st.session_state.page == "scope1":
            scope1_page()
        elif st.session_state.page == "scope2":
            scope2_page()
        elif st.session_state.page == "scope3":
            scope3_page()
        elif st.session_state.page == "results":
            results_page()
        elif st.session_state.page == "report":
            report_page()


if __name__ == "__main__":
    main()