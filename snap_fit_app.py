import streamlit as st
import pandas as pd
import os

# ✅ Page setup
st.set_page_config(page_title="Snap Fit App", layout="wide")

EXCEL_FILE = "Snap Fit  calculation.xlsm"
SHEET_MAP = {
    "Cantilever Snap": "Cantilever Snap",
    "L Shaped Snap": '"L" Shaped',
    "U Shaped Snap": '"U" Shaped'
}

@st.cache_data
def load_sheet(sheet_name):
    return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)

@st.cache_data
def load_and_format_material_ref(sheet_name="Material Prop Ref."):
    raw = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None)
    raw.dropna(how="all", inplace=True)
    raw.dropna(axis=1, how="all", inplace=True)
    raw.columns = raw.iloc[0].astype(str).str.strip()
    df = raw[1:].reset_index(drop=True)
    df.columns = df.columns.map(str).str.strip()
    df = df.astype(str)
    return df

# -------- Sidebar --------
st.sidebar.title("📂 Snap Fit Selector")
snap_type = st.sidebar.selectbox("Select Snap Fit Type", list(SHEET_MAP.keys()))
sheet_name = SHEET_MAP[snap_type]

# 📷 Sidebar images based on selection
st.sidebar.markdown("---")
snap_images = {
    "Cantilever Snap": ["Q factor selection.png", "Beam Type.png", "Beam.png"],
    "L Shaped Snap": ["L Shaped snap.png"],
    "U Shaped Snap": ["U Shaped snap case 1.png", "U Shaped snap case 2.png"]
}
for img_file in snap_images.get(snap_type, []):
    if os.path.exists(img_file):
        st.sidebar.image(img_file, caption=os.path.splitext(img_file)[0], use_container_width=True)
    else:
        st.sidebar.warning(f"⚠️ {img_file} not found")

# -------- Load Excel --------
df = load_sheet(sheet_name)
material_ref_df = load_and_format_material_ref()
st.title("🧩 Snap Fit Design Calculator")

# -------- Inputs --------
def extract_input_value(df, label):
    try:
        return float(df[df[1] == label].iloc[0, 4])
    except:
        return 0.0

inputs = {
    "Flexural Modulus E (GPa)": extract_input_value(df, "Flexural Modulus"),
    "Permissible Strain ε0 (%)": extract_input_value(df, "Permissible Strain"),
    "Coefficient of Friction μ": extract_input_value(df, "Coefficient of Friction"),
    "Beam Thickness t (mm)": extract_input_value(df, "Beam Thickness"),
    "Beam Length L (mm)": extract_input_value(df, "Beam Length"),
    "Beam Width b (mm)": extract_input_value(df, "Beam Width"),
    "Lead Angle α (°)": extract_input_value(df, "Lead Angle"),
    "Return Angle α′ (°)": extract_input_value(df, "Return Angle"),
    "Deflection Y (mm)": extract_input_value(df, "Deflection"),
    "Q Factor": extract_input_value(df, "Q Factor")
}

# -------- Layout: Inputs + Reference --------
col_form, col_ref = st.columns([2, 1])

with col_form:
    with st.form("input_form"):
        st.header(f"📝 Input Parameters ({snap_type})")
        user_inputs = {}
        for label, default_val in inputs.items():
            user_inputs[label] = st.number_input(label, value=default_val)
        submitted = st.form_submit_button("🚀 Submit")

with col_ref:
    st.header("📚 Material Reference")

    center_cols = ["Permissible Strain", "Flexural Modulus", "Coefficient of Friction"]
    col_styles = []
    for col in material_ref_df.columns:
        col_idx = material_ref_df.columns.get_loc(col)
        col_styles.append({
            'selector': f'th.col{col_idx}',
            'props': [('text-align', 'center'), ('font-weight', 'bold')]
        })
    col_styles.append({
        'selector': 'th',
        'props': [('text-align', 'center'), ('font-weight', 'bold'), ('background-color', '#f0f0f0')]
    })

    styled_df = material_ref_df.style.set_table_styles(col_styles)
    for col in material_ref_df.columns:
        align = 'center' if col.strip() in center_cols else 'left'
        styled_df = styled_df.set_properties(subset=[col], **{'text-align': align})

    st.markdown(styled_df.to_html(), unsafe_allow_html=True)

# -------- Output Results --------
if submitted:
    st.subheader("📄 Output Results")

    def get_output(label_keyword):
        matches = df[df.apply(lambda row: row.astype(str).str.contains(label_keyword, case=False, na=False).any(), axis=1)]
        if not matches.empty:
            return matches.iloc[0].dropna().values[-1]
        return None

    if snap_type == "Cantilever Snap":
        output_rows = [
            ["Max Strain", "ε", "%", get_output("Max Strain")],
            ["Max Deflection", "Y", "mm", get_output("Max Deflection")],
            ["Deflection Force", "P", "N", get_output("Deflection Force")],
            ["Push-on Force", "W", "N", get_output("Push-on Force")],
            ["Pull-off Force", "W'", "N", get_output("Pull-off Force")]
        ]
        df_out = pd.DataFrame(output_rows, columns=["Label", "Symbol", "Unit", "Value"])
        st.table(df_out)

    elif snap_type == "L Shaped Snap":
        output_rows = [
            ["Max Strain", "ε", "%", get_output("Max Strain")],
            ["Minimum Leg Length", "L2", "mm", "Input Strain"],
            ["Max Deflection", "Y", "mm", "Input Strain"],
            ["Deflection Force", "P", "N", get_output("Deflection Force")],
            ["Deflection Force", "P", "Lbf", get_output("Deflection Force Lbf")],
        ]
        df_out = pd.DataFrame(output_rows, columns=["Label", "Symbol", "Unit", "Value"])
        st.table(df_out)

    elif snap_type == "U Shaped Snap":
        output_rows = [
            ["Max Strain", "ε", "%", get_output("Max Strain"), "Input Thickness"],
            ["Max Deflection", "Y", "mm", get_output("Max Deflection"), "Input Thickness"],
            ["Deflection Force", "P", "N", get_output("Deflection Force"), "Input Thickness"],
            ["Deflection Force", "P", "Lbf", get_output("Deflection Force Lbf"), "-"]
        ]
        df_out = pd.DataFrame(output_rows, columns=["Label", "Symbol", "Unit", "Case 1", "Case 2"])
        st.table(df_out)

    # Diagram (optional)
    st.subheader("📷 Visualization (Optional Diagram)")
    image_link = None
    for col in df.columns:
        if df[col].astype(str).str.contains("http").any():
            image_link = df[df[col].astype(str).str.contains("http", na=False)].iloc[0, col]
            break
    if image_link:
        st.image(image_link, caption="Snap Fit Diagram", use_column_width=True)
    else:
        st.info("No image link found in the sheet.")

# Footer
st.caption("📘 Snap Fit Engineering Tool · Dynamic Output v4.1")
