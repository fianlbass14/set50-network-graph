import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# ลบการตั้งค่าฟอนต์ภาษาไทยออก เนื่องจากเราจะใช้ภาษาอังกฤษทั้งหมดในการวาดกราฟเพื่อป้องกันกล่องสี่เหลี่ยม (TOFU)
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. ตั้งค่าหน้าจอ UI ของ Streamlit
# ==========================================
st.set_page_config(page_title="SET50 Shareholder Network", layout="wide")
st.title("📊 SET50 Shareholder Network Analysis (CSV Mode)")
st.write("วิเคราะห์โครงสร้างเครือข่ายความสัมพันธ์ผู้ถือหุ้นรายใหญ่ 5 อันดับแรกของดัชนี SET50 (เวอร์ชันรองรับการแสดงผลบน Server)")

# ฟังก์ชันสำหรับแปลงชื่อผู้ถือหุ้นไทยรายใหญ่ให้เป็นภาษาอังกฤษเพื่อการวาดกราฟที่สมบูรณ์
def translate_to_english(name):
    # Dictionary สำหรับจับคู่ชื่อไทย -> อังกฤษ สำหรับรายชื่อที่ปรากฏบ่อย ๆ 
    translation_map = {
        "บริษัท ไทยเอ็นวีดีอาร์ จำกัด": "Thai NVDR Co., Ltd.",
        "กองทุนรวม วายุภักษ์หนึ่ง": "Vayupak Fund 1",
        "สำนักงานประกันสังคม": "Social Security Office",
        "บริษัท ปตท. จำกัด (มหาชน)": "PTT Public Co., Ltd.",
        "บริษัท สยาม แมนเนจเม้นท์ โฮลดิ้ง จำกัด": "Siam Management Holding Co., Ltd.",
        "ธนาคาร กรุงเทพ จำกัด (มหาชน)": "Bangkok Bank PCL",
        "กระทรวงการคลัง": "Ministry of Finance",
        "บริษัท ซีพี ออลล์ จำกัด (มหาชน)": "CP ALL PCL",
        "บริษัท กัลฟ์ ดีเวลลอปเมนท์ จำกัด (มหาชน)": "Gulf Energy Development PCL",
        "บริษัท ทีซีซี บริหารธุรกิจ จำกัด": "TCC Business Administration Co., Ltd.",
        "บริษัท ทีซีซี รีเทล จำกัด": "TCC Retail Co., Ltd.",
        "บริษัท น้ำตาลมิตรผล จำกัด": "Mitr Phol Sugar Co., Ltd.",
        "นาย นิติ โอสถานุเคราะห์": "Mr. Niti Osathanugrah",
        "บริษัท ทุนธนชาต จำกัด (มหาชน)": "Thanachart Capital PCL",
        "บริษัท วี.ซี.สมบัติ จำกัด": "V.C. Sombat Co., Ltd.",
        "บริษัท เอสซีบี เอกซ์ จำกัด (มหาชน)": "SCBX PCL"
    }
    
    # ถ้าเจอชื่อใน Map ให้เปลี่ยนเป็นอังกฤษ ท้าไม่เจอให้ตัดคำว่า (มหาชน) หรือ จำกัด ออกชั่วคราวเพื่อให้อ่านง่ายขึ้นบนกราฟ
    if name in translation_map:
        return translation_map[name]
    
    # สำหรับรายชื่ออื่น ๆ ถ้ายังมีภาษาไทยอยู่ ระบบจะแสดงผลบนตารางได้ปกติ แต่บนกราฟอาจเป็นสี่เหลี่ยม
    # แนะนำให้ใช้ Dictionary ด้านบนเติมรายชื่อเพิ่มเติมได้ตามต้องการครับ
    return name

# ฟังก์ชันโหลดข้อมูลจากไฟล์ CSV แบบ Relative Path และแปลภาษา
@st.cache_data
def load_csv_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "set50_top5_shareholders.csv")
        
        df = pd.read_csv(csv_path)
        df['symbol'] = df['symbol'].astype(str).str.strip()
        # ล้างช่องว่าง
        df['shareholder_name'] = df['shareholder_name'].astype(str).apply(lambda x: " ".join(x.split()))
        
        # 💡 แก้ไข: เพิ่มคอลัมน์ชื่อภาษาอังกฤษสำหรับใช้วาดบนกราฟโดยเฉพาะ
        df['shareholder_en'] = df['shareholder_name'].apply(translate_to_english)
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
    # 3. ประมวลผลโดยใช้ชื่อภาษาอังกฤษ (EN Node Process)
    # ==========================================
    # นับสถิติจากชื่อภาษาอังกฤษเพื่อไม่ให้กราฟแตก
    shareholder_counts = df['shareholder_en'].value_counts().to_dict()
    companies = df['symbol'].unique()

    multi_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count >= 2]
    single_holders_list = [node for node, count in shareholder_counts.items() if node not in companies and count == 1]

    # ทำ DataFrame สรุปผู้ถือหุ้นรายใหญ่แสดงผลบนตารางฝั่งซ้าย
    df_analysis = pd.DataFrame([
        {"Shareholder Name (EN)": name, "No. of Companies (Top 5)": shareholder_counts[name]} 
        for name in multi_holders_list
    ])

    # สรุปภาพรวมจำนวนเส้นเชื่อมโยงในเครือข่ายทุน
    st.subheader("📈 สรุปภาพรวมเส้นเชื่อมโยงในเครือข่ายทุน (Shareholder Connectivity Metrics)")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="🏢 จำนวนบริษัท (SET50)", value=f"{len(companies)} Companies")
    with m_col2:
        st.metric(label="👥 ผู้ถือหุ้นรวมทั้งหมด (Unique)", value=f"{len(shareholder_counts)} Users")
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
            st.dataframe(df_analysis.sort_values(by="No. of Companies (Top 5)", ascending=False), hide_index=True)
        else:
            st.info("ไม่พบผู้ถือหุ้นรายใดที่ลงทุนควบตั้งแต่ 2 บริษัทขึ้นไป")
            
    with col2:
        st.subheader("💡 สถานะตัวกรองสีบนกราฟเครือข่าย")
        st.markdown(f"""
        * 🔵 **Blue Node**: ตัวบริษัทหลักในดัชนี SET50 (เช่น ADVANC, AOT)
        * 🟠 **Orange Node**: ผู้ถือหุ้นรายใหญ่ที่ถือควบ **$\ge$ 2 บริษัท** (เช่น Thai NVDR, Social Security Office)
        * 🟢 **Green Node**: ผู้ถือหุ้นทั่วไปที่ถือครอง **เพียง 1 บริษัท**
        """)

    # ==========================================
    # 4. การคัดกรองซับกราฟ และวาดกราฟภาษาอังกฤษ
    # ==========================================
    st.subheader("🕸️ แผนภูมิเครือข่ายความสัมพันธ์ (Network Graph Visualization)")
    
    nodes_to_include = list(companies)
    if show_multi_holders:
        nodes_to_include.extend(multi_holders_list)
    if show_single_holders:
        nodes_to_include.extend(single_holders_list)

    # ใช้ตารางภาษาอังกฤษในการสร้าง Edge
    G_base = nx.Graph()
    for _, row in df.iterrows():
        G_base.add_edge(row['symbol'], row['shareholder_en'])
        
    G = G_base.subgraph(nodes_to_include).copy()

    plt.clf()
    fig, ax = plt.subplots(figsize=(16, 12))
    
    pos = nx.spring_layout(G, k=0.55, seed=42)
    
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node in companies:
            node_colors.append('#1f77b4')  # 🔵 สีน้ำเงิน
            node_sizes.append(1400)
        elif shareholder_counts.get(node, 0) >= 2:
            node_colors.append('#ff7f0e')  # 🟠 สีส้ม
            node_sizes.append(1100)
        else:
            node_colors.append('#2ca02c')  # 🟢 สีเขียว
            node_sizes.append(400)
            
    if len(G.nodes()) > 0:
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='lightgray', alpha=0.6, width=1.2, ax=ax)
        # ปรับมาใช้ฟอนต์มาตรฐานสากล 'sans-serif' ซึ่งรองรับภาษาอังกฤษได้คมชัดบนทุกเซิร์ฟเวอร์แน่นอน
        nx.draw_networkx_labels(G, pos, font_size=9, font_family='sans-serif', font_weight='bold', ax=ax)
    else:
        st.warning("ไม่มีข้อมูลโหนดแสดงผลบนระบบแผนภูมิเนื่องจากปิดตัวกรองทั้งหมด")
    
    ax.axis('off')
    st.pyplot(fig)
else:
    st.error("ไม่สามารถแสดงผลระบบวิเคราะห์ข้อมูลได้เนื่องจากไม่มีข้อมูลในไฟล์ CSV")
