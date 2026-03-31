import streamlit as st
import pandas as pd

st.set_page_config(page_title="專業旅遊分帳", layout="wide")

st.title("💰 專業旅遊分帳 App (2-5人)")

# --- 1. 設定成員 ---
with st.sidebar:
    st.header("⚙️ 設定")
    num_people = st.slider("旅行人數", 2, 5, 3)
    member_names = []
    for i in range(num_people):
        name = st.text_input(f"成員 {i+1} 姓名", f"成員 {i+1}", key=f"name_{i}")
        member_names.append(name)

# 初始化 session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# --- 2. 新增支出記錄 ---
st.subheader("➕ 新增支出")
with st.container(border=True):
    col1, col2, col3 = st.columns([1, 1, 2])
    payer = col1.selectbox("誰付的錢？", member_names)
    amount = col2.number_input("支付金額", min_value=0.0, step=1.0, format="%.2f")
    item = col3.text_input("項目 (如：飯店、包車)")

    split_mode = st.radio("分帳方式", ["所有人平分", "自定義比例/金額"])
    
    weights = {}
    if split_mode == "自定義比例/金額":
        st.write("請輸入各人負擔的「權重」（例如 1:1:2）或直接輸入金額：")
        cols = st.columns(num_people)
        for i, name in enumerate(member_names):
            weights[name] = cols[i].number_input(f"{name}", min_value=0.0, value=1.0, key=f"w_{name}")
    else:
        for name in member_names:
            weights[name] = 1.0  # 平分等於每人權重都是 1

    if st.button("確認新增", type="primary"):
        if amount > 0:
            # 計算每人應負擔比例
            total_weight = sum(weights.values())
            individual_shares = {name: (w / total_weight) * amount for name, w in weights.items()}
            
            st.session_state.expenses.append({
                "payer": payer,
                "amount": amount,
                "item": item,
                "shares": individual_shares
            })
            st.success("已成功紀錄！")
            st.rerun()

# --- 3. 顯示與結算 ---
if st.session_state.expenses:
    st.divider()
    
    # 顯示表格
    df_display = pd.DataFrame([
        {"項目": e['item'], "付款人": e['payer'], "總額": e['amount']} 
        for e in st.session_state.expenses
    ])
    st.subheader("📋 支出明細")
    st.table(df_display)

    # 計算結餘
    # 淨餘額 = (身為付款人支付的總額) - (身為參與者應負擔的總額)
    balances = {name: 0.0 for name in member_names}
    for exp in st.session_state.expenses:
        # 付款人增加資產
        balances[exp['payer']] += exp['amount']
        # 參與者增加負債
        for name, share in exp['shares'].items():
            balances[name] -= share

    st.subheader("🏁 結算方案")
    
    # 債務抵消演算法
    debtors = sorted([(n, b) for n, b in balances.items() if b < -0.01], key=lambda x: x[1])
    creditors = sorted([(n, b) for n, b in balances.items() if b > 0.01], key=lambda x: x[1], reverse=True)

    if not debtors and not creditors:
        st.info("目前帳目平衡，無須轉帳。")
    else:
        results = []
