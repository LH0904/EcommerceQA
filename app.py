"""
电商智能问答系统 - Streamlit 前端
"""
import streamlit as st
import requests
import json
import os

st.set_page_config(
    page_title="电商智能问答系统",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { max-width: 1200px; margin: 0 auto; }
    .sql-box {
        background: #1e1e1e; color: #d4d4d4; padding: 12px 16px;
        border-radius: 8px; font-family: monospace; font-size: 14px;
        border-left: 4px solid #4CAF50;
    }
    .result-box {
        background: #f8f9fa; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid #2196F3;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 16px; border-radius: 12px; text-align: center;
    }
    div[data-testid="stMetric"] {
        background: #f0f2f6; padding: 12px; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛒 电商智能问答系统")
    st.markdown("---")
    st.markdown("**技术架构**")
    st.markdown("- 💬 自然语言 → SQL（向量检索）")
    st.markdown("- 🗄️ MySQL 数据查询")
    st.markdown("- 🤖 小米 MiMo 生成分析报告")
    st.markdown("- 📊 Echarts 数据看板")
    st.markdown("---")
    st.markdown("**数据规模**")
    st.markdown("- 用户行为：10 万条")
    st.markdown("- 商品信息：32 万条")
    st.markdown("- 用户评论：1.4 万条")
    st.markdown("- 商品类别：5,357 条")
    st.markdown("- 用户画像：1 万条")
    st.markdown("---")
    st.markdown("**示例问题**")
    examples = [
        "统计各行为类型的数量分布",
        "最受欢迎的前10个商品类别",
        "各城市的购买转化率",
        "各职业用户的平均消费金额",
        "每天的购买量趋势",
        "男女用户比例",
    ]
    for ex in examples:
        st.markdown(f"- `{ex}`")

# Header
st.title("🛒 电商智能问答系统")
st.markdown("基于 RAG + NL2SQL 的智能数据查询与可视化分析平台")
st.markdown("---")

# Input
col1, col2 = st.columns([4, 1])
with col1:
    user_input = st.text_input(
        "请输入您的问题",
        placeholder="例如：统计各行为类型的数量分布",
        label_visibility="collapsed"
    )
with col2:
    query_btn = st.button("🔍 查询", type="primary", use_container_width=True)

# Process query
if query_btn and user_input:
    with st.spinner("🔄 正在分析问题并生成查询..."):
        try:
            resp = requests.post(
                "http://localhost:35052/query",
                data={"user_question": user_input},
                timeout=300
            )
            result = resp.json()

            if "error" in result:
                st.error(f"❌ 查询失败：{result['error']}")
            else:
                # Display results
                st.markdown("### 📋 查询结果")

                # Metrics row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ 耗时", result.get("time", "N/A"))
                with col2:
                    st.metric("📊 返回行数", len(result.get("result", [])))
                with col3:
                    st.metric("💾 SQL 长度", f"{len(result.get('sql', ''))} 字符")

                # SQL
                st.markdown("**生成的 SQL：**")
                st.code(result.get("sql", ""), language="sql")

                # Data table
                data = result.get("result", [])
                if data:
                    st.markdown("**查询数据：**")
                    st.dataframe(data, use_container_width=True)

                # Dashboard
                board_html = result.get("board_html", "")
                if board_html:
                    st.markdown("### 📊 数据看板")
                    st.components.v1.html(board_html, height=800, scrolling=True)

                # Download buttons
                st.markdown("### ⬇️ 下载")
                col1, col2 = st.columns(2)
                with col1:
                    if result.get("pdf_path") and os.path.exists(result["pdf_path"]):
                        with open(result["pdf_path"], "rb") as f:
                            st.download_button(
                                "📄 下载 PDF 报告",
                                f.read(),
                                file_name="电商数据分析报告.pdf",
                                mime="application/pdf"
                            )
                with col2:
                    if result.get("html_path") and os.path.exists(result["html_path"]):
                        with open(result["html_path"], "r", encoding="utf-8") as f:
                            st.download_button(
                                "🌐 下载 HTML 看板",
                                f.read(),
                                file_name="电商数据看板.html",
                                mime="text/html"
                            )

        except requests.exceptions.Timeout:
            st.error("❌ 请求超时，请稍后重试")
        except Exception as e:
            st.error(f"❌ 请求失败：{e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#888; font-size:12px;'>"
    "电商智能问答系统 · 基于 RAG + NL2SQL · 计算机科学与技术专业综合实践"
    "</div>",
    unsafe_allow_html=True
)
