import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# ลบการตั้งค่าฟอนต์ภาษาไทยทั้งหมดออกเพื่อใช้ภาษาอังกฤษบริสุทธิ์บนกราฟ
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. ตั้งค่าหน้าจอ UI ของ Streamlit
# ==========================================
st.set_page_config(page_title="SET50 Shareholder Network", layout="wide")
st.title("📊 SET50 Shareholder Network Analysis (100% English Graph Fixed)")
st.write("วิเคราะห์โครงสร้างเครือข่ายผู้ถือหุ้นรายใหญ่ 5 อันดับแรกของ SET50 (แก้ไขปัญหาตัวอักษรสี่เหลี่ยมบน Server สำเร็จ)")

# ฟังก์ชันสำหรับแปลชื่อผู้ถือหุ้นกลุ่มสีส้มทั้งหมดให้เป็นอังกฤษ และจัดการกลุ่มสีเขียวไม่ให้เป็นสี่เหลี่ยม
def translate_to_english(name, index_num):
    # Dictionary แปลชื่อกลุ่มส้ม (>= 2 บริษัท) ครบทุกชื่อในไฟล์ CSV ของคุณ
    translation_map = {
        "บริษัท ไทยเอ็นวีดีอาร์ จำกัด": "Thai NVDR Co., Ltd.",
        "กองทุนรวม วายุภักษ์หนึ่ง": "Vayupak Fund 1",
        "สำนักงานประกันสังคม": "Social Security Office",
        "SOUTH EAST ASIA UK (TYPE C) NOMINEES LIMITED": "SOUTH EAST ASIA UK (TYPE C) NOMINEES LTD",
        "UBS AG SINGAPORE BRANCH - FOR CLIENTS' ACCOUNTS": "UBS AG SINGAPORE BRANCH",
        "STATE STREET EUROPE LIMITED": "STATE STREET EUROPE LTD",
        "นาย นิติ โอสถานุเคราะห์": "Mr. Niti Osathanugrah",
        "บริษัท ปตท. จำกัด (มหาชน)": "PTT Public Co., Ltd.",
        "บริษัท สยาม แมนเนจเม้นท์ โฮลดิ้ง จำกัด": "Siam Management Holding Co., Ltd.",
        "ธนาคาร กรุงเทพ จำกัด (มหาชน)": "Bangkok Bank PCL",
        "กระทรวงการคลัง": "Ministry of Finance",
        "THE BANK OF NEW YORK MELLON": "THE BANK OF NEW YORK MELLON",
        "บริษัท เครือเจริญโภคภัณฑ์ จำกัด": "Charoen Pokphand Group Co., Ltd.",
        "บริษัท กัลฟ์ ดีเวลลอปเมนท์ จำกัด (มหาชน)": "Gulf Energy Development PCL",
        "ธนาคาร กรุงไทย จำกัด (มหาชน)": "Krungthai Bank PCL",
        "พระบาทสมเด็จพระวชิรเกล้าเจ้าอยู่หัว": "King Rama X",
        "บริษัท ทุนธนชาต จำกัด (มหาชน)": "Thanachart Capital PCL",
        "ชุมนุมสหกรณ์ออมทรัพย์ แห่งประเทศไทย จำกัด": "FSCT",
        "การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย": "EGAT",
        "นาย ประทีป ตั้งมติธรรม": "Mr. Prateep Tangmatitham",
        "STATE STREET BANK AND TRUST COMPANY": "STATE STREET BANK & TRUST"
    }
    
    # 1. ถ้าเป็นกลุ่มผู้ถือหุ้นใหญ่ (สีส้ม) ให้ดึงชื่อภาษาอังกฤษไปใช้ทันที
    if name in translation_map:
        return translation_map[name]
        
    # 2. ถ้าเป็นภาษาอังกฤษอยู่แล้ว (เช่น ชื่อกองทุนต่างประเทศ) ให้ใช้ชื่อเดิมได้เลย ไม่เป็นสี่เหลี่ยมแน่นอน
    if all(ord(char) < 128 for char in name):
        return name
        
    # 3. ถ้าเป็นกลุ่มผู้ถือหุ้นทั่วไป (สีเขียว ถือ 1 บริษัท) และเป็นชื่อภาษาไทย 
    # ระบบจะแปลงเป็นรหัสสากลเพื่อไม่ให้กราฟพังเป็นสี่เหลี่ยม แต่บนตารางจะยังเห็นเป็นชื่อไทยปกติ
    return f"Shareholder_{index_num}"

# ฟังก์ชันโหลดข้อมูลจากไฟล์ CSV แบบ Relative Path
@st.cache_data
def load_csv_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "set50_top5_shareholders.csv")
        
        df = pd.read_csv(csv_path)
        df['symbol'] = df['symbol'].astype(str).str.strip()
        df['shareholder_name'] = df['shareholder_name'].astype(str).apply(lambda x: " ".join(x.split()))
        
        # สร้างรายชื่อภาษาอังกฤษโดยส่งเลข Index เข้าไปกำกับกรณีต้องแปลงชื่อกลุ่มสีเขียว
        df['shareholder_en'] = [translate_to_english(row['shareholder_name'], idx) for idx, row in df.iterrows()]
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

    with st.expander("🔍 ดูตารางข้อมูลดิบภาษาไทยจากไฟล์ CSV ทั้งหมด"):
        st.dataframe(df[['symbol', 'shareholder_rank', 'shareholder_name']], use_container_width=True)

    # ==========================================
    # 3. ประมวลผลทางสถิติ (ขจัดปัญหาโหนดเบิ้ลด้วยชื่ออังกฤษสากล)
    # ==========================================
    shareholder_counts = df['shareholder_en'].value_counts().to_dict()
    companies = df['symbol'].unique()

    # จัดกลุ่มรายชื่อเพื่อใช้ทำฟิลเตอร์เปิด/ปิด
    multi_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count >= 2]
    single_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count == 1]

    # สร้างตารางข้อมูลจับคู่ชื่อไทย-อังกฤษ เพื่อให้ตารางฝั่งซ้ายแสดงผลควบคู่กันอย่างสวยงาม
    mapping_df = df[['shareholder_name', 'shareholder_en']].drop_duplicates().set_index('shareholder_en')

    df_analysis = pd.DataFrame([
        {
            "รายชื่อผู้ถือหุ้น (ไทย)": mapping_df.loc[name, 'shareholder_name'] if name in mapping_df.index else name,
            "Shareholder Name (EN)": name, 
            "จำนวนบริษัทที่ติด Top 5 จริง": shareholder_counts[name]
        } 
        for name in multi_holders_list
    ])

    # สรุปภาพรวมจำนวนเส้นเชื่อมโยงในเครือข่ายทุน (Metrics Dashboard)
    st.subheader("📈 สรุปภาพรวมเส้นเชื่อมโยงในเครือข่ายทุน (Shareholder Connectivity Metrics)")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="🏢 จำนวนบริษัทจดทะเบียน (SET50)", value=f"{len(companies)} Companies")
    with m_col2:
        st.metric(label="👥 จำนวนผู้ถือหุ้นรวมทั้งหมด (Unique)", value=f"{len(shareholder_counts)} Users")
    with m_col3:
        st.metric(label="🟠 ผู้ถือหุ้นรายใหญ่ (ถือครอง ≥ 2 บริษัท)", value=f"{len(multi_holders_list)} Users")
    with m_col4:
        st.metric(label="🟢 ผู้ถือหุ้นทั่วไป (ถือครองแค่ 1 บริษัท)", value=f"{len(single_holders_list)} Users")

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
        * 🔵 **Blue Node**: แทนตัวบริษัทหลักในดัชนี SET50 (เช่น ADVANC, AOT, WHA)
        * 🟠 **Orange Node**: แทนผู้ถือหุ้นรายใหญ่ที่ติด Top 5 **$\ge$ 2 บริษัท** (เปลี่ยนเป็นภาษาอังกฤษสากลแล้ว)
        * 🟢 **Green Node**: แทนผู้ถือหุ้นทั่วไปที่ติดอันดับ Top 5 **เพียง 1 บริษัท** (แปลงเป็นรหัสสากลเพื่อป้องกันสี่เหลี่ยม)
        """)

    # ==========================================
    # 4. การคัดกรองซับกราฟ (Sub-graph Filtering) และแสดงผลกราฟ
    # ==========================================
    st.subheader("🕸️ แผนภูมิเครือข่ายความสัมพันธ์ (Network Graph Visualization)")
    
    nodes_to_include = list(companies)
    if show_multi_holders:
        nodes_to_include.extend(multi_holders_list)
    if show_single_holders:
        nodes_to_include.extend(single_holders_list)

    # สร้างโครงข่ายกราฟโดยใช้ชื่อภาษาอังกฤษสากลทั้งหมด
    G_base = nx.Graph()
    for _, row in df.iterrows():
        G_base.add_edge(row['symbol'], row['shareholder_en'])
        
    G = G_base.subgraph(nodes_to_include).copy()

    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # คำนวณพิกัด Layout กราฟแบบแรงผลักสปริง
    pos = nx.spring_layout(G, k=0.55, seed=42)
    
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node in companies:
            node_colors.append('#1f77b4')  # 🔵 บริษัท (น้ำเงิน)
            node_sizes.append(1400)
        elif shareholder_counts.get(node, 0) >= 2:
            node_colors.append('#ff7f0e')  # 🟠 ผู้ถือหุ้นควบ >= 2 บริษัท (ส้ม)
            node_sizes.append(1100)
        else:
            node_colors.append('#2ca02c')  # 🟢 ผู้ถือหุ้นทั่วไปที่ถือ 1 บริษัท (เขียว)
            node_sizes.append(400)
            
    if len(G.nodes()) > 0:
        # วาดองค์ประกอบทั้งหมดโดยใช้ฟอนต์สากล sans-serif ปราศจากกล่องสี่เหลี่ยม 100%
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='lightgray', alpha=0.6, width=1.2, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=9, font_family='sans-serif', font_weight='bold', ax=ax)
    else:
        st.warning("ไม่มีข้อมูลโหนดแสดงผลบนระบบแผนภูมิเนื่องจากปิดตัวกรองทั้งหมด")
    
    ax.axis('off')
    st.pyplot(fig)
else:
    st.error("ไม่สามารถแสดงผลระบบวิเคราะห์ข้อมูลได้เนื่องจากไม่มีข้อมูลในไฟล์ CSV")
