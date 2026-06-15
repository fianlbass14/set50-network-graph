import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# ตั้งค่าฟอนต์ภาษาไทยสำหรับ Matplotlib ให้แสดงผลได้บนทุกระบบปฏิบัติการ
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Tahoma', 'Loma', 'Leelawadee', 'Ayuthaya', 'Thai Sans Neue', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. ตั้งค่าหน้าจอ UI ของ Streamlit
# ==========================================
st.set_page_config(page_title="SET50 Shareholder Network", layout="wide")
st.title("📊 SET50 Shareholder Network Analysis")
st.write("วิเคราะห์โครงสร้างเครือข่ายความสัมพันธ์ผู้ถือหุ้นรายใหญ่ 5 อันดับแรกของดัชนี SET50")

# ฟังก์ชันโหลดข้อมูลจากไฟล์ CSV แบบ Relative Path และทำความสะอาดตัวอักษร
@st.cache_data
def load_csv_data():
    try:
        # 💡 แก้ไขข้อที่ 1: ดึงไฟล์แบบ Relative Path โดยอ้างอิงจากที่อยู่ของไฟล์สคริปต์นี้
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "set50_top5_shareholders.csv")
        
        df = pd.read_csv(csv_path)
        # ทำความสะอาดช่องว่างวรรคตอนของชื่อเพื่อความแม่นยำในการนับสถิติ
        df['symbol'] = df['symbol'].astype(str).str.strip()
        df['shareholder_name'] = df['shareholder_name'].astype(str).apply(lambda x: " ".join(x.split()))
        return df
    except Exception as e:
        st.error(f"ไม่สามารถโหลดไฟล์ CSV ได้: {e}")
        return pd.DataFrame()

df = load_csv_data()

if not df.empty:
    # ==========================================
    # 2. แถบเครื่องมือด้านซ้าย (Sidebar Filters)
    # ==========================================
    st.sidebar.header("🎯 ตัวกรองเปิด/ปิด โหนดผู้ถือหุ้น")
    show_multi_holders = st.sidebar.checkbox("🟠 แสดงผู้ถือหุ้นที่ถือ ≥ 2 บริษัท", value=True)
    show_single_holders = st.sidebar.checkbox("🟢 แสดงผู้ถือหุ้นที่ถือแค่ 1 บริษัท", value=True)

    with st.expander("🔍 ดูตารางข้อมูลดิบจากไฟล์ CSV ทั้งหมด"):
        st.dataframe(df, use_container_width=True)

    # ==========================================
    # 3. ประมวลผลและคำนวณจำนวนบริษัทที่ถือหุ้นจริง
    # ==========================================
    # นับจำนวนครั้งที่ชื่อผู้ถือหุ้นปรากฏตัวในตารางจริง ๆ
    shareholder_counts = df['shareholder_name'].value_counts().to_dict()
    companies = df['symbol'].unique()

    # คัดแยกกลุ่มผู้ถือหุ้นตามสถิติจริง (ไม่รวมชื่อย่อบริษัท)
    # กลุ่มสีส้ม: ถือหุ้นตั้งแต่ 2 บริษัทขึ้นไป (Count >= 2)
    # กลุ่มสีเขียว: ถือหุ้นแค่บริษัทเดียวเท่านั้น (Count == 1)
    multi_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count >= 2]
    single_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count == 1]

    # ทำ DataFrame สรุปผู้ถือหุ้นรายใหญ่แสดงผลบนตารางฝั่งซ้าย
    df_analysis = pd.DataFrame([
        {"รายชื่อผู้ถือหุ้น": name, "จำนวนบริษัทที่ติด Top 5 จริง": shareholder_counts[name]} 
        for name in multi_holders_list
    ])

    # ==========================================
    # 💡 แก้ไขข้อที่ 2: เพิ่มสรุปจำนวนเส้นเชื่อมของผู้ถือหุ้นทั้งหมด (Metrics Dashboard)
    # ==========================================
    st.subheader("📈 สรุปภาพรวมเส้นเชื่อมโยงในเครือข่ายทุน (Shareholder Connectivity Metrics)")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="🏢 จำนวนบริษัทจดทะเบียน (SET50)", value=f"{len(companies)} บริษัท")
    with m_col2:
        st.metric(label="👥 จำนวนผู้ถือหุ้นรวมทั้งหมด (Unique)", value=f"{len(shareholder_counts)} ราย")
    with m_col3:
        st.metric(label="🟠 ผู้ถือหุ้นรายใหญ่ (ถือครอง ≥ 2 บริษัท)", value=f"{len(multi_holders_list)} ราย")
    with m_col4:
        st.metric(label="🟢 ผู้ถือหุ้นทั่วไป (ถือครองแค่ 1 บริษัท)", value=f"{len(single_holders_list)} ราย")

    st.markdown("---")

    # แบ่งหน้าจอแสดงผลข้อมูลเชิงสถิติและสถานะตัวกรอง
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🎯 สรุปผู้ถือหุ้นที่ติด Top 5 กับบริษัท ≥ 2 แห่ง")
        if not df_analysis.empty:
            st.dataframe(df_analysis.sort_values(by="จำนวนบริษัทที่ติด Top 5 จริง", ascending=False), hide_index=True)
        else:
            st.info("ไม่พบผู้ถือหุ้นรายใดที่ลงทุนควบตั้งแต่ 2 บริษัทขึ้นไป")
            
    with col2:
        st.subheader("💡 สถานะตัวกรองสีบนกราฟเครือข่าย")
        st.markdown(f"""
        * 🔵 **โหนดสีน้ำเงิน**: แทนตัวบริษัทจดทะเบียนหลักในดัชนี SET50 (เปิดไว้เสมอ)
        * 🟠 **โหนดสีส้ม**: แทนผู้ถือหุ้นที่ติดอันดับ Top 5 **$\ge$ 2 บริษัท** -> สถานะ: {"🟢 เปิดอยู่" if show_multi_holders else "🔴 ปิดอยู่"}
        * 🟢 **โหนดสีเขียว**: แทนผู้ถือหุ้นที่ติดอันดับ Top 5 **เพียง 1 บริษัท** -> สถานะ: {"🟢 เปิดอยู่" if show_single_holders else "🔴 ปิดอยู่"} *(💡 เปลี่ยนสีใหม่เพื่อการมองเห็นที่ชัดเจนขึ้น)*
        """)

    # ==========================================
    # 4. การคัดกรองซับกราฟ (Sub-graph Filtering) และแสดงผลกราฟ
    # ==========================================
    st.subheader("🕸️ แผนภูมิเครือข่ายความสัมพันธ์ (Network Graph Visualization)")
    
    # คำนวณรายชื่อ Node ที่จะยอมให้ผ่านเข้าไปวาดบนกราฟตามเงื่อนไข Checkbox ด้านซ้าย
    nodes_to_include = list(companies)  # ล็อกโหนดบริษัทไว้เสมอ
    if show_multi_holders:
        nodes_to_include.extend(multi_holders_list)
    if show_single_holders:
        nodes_to_include.extend(single_holders_list)

    # สร้างกราฟความสัมพันธ์แกนหลักจากตาราง CSV
    G_base = nx.Graph()
    for _, row in df.iterrows():
        G_base.add_edge(row['symbol'], row['shareholder_name'])
        
    # ตัดแปลงกราฟให้เหลือเฉพาะกลุ่ม Node ที่เลือกแสดงผล (Sub-graph)
    G = G_base.subgraph(nodes_to_include).copy()

    # ล้างหน่วยความจำรูปภาพเก่าของ Matplotlib ป้องกันระบบค้าง
    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # จัดวางตำแหน่งโหนดด้วยอัลกอริทึมแรงผลักสปริง (Spring Layout)
    pos = nx.spring_layout(G, k=0.55, seed=42)
    
    # 💡 แก้ไขข้อที่ 3: ปรับเปลี่ยนการเช็คเงื่อนไขสีของโหนดจากสีเทาเป็นสีเขียว
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node in companies:
            node_colors.append('#1f77b4')  # 🔵 บริษัท (สีน้ำเงิน)
            node_sizes.append(1400)
        elif shareholder_counts.get(node, 0) >= 2:
            node_colors.append('#ff7f0e')  # 🟠 ผู้ถือหุ้นควบ >= 2 บริษัท (สีส้ม)
            node_sizes.append(1100)
        else:
            node_colors.append('#2ca02c')  # 🟢 ผู้ถือหุ้นทั่วไปที่ถือ 1 บริษัท (เปลี่ยนเป็นสีเขียวพาสเทล/ชัดเจนขึ้น)
            node_sizes.append(400)
            
    if len(G.nodes()) > 0:
        # วาดโหนด เส้นเชื่อม และป้ายชื่อภาษไทยลงแกนภาพแบบเด็ดขาด
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='lightgray', alpha=0.6, width=1.2, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_family='Tahoma', font_weight='bold', ax=ax)
    else:
        st.warning("ไม่มีข้อมูลโหนดแสดงผลบนระบบแผนภูมิเนื่องจากปิดตัวกรองทั้งหมด")
    
    ax.axis('off')  # ปิดแกนกริด x, y ของรูปภาพ
    st.pyplot(fig)
else:
    st.error("ไม่สามารถแสดงผลระบบวิเคราะห์ข้อมูลได้เนื่องจากไม่มีข้อมูลในไฟล์ CSV")