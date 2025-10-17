import streamlit as st
import pandas as pd
import os
import math

# --- Page Setup ---
st.set_page_config(page_title="Snap Fit Design Calculator", layout="wide", page_icon="🔧")

# --- Constants and Configuration ---
EXCEL_FILE = "Snap Fit  calculation.xlsm"
SHEET_MAP = {
    "Cantilever Snap": "Cantilever Snap",
    "L Shaped Snap": '"L" Shaped',
    "U Shaped Snap": '"U" Shaped'
}

# --- Caching Functions for Performance ---
@st.cache_data
def load_sheet(sheet_name):
    """Loads a specific sheet from the Excel file."""
    try:
        return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)
    except FileNotFoundError:
        st.error(f"FATAL ERROR: The file '{EXCEL_FILE}' was not found. Please ensure it is in the correct directory.")
        return None
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return None

@st.cache_data
def load_and_format_material_ref(sheet_name="Material Prop Ref."):
    """Loads and cleans the material properties reference sheet."""
    try:
        raw = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)
        raw.dropna(how="all", inplace=True)
        raw.dropna(axis=1, how="all", inplace=True)
        raw.columns = raw.iloc[0].astype(str).str.strip()
        df = raw[1:].reset_index(drop=True)
        df.columns = df.columns.map(str).str.strip()
        # Convert all data to strings to prevent type errors
        return df.astype(str)
    except Exception as e:
        st.warning(f"Could not load material reference sheet: {e}")
        return pd.DataFrame()

# --- Core Calculation Functions ---
def calculate_cantilever_snap(E_gpa, t, L, b, y, mu, alpha_deg, alpha_prime_deg, q):
    """Performs all calculations for a Cantilever Snap Fit."""
    if L == 0 or t == 0 or b == 0:
        return {"error": "Beam dimensions (L, t, b) cannot be zero."}

    E_mpa = E_gpa * 1000
    alpha_rad = math.radians(alpha_deg)
    alpha_prime_rad = math.radians(alpha_prime_deg)

    strain = (3 * y * t) / (2 * L**2) * q
    strain_percent = strain * 100
    deflection_force = (E_mpa * b * y) / q * ((t / L)**3) / 4
    tan_alpha = math.tan(alpha_rad)
    push_on_force = deflection_force * (mu + tan_alpha) / (1 - mu * tan_alpha) if (1 - mu * tan_alpha) != 0 else float('inf')
    tan_alpha_prime = math.tan(alpha_prime_rad)
    pull_off_force = deflection_force * (tan_alpha_prime - mu) / (1 + mu * tan_alpha_prime) if (1 + mu * tan_alpha_prime) != 0 else float('inf')

    return {
        "Max Strain": strain_percent,
        "Deflection Force": deflection_force,
        "Push-on Force": push_on_force,
        "Pull-off Force": pull_off_force,
        "error": None
    }

# --- UI and Application Flow ---
df_sheet = load_sheet(list(SHEET_MAP.values())[0])
if df_sheet is None:
    st.stop()

material_ref_df = load_and_format_material_ref()

st.sidebar.title("📂 Snap Fit Selector")
snap_type = st.sidebar.selectbox("Select Snap Fit Type", list(SHEET_MAP.keys()))
sheet_name = SHEET_MAP[snap_type]
df = load_sheet(sheet_name)

st.sidebar.markdown("---")
snap_images = {
    "Cantilever Snap": ["Q factor selection.png", "Beam Type.png", "Beam.png"],
    "L Shaped Snap": ["L Shaped snap.png"],
    "U Shaped Snap": ["U Shaped snap case 1.png", "U Shaped snap case 2.png"]
}
for img_file in snap_images.get(snap_type, []):
    if os.path.exists(img_file):
        st.sidebar.image(img_file, use_container_width=True)
    else:
        st.sidebar.warning(f"Image not found: {img_file}")

st.title(f"🧩 {snap_type} Design Calculator")

def extract_input_value(df, label):
    try:
        return float(df[df[1] == label].iloc[0, 4])
    except (ValueError, IndexError, TypeError):
        return 0.0

inputs = {}
if snap_type == "Cantilever Snap":
    inputs = {
        "Flexural Modulus E (GPa)": extract_input_value(df, "Flexural Modulus"),
        "Permissible Strain ε (%)": extract_input_value(df, "Permissible Strain"),
        "Coefficient of Friction μ": extract_input_value(df, "Coefficient of Friction"),
        "Beam Thickness t (mm)": extract_input_value(df, "Beam Thickness"),
        "Beam Length L (mm)": extract_input_value(df, "Beam Length"),
        "Beam Width b (mm)": extract_input_value(df, "Beam Width"),
        "Lead Angle α (°)": extract_input_value(df, "Lead Angle"),
        "Return Angle α′ (°)": extract_input_value(df, "Return Angle"),
        "Deflection Y (mm)": extract_input_value(df, "Deflection"),
        "Q Factor": extract_input_value(df, "Q Factor")
    }

col_form, col_ref = st.columns([2, 1])

with col_form:
    with st.form("input_form"):
        st.header("📝 Input Parameters")
        user_inputs = {label: st.number_input(label, value=val, format="%.2f") for label, val in inputs.items()}
        submitted = st.form_submit_button("🚀 Calculate Results")

with col_ref:
    st.header("📚 Material Reference")
    if not material_ref_df.empty:
        # ** THIS IS THE FIX **
        # Using st.table() is more robust for data from Excel.
        st.table(material_ref_df)
    else:
        st.info("Material reference data is not available.")

if submitted:
    st.markdown("---")
    st.subheader("📄 Output Results")

    if snap_type == "Cantilever Snap":
        calc_inputs = {
            "E_gpa": user_inputs["Flexural Modulus E (GPa)"],
            "t": user_inputs["Beam Thickness t (mm)"],
            "L": user_inputs["Beam Length L (mm)"],
            "b": user_inputs["Beam Width b (mm)"],
            "y": user_inputs["Deflection Y (mm)"],
            "mu": user_inputs["Coefficient of Friction μ"],
            "alpha_deg": user_inputs["Lead Angle α (°)"],
            "alpha_prime_deg": user_inputs["Return Angle α′ (°)"],
            "q": user_inputs["Q Factor"]
        }
        
        results = calculate_cantilever_snap(**calc_inputs)
        
        if results.get("error"):
            st.error(results["error"])
        else:
            permissible_strain = user_inputs["Permissible Strain ε (%)"]
            col1, col2 = st.columns(2)
            is_safe = results["Max Strain"] < permissible_strain
            
            with col1:
                st.metric(
                    label="Maximum Calculated Strain (ε)",
                    value=f"{results['Max Strain']:.3f} %",
                    delta=f"Limit: {permissible_strain:.2f} %",
                    delta_color="inverse" if is_safe else "normal"
                )
            
            with col2:
                if is_safe:
                    st.success("✅ **Design is SAFE**")
                else:
                    st.error("❌ **Design WILL LIKELY FAIL**")

            force_data = {
                "Metric": ["Deflection Force (P)", "Push-on Force (W)", "Pull-off Force (W')"],
                "Force (N)": [
                    f"{results['Deflection Force']:.2f}",
                    f"{results['Push-on Force']:.2f}",
                    f"{results['Pull-off Force']:.2f}"
                ]
            }
            st.table(pd.DataFrame(force_data))

    elif snap_type in ["L Shaped Snap", "U Shaped Snap"]:
        st.info(f"Calculation logic for {snap_type} is not yet implemented.")

st.markdown("---")
st.caption("📘 Snap Fit Engineering Tool · Powered by Python & Streamlit")
