#streamlit run BasketBallData.py
import streamlit as st
import pandas as pd
import os
from datetime import date
import hashlib
import plotly.express as px
from PIL import Image
import base64

# --- 1. 基础配置与文件初始化 ---
# 设置页面标题和图标
st.set_page_config(page_title="武林风篮球技巧交流群球员信息", page_icon="🏀", layout="wide")

USER_DATA_PATH = "players_info.csv"
STATS_DATA_PATH = "players_stats.csv"
AVATAR_FOLDER = "avatars"

# 创建头像文件夹
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

# 初始化数据存储文件
if not os.path.exists(USER_DATA_PATH):
    pd.DataFrame(columns=["姓名", "密码", "身高", "体重", "位置"]).to_csv(USER_DATA_PATH, index=False)
if not os.path.exists(STATS_DATA_PATH):
    pd.DataFrame(columns=["姓名", "日期", "进球", "篮板", "抢断", "盖帽"]).to_csv(STATS_DATA_PATH, index=False)

# 密码加密处理
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# 获取用户头像路径
def get_avatar_path(username):
    """获取用户头像路径，如果不存在则返回None"""
    for ext in ['png', 'jpg', 'jpeg']:
        avatar_path = f"{AVATAR_FOLDER}/{username}.{ext}"
        if os.path.exists(avatar_path):
            return avatar_path
    return None

# 显示头像
def display_avatar(username, width=150):
    """显示用户头像，如果没有则显示默认头像"""
    avatar_path = get_avatar_path(username)
    if avatar_path:
        image = Image.open(avatar_path)
        st.image(image, width=width, caption=f"{username}")
    else:
        # 显示默认头像（使用emoji或占位图）
        st.markdown(f"""
        <div style="width:{width}px; height:{width}px; background-color:#f0f0f0; 
        border-radius:50%; display:flex; align-items:center; justify-content:center; 
        font-size:60px; margin:auto;">👤</div>
        <p style="text-align:center; margin-top:5px;">{username}</p>
        """, unsafe_allow_html=True)

# --- 2. 会话状态管理 (登录状态) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- 3. 侧边栏：身份验证 ---
st.sidebar.title("🔐 球员通道")
if not st.session_state['logged_in']:
    auth_mode = st.sidebar.radio("选择操作", ["登录系统", "注册新球员"])
    input_user = st.sidebar.text_input("姓名", placeholder="请输入真实姓名")
    input_pw = st.sidebar.text_input("密码", type='password')
    
    if auth_mode == "登录系统":
        if st.sidebar.button("立即登录", use_container_width=True):
            df_u = pd.read_csv(USER_DATA_PATH)
            user_record = df_u[df_u['姓名'] == input_user]
            if not user_record.empty and check_hashes(input_pw, user_record.iloc[0]['密码']):
                st.session_state['logged_in'] = True
                st.session_state['username'] = input_user
                st.rerun()
            else:
                st.sidebar.error("❌ 姓名或密码不匹配")
    else:
        if st.sidebar.button("完成注册", use_container_width=True):
            df_u = pd.read_csv(USER_DATA_PATH)
            if input_user in df_u['姓名'].values:
                st.sidebar.warning("⚠️ 该姓名已被注册")
            elif not input_user or not input_pw:
                st.sidebar.error("⚠️ 姓名和密码不能为空")
            else:
                new_row = pd.DataFrame([[input_user, make_hashes(input_pw), 180, 75, "SF"]], columns=df_u.columns)
                pd.concat([df_u, new_row], ignore_index=True).to_csv(USER_DATA_PATH, index=False)
                st.sidebar.success("✅ 注册成功！请切换到登录模式")
else:
    st.sidebar.info(f"当前在线: **{st.session_state['username']}**")
    
    # 在侧边栏显示当前用户的头像
    with st.sidebar:
        st.markdown("---")
        avatar_path = get_avatar_path(st.session_state['username'])
        if avatar_path:
            image = Image.open(avatar_path)
            st.image(image, width=100, caption="我的头像")
        else:
            st.markdown("""
            <div style="width:100px; height:100px; background-color:#f0f0f0; 
            border-radius:50%; display:flex; align-items:center; justify-content:center; 
            font-size:40px; margin:auto;">👤</div>
            """, unsafe_allow_html=True)
            st.caption("暂无头像")
    
    if st.sidebar.button("退出系统", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()

# --- 4. 主界面逻辑 ---
if not st.session_state['logged_in']:
    st.title("🏀 业余篮球联盟数据管理系统")
    st.markdown("""
    ### 欢迎来到联盟后台！
    在这里你可以：
    * **查看** 任何一位队友的身高、位置和历史战绩。
    * **录入** 你每场比赛的进球、篮板、抢断和盖帽。
    * **管理** 自己的体测数据和个人头像。
    
    **请先在左侧侧边栏完成登录。**
    """)
    st.image("https://images.unsplash.com/photo-1546519638-68e109498ffc?q=80&w=2090&auto=format&fit=crop", caption="无篮球，不兄弟")

else:
    # 顶部导航标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 联盟数据大屏", "✍️ 个人战绩录入", "⚙️ 我的资料设置", "👥 球员相册"])

    # --- TAB 1: 联盟大屏（公开查看） ---
    with tab1:
        st.subheader("联盟球员动态与查询")
        df_p = pd.read_csv(USER_DATA_PATH)
        df_s = pd.read_csv(STATS_DATA_PATH)
        
        # 1.1 全员概览（排行榜）
        with st.expander("🏆 查看联盟得分榜"):
            if not df_s.empty:
                leaderboard = df_s.groupby('姓名')[['进球', '篮板', '抢断', '盖帽']].sum().sort_values(by='进球', ascending=False)
                st.table(leaderboard)
            else:
                st.write("暂无比赛记录")

        st.divider()

        # 1.2 个人档案详细查询 (可查任何人)
        search_name = st.selectbox("🔍 选择要查询的球员", df_p['姓名'].tolist())
        
        # 创建两列布局，左边显示头像，右边显示信息
        col_avatar, col_info = st.columns([1, 3])
        
        with col_avatar:
            st.markdown("### 球员头像")
            display_avatar(search_name, width=150)
        
        with col_info:
            st.markdown("### 基本信息")
            p_info = df_p[df_p['姓名'] == search_name].iloc[0]
            p_stats = df_s[df_s['姓名'] == search_name]
            
            # 展示基本体测
            c1, c2, c3 = st.columns(3)
            c1.metric("身高 (cm)", p_info['身高'])
            c2.metric("体重 (kg)", p_info['体重'])
            c3.metric("擅长位置", p_info['位置'])

        # 展示统计数据
        st.write(f"### {search_name} 的生涯总计")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总进球", p_stats['进球'].sum())
        m2.metric("总篮板", p_stats['篮板'].sum())
        m3.metric("总抢断", p_stats['抢断'].sum())
        m4.metric("总盖帽", p_stats['盖帽'].sum())

        # 趋势图
        if not p_stats.empty:
            p_stats['日期'] = pd.to_datetime(p_stats['日期'])
            fig = px.line(p_stats.sort_values('日期'), x='日期', y='进球', title=f"{search_name} 进球趋势图")
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("#### 📅 详细战绩表")
            st.dataframe(p_stats.sort_values(by="日期", ascending=False), use_container_width=True)
            
            # --- 权限判断：只有本人能删除自己的数据 ---
            if search_name == st.session_state['username']:
                st.warning("您正在查看自己的记录，如有录入错误可在此删除：")
                del_date = st.date_input("选择记录日期", value=date.today(), key="del_date")
                if st.button("确认删除该日战绩"):
                    df_s = df_s[~((df_s['姓名'] == search_name) & (df_s['日期'] == str(del_date)))]
                    df_s.to_csv(STATS_DATA_PATH, index=False)
                    st.success("数据已删除！")
                    st.rerun()
        else:
            st.info(f"{search_name} 还没有录入任何比赛数据。")

    # --- TAB 2: 个人战绩录入（限本人） ---
    with tab2:
        st.subheader("📝 录入新比赛战绩")
        st.info(f"当前身份：**{st.session_state['username']}** (您的数据将存入个人档案)")
        
        with st.form("stat_form"):
            entry_date = st.date_input("比赛日期", date.today())
            col_a, col_b = st.columns(2)
            g = col_a.number_input("进球 (Goals)", min_value=0, step=1)
            r = col_b.number_input("篮板 (Rebounds)", min_value=0, step=1)
            s = col_a.number_input("抢断 (Steals)", min_value=0, step=1)
            b = col_b.number_input("盖帽 (Blocks)", min_value=0, step=1)
            
            submit = st.form_submit_button("保存数据到云端", use_container_width=True)
            
            if submit:
                df_s = pd.read_csv(STATS_DATA_PATH)
                # 将 entry_date 转为字符串，确保存储格式统一
                str_date = entry_date.strftime('%Y-%m-%d') 
                new_entry = pd.DataFrame(
                    [[st.session_state['username'], str_date, g, r, s, b]], 
                    columns=["姓名", "日期", "进球", "篮板", "抢断", "盖帽"]
                )
                pd.concat([df_s, new_entry], ignore_index=True).to_csv(STATS_DATA_PATH, index=False)
                st.success("🎉 数据录入成功！")

    # --- TAB 3: 个人资料设置（限本人） ---
    with tab3:
        st.subheader("⚙️ 个人体测资料修改")
        
        # 分两列显示：左边是头像，右边是资料
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.markdown("### 📸 我的头像")
            # 显示当前头像
            display_avatar(st.session_state['username'], width=200)
            
            # 头像上传
            st.markdown("---")
            uploaded_avatar = st.file_uploader("更换头像", type=["jpg", "png", "jpeg"], key="avatar_uploader")
            if uploaded_avatar:
                # 删除旧头像
                old_avatar = get_avatar_path(st.session_state['username'])
                if old_avatar and os.path.exists(old_avatar):
                    os.remove(old_avatar)
                
                # 保存新头像
                file_extension = uploaded_avatar.name.split('.')[-1]
                avatar_path = f"{AVATAR_FOLDER}/{st.session_state['username']}.{file_extension}"
                with open(avatar_path, "wb") as f:
                    f.write(uploaded_avatar.getbuffer())
                st.success("✅ 头像更新成功！")
                st.rerun()
        
        with col_right:
            st.markdown("### 📋 基本资料")
            df_p = pd.read_csv(USER_DATA_PATH)
            idx = df_p[df_p['姓名'] == st.session_state['username']].index[0]
            
            with st.form("profile_form"):
                new_h = st.number_input("更新身高 (cm)", 140, 230, int(df_p.at[idx, '身高']))
                new_w = st.number_input("更新体重 (kg)", 40, 150, int(df_p.at[idx, '体重']))
                new_p = st.selectbox("球场位置", ["PG", "SG", "SF", "PF", "C"], 
                                     index=["PG", "SG", "SF", "PF", "C"].index(df_p.at[idx, '位置']))
                
                save_profile = st.form_submit_button("保存修改", use_container_width=True)
                if save_profile:
                    df_p.at[idx, '身高'] = new_h
                    df_p.at[idx, '体重'] = new_w
                    df_p.at[idx, '位置'] = new_p
                    df_p.to_csv(USER_DATA_PATH, index=False)
                    st.success("✅ 个人资料已同步更新！")

        # --- 新增下载备份部分 ---
        st.divider()
        st.subheader("💾 数据备份 (防止云端丢失)")
        st.caption("定期下载此文件。若云端数据意外重置，可将此文件上传至 GitHub 覆盖旧文件。")
        
        cd1, cd2 = st.columns(2)
        # 使用 utf_8_sig 确保下载的 CSV 在 Excel 中打开不乱码
        cd1.download_button(
            "📥 下载球员名单",
            pd.read_csv(USER_DATA_PATH).to_csv(index=False).encode('utf_8_sig'),
            f"players_info_{date.today()}.csv", "text/csv", use_container_width=True
        )
        cd2.download_button(
            "📥 下载全部战绩",
            pd.read_csv(STATS_DATA_PATH).to_csv(index=False).encode('utf_8_sig'),
            f"all_stats_{date.today()}.csv", "text/csv", use_container_width=True
        )
        
        # --- 管理员专用功能 ---
        if st.session_state['username'] == "赵阳":  
            st.divider()
            with st.expander("🛠️ 系统管理（仅管理员可见）"):
                st.warning("此区域功能具有破坏性，请谨慎操作")
                
                if st.button("🔴 重置/清空所有球员战绩"):
                    empty_stats = pd.DataFrame(columns=["姓名", "日期", "进球", "篮板", "抢断", "盖帽"])
                    empty_stats.to_csv(STATS_DATA_PATH, index=False)
                    st.success("战绩已清空！请刷新页面。")
                    
                if st.button("📋 查看所有注册用户信息"):
                    df_all_users = pd.read_csv(USER_DATA_PATH)
                    st.dataframe(df_all_users)

    # --- TAB 4: 球员相册（新增） ---
    with tab4:
        st.subheader("👥 联盟球员相册")
        st.markdown("查看所有球员的头像和基本信息")
        
        df_p = pd.read_csv(USER_DATA_PATH)
        
        # 每行显示4个球员
        cols_per_row = 4
        players = df_p['姓名'].tolist()
        
        for i in range(0, len(players), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(players):
                    player_name = players[i + j]
                    player_info = df_p[df_p['姓名'] == player_name].iloc[0]
                    
                    with col:
                        # 显示头像
                        display_avatar(player_name, width=120)
                        
                        # 显示基本信息
                        st.markdown(f"""
                        <div style="text-align: center; padding: 5px;">
                            <small>身高: {player_info['身高']}cm</small><br>
                            <small>体重: {player_info['体重']}kg</small><br>
                            <small>位置: {player_info['位置']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 添加分隔线
                        st.markdown("---")

# 底部说明
st.markdown("---")
st.caption("🏀 业余篮球联盟数据系统 v1.1 | 仅供队友内部交流使用")
