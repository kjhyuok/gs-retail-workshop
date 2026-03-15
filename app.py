"""GS Retail AI Agent Workshop — Streamlit UI"""
import streamlit as st
import time, uuid, json, os
from demo_mode import demo_response

# ── 페이지 설정 ──
st.set_page_config(
    page_title="GS Retail AI Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS (모던 다크 UI) ──
_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── 기본 ── */
.stApp { background-color: #0a0e17; font-family: 'Inter', -apple-system, sans-serif !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0c1120 0%, #0a0e17 100%); border-right: 1px solid rgba(255,255,255,0.06); }
section[data-testid="stSidebar"] .stMarkdown { color: #c4cede; }
header[data-testid="stHeader"] { background: #0a0e17; }

/* ── 채팅 메시지 — 컴팩트 & 글씨 축소 ── */
.stChatMessage { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 16px !important; padding: 12px 16px !important; }
.stChatMessage p, .stChatMessage li, .stChatMessage td, .stChatMessage th { font-size: 13px !important; line-height: 1.65 !important; color: #c4cede !important; }
.stChatMessage strong { color: #e8edf5 !important; }
.stChatMessage h1,.stChatMessage h2,.stChatMessage h3 { font-size: 14px !important; color: #e8edf5 !important; }
.stChatMessage blockquote { border-left: 2px solid rgba(99,102,241,0.4); background: rgba(99,102,241,0.06); border-radius: 0 8px 8px 0; padding: 6px 12px; margin: 8px 0; }
.stChatMessage blockquote p { font-size: 12px !important; color: #8b95a8 !important; }
.stChatMessage table { font-size: 12px !important; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; border: 1px solid rgba(255,255,255,0.06); }
.stChatMessage th { background: rgba(99,102,241,0.08) !important; color: #8b95a8 !important; font-size: 11px !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; padding: 8px 12px !important; border: none !important; }
.stChatMessage td { padding: 7px 12px !important; border: none !important; border-top: 1px solid rgba(255,255,255,0.04) !important; }

/* ── 버튼 — pill shape ── */
.stButton > button { border-radius: 20px !important; font-weight: 500 !important; font-size: 12px !important; padding: 6px 16px !important; border: 1px solid rgba(255,255,255,0.08) !important; background: rgba(255,255,255,0.04) !important; color: #c4cede !important; transition: all 0.2s ease !important; backdrop-filter: blur(4px); }
.stButton > button:hover { background: rgba(99,102,241,0.1) !important; border-color: rgba(99,102,241,0.3) !important; color: #e8edf5 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── 상태 뱃지 ── */
.status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 600; letter-spacing: 0.03em; backdrop-filter: blur(4px); }
.status-badge.live { background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.2); color: #34d399; }
.status-badge.waiting { background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.2); color: #fbbf24; }
.status-badge.off { background: rgba(148,163,184,0.08); border: 1px solid rgba(148,163,184,0.12); color: #64748b; }

/* ── 로그 패널 ── */
.log-entry-st { font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 10px; line-height: 1.7; padding: 1px 0; }
.log-ts { color: #334155; } .log-tool { color: #f59e0b; font-weight: 600; } .log-agent { color: #a78bfa; font-weight: 600; } .log-ok { color: #34d399; font-weight: 600; } .log-sys { color: #38bdf8; font-weight: 600; }
.stat-box { text-align: center; padding: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }
.stat-val { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 700; color: #34d399; }
.stat-lbl { font-size: 8px; color: #475569; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; }

/* ── 고정 로그 패널 ── */
.fixed-log-panel { position: fixed; top: 56px; right: 0; bottom: 0; width: 260px; background: linear-gradient(180deg, #0c1120 0%, #0a0e17 100%); border-left: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; z-index: 999; }
.fixed-log-panel .log-header { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.06); display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.fixed-log-panel .log-header .lh-title { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #475569; }
.fixed-log-panel .log-header .live-dot { width: 6px; height: 6px; border-radius: 50%; background: #34d399; margin-left: auto; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.fixed-log-panel .log-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.06); flex-shrink: 0; }
.fixed-log-panel .log-scroll { flex: 1; overflow-y: auto; padding: 10px 12px; font-family: 'JetBrains Mono', monospace; font-size: 10px; }
.fixed-log-panel .log-scroll::-webkit-scrollbar { width: 2px; }
.fixed-log-panel .log-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

/* ── expander ── */
[data-testid="stExpander"] { background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #64748b !important; font-size: 11px !important; font-weight: 500 !important; }
[data-testid="stExpander"] summary:hover { color: #94a3b8 !important; }

/* ── 인풋 ── */
.stTextInput input { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important; color: #c4cede !important; font-size: 12px !important; }
.stTextInput input:focus { border-color: rgba(99,102,241,0.4) !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.1) !important; }
.stTextInput input::placeholder { color: #334155 !important; }

/* ── 채팅 입력 ── */
[data-testid="stChatInput"] { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 14px !important; color: #c4cede !important; font-size: 13px !important; }

/* ── 레이아웃 ── */
section.main .block-container { padding-right: 280px !important; }
@media(max-width:1100px) { .fixed-log-panel { display:none; } section.main .block-container { padding-right: 1rem !important; } }

/* ── 라디오 ── */
.stRadio > div { gap: 4px !important; }
.stRadio label { font-size: 12px !important; }
</style>
"""
st.markdown(_css, unsafe_allow_html=True)

# ── 세션 상태 초기화 ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "demo"  # "demo" | "agentcore"
if "agent_arn" not in st.session_state:
    # 환경변수에서 ARN 자동 로딩 (CF가 Phase 2 완료 후 설정)
    env_arn = os.environ.get("AGENTCORE_RUNTIME_ARN", "")
    st.session_state.agent_arn = env_arn
if "agent_status" not in st.session_state:
    st.session_state.agent_status = "off"  # "off" | "connecting" | "ready"
if "agent_name" not in st.session_state:
    st.session_state.agent_name = ""
if "logs" not in st.session_state:
    st.session_state.logs = [
        {"ts": "00:00", "tag": "sys", "msg": "Workshop UI 시작됨"},
        {"ts": "00:00", "tag": "sys", "msg": "샘플 데이터 로드 대기 중..."},
    ]
if "tool_calls_count" not in st.session_state:
    st.session_state.tool_calls_count = 0
if "turns" not in st.session_state:
    st.session_state.turns = 0


def add_log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    st.session_state.logs.append({"ts": ts, "tag": tag, "msg": msg})


def render_log_entry(entry):
    tag_class = {"tool": "log-tool", "agent": "log-agent", "ok": "log-ok", "sys": "log-sys"}.get(entry["tag"], "log-sys")
    tag_label = {"tool": "[TOOL]", "agent": "[AGNT]", "ok": "[OK]", "sys": "[SYS]"}.get(entry["tag"], "[LOG]")
    return f'<span class="log-ts">{entry["ts"]}</span> <span class="{tag_class}">{tag_label}</span> {entry["msg"]}'


# Tool 이름 → 이모지 매핑
TOOL_ICONS = {
    "query_sales_db": "📊", "weather_api": "🌤️", "calc_order_qty": "🧮",
    "submit_order": "📦", "query_waste_db": "🗑️", "scan_all_stores": "🔍",
    "detect_anomaly": "🚨", "get_inventory": "📦",
}


def _tool_status_html(done_tools, current=None, thinking=False):
    """Tool 실행 상태를 인라인 HTML로 생성"""
    lines = []
    if thinking and not done_tools and not current:
        return '<div style="padding:8px 0;font-size:13px;color:#5a6a90">🔍 요청을 분석하고 있어요...</div>'
    for tc in done_tools:
        icon = TOOL_ICONS.get(tc["tool"], "🔧")
        lines.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12.5px">'
            f'<span>{icon}</span>'
            f'<span style="color:#dce6ff">{tc["tool"]}</span>'
            f'<span style="color:#00e87a;margin-left:auto;font-size:11px">✅ {tc.get("output","")[:35]}</span>'
            f'</div>'
        )
    if current:
        icon = TOOL_ICONS.get(current["tool"], "🔧")
        lines.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12.5px">'
            f'<span>{icon}</span>'
            f'<span style="color:#ffd060">{current["tool"]}</span>'
            f'<span style="color:#ffd060;margin-left:auto;font-size:11px">⏳ 실행 중...</span>'
            f'</div>'
        )
    return '<div style="background:#111826;border:1px solid #1e2840;border-radius:8px;padding:8px 12px;margin:4px 0">' + "".join(lines) + '</div>'


def _stream_text(text):
    """텍스트를 스트리밍처럼 표시"""
    placeholder = st.empty()
    displayed = ""
    # 줄 단위로 스트리밍 (글자 단위보다 자연스럽고 빠름)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        displayed += line + ("\n" if i < len(lines) - 1 else "")
        placeholder.markdown(displayed)
        if line.strip():
            time.sleep(0.04)
    placeholder.markdown(text)


# ══════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    # 로고
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#818cf8);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px">GS</div>
        <div>
            <div style="font-size:14px;font-weight:700;color:#e2e8f0"><span style="color:#818cf8">GS</span> Retail AI Agent</div>
            <div style="font-size:9px;color:#475569;letter-spacing:0.04em">Workshop — Kiro × Strands × AgentCore</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Agent 상태 ──
    if st.session_state.agent_status == "ready":
        st.markdown('<div class="status-badge live">🟢 Agent Ready</div>', unsafe_allow_html=True)
    elif st.session_state.agent_status == "connecting":
        st.markdown('<div class="status-badge waiting">🟡 연결 중...</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge off">⚪ Agent 미연결</div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Agent 연결 섹션 ──
    st.markdown("##### 🔗 Agent 연결")

    connect_method = st.radio(
        "연결 방법", ["수동 입력 (ARN)", "자동 검색"],
        horizontal=True, label_visibility="collapsed"
    )

    if connect_method == "수동 입력 (ARN)":
        arn_input = st.text_input(
            "Runtime ARN",
            value=st.session_state.agent_arn,
            placeholder="arn:aws:bedrock-agentcore:<region>:...",
            label_visibility="collapsed",
        )
        if arn_input != st.session_state.agent_arn:
            st.session_state.agent_arn = arn_input

    else:  # 자동 검색
        if st.button("🔍 배포된 Agent 검색", use_container_width=True):
            with st.spinner("AgentCore Runtime 검색 중..."):
                try:
                    from agentcore_client import list_agent_runtimes
                    runtimes = list_agent_runtimes()
                    if runtimes and "error" not in runtimes[0]:
                        st.session_state["discovered_runtimes"] = runtimes
                        add_log("sys", f"{len(runtimes)}개 Runtime 발견")
                    else:
                        st.warning(f"검색 실패: {runtimes[0].get('error', 'Unknown')}")
                        add_log("sys", "Runtime 검색 실패")
                except Exception as e:
                    st.warning(f"AWS 연결 실패: {e}")
                    add_log("sys", f"AWS 연결 실패: {e}")

        if "discovered_runtimes" in st.session_state:
            for rt in st.session_state.discovered_runtimes:
                if "error" in rt:
                    continue
                status_emoji = "🟢" if rt["status"] == "READY" else "🟡"
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{status_emoji} {rt['name']}**<br><span style='font-size:10px;color:#5a6a90'>{rt['status']}</span>", unsafe_allow_html=True)
                with col2:
                    if st.button("가져오기", key=f"import_{rt['arn'][:20]}"):
                        st.session_state.agent_arn = rt["arn"]
                        st.session_state.agent_name = rt["name"]
                        add_log("sys", f"Agent 선택: {rt['name']}")

    # 연결 버튼
    if st.session_state.agent_arn:
        if st.session_state.agent_status != "ready":
            if st.button("⚡ Agent 연결하기", type="primary", use_container_width=True):
                st.session_state.agent_status = "connecting"
                add_log("sys", "AgentCore 연결 시도...")
                with st.spinner("Runtime 검증 중..."):
                    try:
                        from agentcore_client import validate_runtime
                        result = validate_runtime(st.session_state.agent_arn)
                        if result.get("valid") and result.get("ready"):
                            st.session_state.agent_status = "ready"
                            st.session_state.agent_mode = "agentcore"
                            st.session_state.agent_name = result.get("name", st.session_state.agent_arn.split("/")[-1])
                            add_log("ok", f"Agent 연결 완료: {st.session_state.agent_name} (READY)")
                            st.rerun()
                        elif result.get("valid"):
                            st.session_state.agent_status = "off"
                            st.warning(f"Runtime 상태: {result.get('status')} — READY가 아닙니다. 배포 완료를 기다려주세요.")
                            add_log("sys", f"Runtime 상태: {result.get('status')}")
                        else:
                            st.session_state.agent_status = "off"
                            st.error(f"검증 실패: {result.get('error')}")
                            add_log("sys", f"검증 실패: {result.get('error')}")
                    except Exception as e:
                        st.session_state.agent_status = "off"
                        st.error(f"AWS 연결 실패: {e}")
                        add_log("sys", f"AWS 연결 실패: {e}")
        else:
            if st.button("🔌 연결 해제", use_container_width=True):
                st.session_state.agent_status = "off"
                st.session_state.agent_mode = "demo"
                add_log("sys", "Agent 연결 해제됨")
                st.rerun()

    st.divider()

    # ── 현재 모드 표시 ──
    if st.session_state.agent_mode == "agentcore":
        st.markdown(f"""
        <div style="background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.15);border-radius:12px;padding:10px 12px">
            <div style="font-size:10px;color:#34d399;font-weight:600;text-transform:uppercase;letter-spacing:0.08em">🤖 연결된 Agent</div>
            <div style="font-size:12px;font-weight:600;color:#e2e8f0;margin-top:3px">{st.session_state.agent_name}</div>
            <div style="font-size:9px;color:#475569;margin-top:2px">AgentCore · Strands SDK · Bedrock</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(251,191,36,0.04);border:1px solid rgba(251,191,36,0.12);border-radius:12px;padding:10px 12px">
            <div style="font-size:10px;color:#fbbf24;font-weight:600">💬 데모 모드</div>
            <div style="font-size:10px;color:#475569;margin-top:3px;line-height:1.5">샘플 데이터 기반 시뮬레이션<br>Agent를 배포하면 실제 AgentCore로 전환됩니다</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── 빠른 질문 (카테고리별 + 랜덤 추천) ──
    import random

    # 세션별 고정 시드 (새로고침 시 변경)
    if "qq_seed" not in st.session_state:
        st.session_state.qq_seed = random.randint(0, 9999)

    qq_categories = {
        "📦 발주": [
            "강남역점 내일 발주 해줘",
            "역삼역점 이번주 발주 계산해줘",
            "잠실새내점 도시락만 발주해줘",
            "테헤란로점 금요일 발주인데 음료 많이 시켜줘",
            "선릉점 내일 발주 부탁해",
            "홍대입구점 주말 발주 해줘",
            "석촌점 야구 경기 있는 날 발주",
            "여의도점 월요일 발주 해줘",
        ],
        "📊 분석": [
            "역삼역점 폐기율 어때?",
            "강남역점 최근 매출 추세 알려줘",
            "잠실점 재고 현황 보여줘",
            "홍대입구점 스낵 폐기율 왜 높아?",
            "내일 날씨가 매출에 영향 줄까?",
            "이번주 베스트셀러 카테고리는?",
        ],
        "🚨 모니터링": [
            "이번주 이상 점포 있어?",
            "폐기율 5% 넘는 점포 알려줘",
            "재고 부족 점포 스캔해줘",
            "석촌점 도시락 폐기율 심각하지 않아?",
        ],
    }

    # 카테고리 탭
    st.markdown("##### 💬 이런 걸 물어보세요")

    qq_tab = st.radio(
        "질문 카테고리", list(qq_categories.keys()),
        horizontal=True, label_visibility="collapsed",
        key="qq_tab",
    )

    # 선택된 카테고리에서 3개 랜덤 추출
    rng = random.Random(st.session_state.qq_seed + hash(qq_tab))
    pool = qq_categories[qq_tab]
    picks = rng.sample(pool, min(3, len(pool)))

    for q in picks:
        if st.button(q, key=f"qq_{hash(q)}", use_container_width=True):
            st.session_state["pending_question"] = q
            st.rerun()

    # 다른 질문 보기
    if st.button("🔄 다른 질문 보기", key="qq_refresh", use_container_width=True):
        st.session_state.qq_seed = random.randint(0, 9999)
        st.rerun()

    st.divider()

    # ── 세션 관리 ──
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.turns = 0
        st.session_state.tool_calls_count = 0
        st.session_state.logs = [{"ts": time.strftime("%H:%M:%S"), "tag": "sys", "msg": "대화 초기화됨"}]
        st.rerun()


# ══════════════════════════════════════════════════════════════
# 메인 영역 — 채팅 + 고정 로그 패널
# ══════════════════════════════════════════════════════════════

# ── 고정 우측 로그 패널 (HTML로 렌더링) ──
log_entries_html = ""
for entry in reversed(st.session_state.logs[-50:]):
    log_entries_html += f'<div class="log-entry-st">{render_log_entry(entry)}</div>'

st.markdown(f"""
<div class="fixed-log-panel">
    <div class="log-header">
        <span class="lh-title">Agent 실행 로그</span>
        <span class="live-dot"></span>
    </div>
    <div class="log-stats">
        <div class="stat-box"><div class="stat-val">{st.session_state.tool_calls_count}</div><div class="stat-lbl">Tool Calls</div></div>
        <div class="stat-box"><div class="stat-val">{st.session_state.turns}</div><div class="stat-lbl">Turns</div></div>
    </div>
    <div class="log-scroll" id="logScroll">{log_entries_html}</div>
</div>
<script>
    var el = document.getElementById('logScroll');
    if(el) el.scrollTop = 0;
</script>
""", unsafe_allow_html=True)

# ── 채팅 영역 ──
# 헤더 — 모드별 스타일 분기
if st.session_state.agent_mode == "agentcore":
    mode_label = f"🤖 {st.session_state.agent_name}"
    status_label = "AgentCore · Bedrock Claude"
    status_color = "#34d399"
    icon_bg = "rgba(52,211,153,0.08)"
    icon_border = "rgba(52,211,153,0.2)"
    dot_html = '<span style="width:6px;height:6px;border-radius:50%;background:#34d399;display:inline-block;animation:pulse 2s ease-in-out infinite;margin-left:4px"></span>'
    badge_html = """
        <span style="padding:2px 8px;border-radius:20px;font-size:9px;font-weight:600;background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.2);color:#34d399;letter-spacing:0.05em">● LIVE</span>
    """
else:
    mode_label = "💬 GS25 발주 도우미"
    status_label = "데모 모드 · 샘플 데이터"
    status_color = "#fbbf24"
    icon_bg = "rgba(251,191,36,0.06)"
    icon_border = "rgba(251,191,36,0.15)"
    dot_html = ""
    badge_html = '<span style="padding:2px 8px;border-radius:20px;font-size:9px;font-weight:600;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.15);color:#fbbf24;letter-spacing:0.05em">DEMO</span>'

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:6px 0;margin-bottom:0">
    <div style="width:36px;height:36px;background:{icon_bg};border:1px solid {icon_border};border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px">📦</div>
    <div>
        <div style="font-size:13px;font-weight:600;color:#e2e8f0">{mode_label}{dot_html}</div>
        <div style="font-size:10px;color:{status_color}">{status_label}</div>
    </div>
    <div style="margin-left:auto">{badge_html}</div>
</div>
""", unsafe_allow_html=True)

# 데모 모드 배너
if st.session_state.agent_mode != "agentcore":
    st.markdown("""
    <div style="background:rgba(251,191,36,0.04);border:1px solid rgba(251,191,36,0.1);border-radius:12px;padding:7px 12px;margin:6px 0;display:flex;align-items:center;gap:8px">
        <span style="font-size:13px;opacity:0.7">💡</span>
        <span style="font-size:10px;color:#94a3b8">데모 모드 · Agent를 배포하고 ARN을 연결하면 <span style="color:#34d399;font-weight:600">실제 AI Agent</span>로 전환됩니다</span>
    </div>
    """, unsafe_allow_html=True)

# 메시지 표시
if not st.session_state.messages:
    if st.session_state.agent_mode == "agentcore":
        st.markdown(f"""
        <div style="text-align:center;padding:60px 40px;color:#323d58">
            <div style="font-size:48px;margin-bottom:12px">🤖</div>
            <div style="font-size:18px;font-weight:700;color:#00e87a;margin-bottom:8px">Agent 연결 완료!</div>
            <div style="font-size:14px;color:#dce6ff;margin-bottom:4px">{st.session_state.agent_name}</div>
            <div style="font-size:12px;color:#5a6a90;line-height:1.8">
                Bedrock Claude + Strands SDK 기반 실제 AI Agent가 동작합니다<br>
                아래 입력창에 자연어로 질문해보세요!
            </div>
            <div style="margin-top:16px;display:flex;justify-content:center;gap:8px">
                <span style="padding:4px 12px;border-radius:12px;font-size:11px;background:rgba(0,232,122,0.08);border:1px solid rgba(0,232,122,0.2);color:#00e87a">● AI 응답</span>
                <span style="padding:4px 12px;border-radius:12px;font-size:11px;background:rgba(255,153,0,0.08);border:1px solid rgba(255,153,0,0.2);color:#FF9900">Tool 자동 호출</span>
                <span style="padding:4px 12px;border-radius:12px;font-size:11px;background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);color:#a78bfa">실시간 로그</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:50px 40px 20px;color:#323d58">
            <div style="font-size:48px;opacity:0.3;margin-bottom:12px">📦</div>
            <div style="font-size:18px;font-weight:700;color:#ffd060;margin-bottom:8px">데모 모드</div>
            <div style="font-size:12px;color:#5a6a90;line-height:1.6;margin-bottom:20px">
                샘플 데이터 기반으로 동작합니다 · ARN을 연결하면 실제 AI Agent로 전환
            </div>
            <div style="font-size:11px;color:#323d58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px">이런 걸 물어보세요</div>
        </div>
        """, unsafe_allow_html=True)

        # 중앙 추천 질문 칩 (2열)
        _chip_qs = [
            ("📦", "강남역점 내일 발주 해줘"),
            ("📊", "역삼역점 폐기율 어때?"),
            ("🌤️", "내일 날씨가 매출에 영향 줄까?"),
            ("🚨", "이번주 이상 점포 있어?"),
            ("🍱", "잠실새내점 도시락만 발주해줘"),
            ("🍺", "석촌점 야구 경기 있는 날 발주"),
        ]
        cols = st.columns(2)
        for i, (icon, q) in enumerate(_chip_qs):
            with cols[i % 2]:
                if st.button(f"{icon} {q}", key=f"chip_{i}", use_container_width=True):
                    st.session_state["pending_question"] = q
                    st.rerun()

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "📦"):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander(f"🔧 Agent가 사용한 도구 ({len(msg['tool_calls'])}개)", expanded=False):
                for tc in msg["tool_calls"]:
                    st.markdown(f"""<div style="background:#0d111c;border:1px solid #263354;border-radius:6px;padding:8px 10px;margin:4px 0;font-family:monospace;font-size:11px">
                    <span style="color:#FF9900;font-weight:700">{tc['tool']}</span>
                    <span style="color:#323d58">→</span>
                    <span style="color:#00e87a">✓ done</span>
                    <span style="color:#323d58;margin-left:8px">{tc.get('time','')}</span>
                    <br><span style="color:#00d4ff">{tc.get('input','')}</span>
                    <br><span style="color:#00e87a">{tc.get('output','')}</span>
                    </div>""", unsafe_allow_html=True)

        # 마지막 assistant 메시지에만 액션/추천 표시
        is_last_assistant = (msg["role"] == "assistant" and idx == len(st.session_state.messages) - 1)
        if is_last_assistant:
            # 액션 버튼
            if msg.get("actions"):
                action_cols = st.columns(len(msg["actions"]))
                for ai, act in enumerate(msg["actions"]):
                    with action_cols[ai]:
                        if st.button(act["label"], key=f"act_{idx}_{ai}", use_container_width=True):
                            st.session_state["pending_question"] = act["query"]
                            st.rerun()

            # 후속 질문 제안
            if msg.get("suggestions"):
                st.markdown('<div style="margin-top:8px;font-size:10px;color:#323d58;text-transform:uppercase;letter-spacing:0.08em">이어서 물어보기</div>', unsafe_allow_html=True)
                sug_cols = st.columns(min(len(msg["suggestions"]), 3))
                for si, sug in enumerate(msg["suggestions"][:3]):
                    with sug_cols[si]:
                        if st.button(sug, key=f"sug_{idx}_{si}", use_container_width=True):
                            st.session_state["pending_question"] = sug
                            st.rerun()

# 입력 처리
pending = st.session_state.pop("pending_question", None)
prompt = st.chat_input("메시지를 입력하세요...", key="chat_input")
user_input = pending or prompt

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.turns += 1
    add_log("agent", f"User: {user_input[:40]}...")

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="📦"):
        # Tool 실행 상태를 순차 표시할 placeholder
        status_area = st.empty()
        add_log("agent", "Analyzing request...")

        # Agent 호출
        if st.session_state.agent_mode == "agentcore" and st.session_state.agent_status == "ready":
            # 실제 AgentCore — 호출 전 "분석 중" 표시
            status_area.markdown(_tool_status_html([], thinking=True), unsafe_allow_html=True)
            try:
                from agentcore_client import invoke_agent
                result = invoke_agent(
                    st.session_state.agent_arn, user_input, st.session_state.session_id,
                )
            except Exception as e:
                result = {"text": f"❌ Agent 호출 실패: {e}", "tool_calls": []}
            # AgentCore 응답의 tool_calls도 순차 표시
            tool_calls = result.get("tool_calls", [])
            for i, tc in enumerate(tool_calls):
                status_area.markdown(
                    _tool_status_html(tool_calls[:i], current=tc),
                    unsafe_allow_html=True
                )
                time.sleep(0.3)
            if tool_calls:
                status_area.markdown(_tool_status_html(tool_calls), unsafe_allow_html=True)
                time.sleep(0.2)
        else:
            # 데모 모드 — Tool 하나씩 순차 표시
            result = demo_response(user_input)
            tool_calls = result.get("tool_calls", [])
            for i, tc in enumerate(tool_calls):
                # 현재까지 완료된 것 + 진행 중인 것 표시
                status_area.markdown(
                    _tool_status_html(tool_calls[:i], current=tc),
                    unsafe_allow_html=True
                )
                time.sleep(0.5 + 0.3 * (i % 2))
            # 전부 완료 표시
            if tool_calls:
                status_area.markdown(
                    _tool_status_html(tool_calls, current=None),
                    unsafe_allow_html=True
                )
                time.sleep(0.3)

        # Tool call 로그 기록
        for tc in result.get("tool_calls", []):
            add_log("tool", f"{tc['tool']} → {tc.get('output', '')[:50]}")
            st.session_state.tool_calls_count += 1
        add_log("ok", "Response sent")

        # 상태 영역을 최종 결과로 교체
        status_area.empty()

        # 최종 응답 스트리밍 표시
        _stream_text(result["text"])

        # Tool call 상세 (접기)
        if result.get("tool_calls"):
            with st.expander(f"🔧 사용된 도구 ({len(result['tool_calls'])}개)", expanded=False):
                for tc in result["tool_calls"]:
                    st.markdown(f"""<div style="background:#0d111c;border:1px solid #263354;border-radius:6px;padding:8px 10px;margin:4px 0;font-family:monospace;font-size:11px">
                    <span style="color:#FF9900;font-weight:700">{tc['tool']}</span>
                    <span style="color:#323d58">→</span>
                    <span style="color:#00e87a">✓ done</span>
                    <span style="color:#323d58;margin-left:8px">{tc.get('time','')}</span>
                    <br><span style="color:#00d4ff">{tc.get('input','')}</span>
                    <br><span style="color:#00e87a">{tc.get('output','')}</span>
                    </div>""", unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant", "content": result["text"],
        "tool_calls": result.get("tool_calls", []),
        "actions": result.get("actions", []),
        "suggestions": result.get("suggestions", []),
    })
    st.rerun()
