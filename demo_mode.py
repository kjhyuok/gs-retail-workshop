"""데모 모드 — AgentCore 없이 샘플 데이터로 시뮬레이션 + Bedrock fallback"""
import json, os, random, time
from datetime import datetime

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

DATA_DIR = os.environ.get("SAMPLE_DATA_DIR", "./data")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
BEDROCK_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

CAT_NAMES = {"dosirak": "도시락류", "beverage": "음료류", "snack": "스낵류", "household": "생활용품"}
CAT_EMOJI = {"dosirak": "🍱", "beverage": "🥤", "snack": "🍪", "household": "🧴"}
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def _invoke_bedrock(message):
    if not HAS_BOTO3:
        return None
    try:
        client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
        resp = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "system": "당신은 GS25 편의점 발주 자동화 도우미입니다. 친절하고 간결하게 한국어로 답변하세요.",
                "messages": [{"role": "user", "content": message}],
            }),
        )
        body = json.loads(resp["body"].read())
        return body.get("content", [{}])[0].get("text", None)
    except Exception:
        return None


def load_json(name):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _find_store(stores, message):
    """메시지에서 점포명 추출 (부분 매칭 지원)"""
    store_list = stores if isinstance(stores, list) else stores.get("stores", [])
    # 정확 매칭
    for s in store_list:
        name = s.get("name", "")
        if name and name in message:
            return name, s
    # 부분 매칭 (강남 → 강남역점)
    for s in store_list:
        name = s.get("name", "")
        short = name.replace("점", "").replace("역", "").replace("호", "")
        for keyword in [name, short, name[:2]]:
            if keyword and keyword in message:
                return name, s
    return None, None


def _get_weekday_str():
    return WEEKDAY_KR[datetime.now().weekday()]


def demo_response(message):
    """샘플 데이터 기반 데모 응답 생성 — 고품질 응답 + 액션 + 후속 제안"""
    msg = message.lower()
    tool_calls = []
    actions = []      # 클릭 가능한 액션 버튼
    suggestions = []   # 후속 질문 제안

    stores = load_json("stores.json") or []
    sales = load_json("sales.json") or {}
    weather_data = load_json("weather.json") or {}
    inventory = load_json("inventory.json") or {}
    waste = load_json("waste.json") or {}
    events = load_json("events.json") or []

    store_name, store_info = _find_store(stores, message)
    today = _get_weekday_str()

    # ═══════════════════════════════════════════
    # 발주 요청
    # ═══════════════════════════════════════════
    if "발주" in msg:
        sn = store_name or "역삼역점"
        si = store_info or {"area": "강남", "type": "오피스"}
        s_data = sales.get(sn, {})
        avg = s_data.get("daily_average", {"dosirak": 62, "beverage": 180, "snack": 130, "household": 22})
        inv = inventory.get(sn, {}).get("inventory", {})
        low = inventory.get(sn, {}).get("low_stock", [])
        w_rates = waste.get(sn, {}).get("waste_rate", {})
        w_warnings = waste.get(sn, {}).get("warnings", [])
        area = si.get("area", "강남")
        wx = weather_data.get(area, {})
        wx_cond = wx.get("weather", "맑음")
        wx_high = wx.get("temp_high", 18)

        # 금요일 패턴
        is_friday = "금요일" in msg or "금" in msg
        has_event = any(e.get("location", "") in ["잠실", "전체"] and sn in ["잠실점", "석촌점", "잠실새내점"] for e in events)

        tool_calls = [
            {"tool": "get_sales_data", "input": f'store: "{sn}", weeks: 4', "output": f"일평균 도시락 {avg.get('dosirak',0)}개, 음료 {avg.get('beverage',0)}개", "time": "0.4s"},
            {"tool": "get_weather_forecast", "input": f'location: "{area}"', "output": f"{wx_cond}, 최고 {wx_high}°C, 강수확률 {wx.get('precipitation_prob',10)}%", "time": "0.3s"},
            {"tool": "get_inventory_status", "input": f'store: "{sn}"', "output": f"재고 부족 {len(low)}건" if low else "재고 정상", "time": "0.3s"},
            {"tool": "get_waste_rate", "input": f'store: "{sn}"', "output": f"경고 {len(w_warnings)}건" if w_warnings else "전 카테고리 정상", "time": "0.2s"},
            {"tool": "calculate_order", "input": "종합 분석 → 발주량 산출", "output": "비즈니스 규칙 적용 완료", "time": "0.5s"},
        ]

        # 발주량 계산
        order_rows = []
        total_qty = 0
        adjustments = []
        for cat, label in CAT_NAMES.items():
            emoji = CAT_EMOJI[cat]
            daily = avg.get(cat, 50)
            qty = daily * 7
            stock = inv.get(cat, 0)
            need = max(0, qty - stock)
            notes = []
            wr = w_rates.get(cat, 2.0)

            if wr > 5.0:
                before = need
                need = int(need * 0.85)
                notes.append(f"폐기율 {wr}% → -15%")
                adjustments.append(f"⚠️ {label} 폐기율 **{wr}%** (기준 5% 초과) → 발주량 15% 감소 적용")
            if wx_cond == "맑음" and cat == "beverage":
                need = int(need * 1.18)
                notes.append(f"맑음 +18%")
                adjustments.append(f"☀️ 내일 **맑음** 예보 → 음료류 18% 증가 적용")
            if is_friday and cat in ["snack", "beverage"]:
                need = int(need * 1.35)
                notes.append("금요일 +35%")
                adjustments.append(f"🍻 **금요일** 패턴 → {label} 35% 증가 적용")
            if has_event and cat in ["snack", "beverage"]:
                need = int(need * 1.40)
                notes.append("야구 +40%")
                adjustments.append(f"⚾ **잠실 야구 경기** → {label} 40% 증가 적용")

            total_qty += need
            note_str = f' ({", ".join(notes)})' if notes else ""
            stock_warn = " 🔴" if cat in low else ""
            order_rows.append(f"| {emoji} {label} | {daily}개 | {stock}개{stock_warn} | **{need}개**{note_str} |")

        # 고유 조정사항만
        unique_adj = list(dict.fromkeys(adjustments))

        text = f"""📦 **{sn}** 발주 분석이 완료됐습니다.

> 📍 {sn} ({si.get('area', '')}, {si.get('type', '')}) · 🌤️ 내일 {wx_cond} {wx_high}°C · 📅 {today}요일

| 카테고리 | 일평균 | 현재고 | 권장 발주량 |
|---------|--------|--------|-----------|
{chr(10).join(order_rows)}

**총 발주량: {total_qty:,}개**"""

        if unique_adj:
            text += "\n\n**📋 적용된 비즈니스 규칙:**\n" + "\n".join(unique_adj)

        if low:
            low_labels = ", ".join(CAT_NAMES.get(c, c) for c in low)
            text += f"\n\n🔴 **재고 부족 주의**: {low_labels} — 긴급 발주를 권장합니다."

        text += "\n\n이대로 발주를 진행할까요?"

        actions = [
            {"label": "✅ 발주 진행", "query": f"{sn} 발주 확정해줘"},
            {"label": "✏️ 수량 조정", "query": f"{sn} 도시락 수량을 20% 더 늘려줘"},
            {"label": "❌ 취소", "query": "발주 취소할게"},
        ]
        suggestions = []

    # ═══════════════════════════════════════════
    # 폐기율 조회
    # ═══════════════════════════════════════════
    elif "폐기" in msg:
        sn = store_name or "역삼역점"
        si = store_info or {"area": "강남", "type": "오피스"}
        w_data = waste.get(sn, {})
        rates = w_data.get("waste_rate", {})
        warnings = w_data.get("warnings", [])
        avg_rate = sum(rates.values()) / max(len(rates), 1)

        tool_calls = [
            {"tool": "get_waste_rate", "input": f'store: "{sn}"', "output": f"평균 {avg_rate:.1f}%, 경고 {len(warnings)}건", "time": "0.3s"},
            {"tool": "get_sales_data", "input": f'store: "{sn}"', "output": "매출 데이터 참조", "time": "0.2s"},
        ]

        rows = []
        for cat, label in CAT_NAMES.items():
            rate = rates.get(cat, 2.0)
            emoji = CAT_EMOJI[cat]
            if rate > 10:
                status = "🔴 심각"
                bar = "█████"
            elif rate > 5:
                status = "🟡 주의"
                bar = "███"
            else:
                status = "🟢 양호"
                bar = "█"
            rows.append(f"| {emoji} {label} | {rate}% | {bar} | {status} |")

        text = f"""🗑️ **{sn}** 폐기율 분석 리포트

> 📍 {sn} ({si.get('area', '')}) · 평균 폐기율 **{avg_rate:.1f}%**

| 카테고리 | 폐기율 | 수준 | 상태 |
|---------|-------|------|------|
{chr(10).join(rows)}"""

        if warnings:
            warn_labels = ", ".join(f"**{CAT_NAMES.get(w, w)}**" for w in warnings)
            text += f"\n\n⚠️ **기준 초과 카테고리**: {warn_labels}\n\n"
            text += "폐기율이 5%를 초과하면 자동으로 발주량이 **15% 감소** 적용됩니다. "
            text += "원인을 분석하고 발주 전략을 조정하는 것이 좋습니다."
        else:
            text += "\n\n✅ 전 카테고리 폐기율 정상 범위입니다. 우수한 재고 관리 상태예요!"

        actions = []
        suggestions = [f"📦 {sn} 폐기율 반영해서 발주 해줘"] if warnings else []

    # ═══════════════════════════════════════════
    # 재고 현황
    # ═══════════════════════════════════════════
    elif "재고" in msg:
        sn = store_name or "역삼역점"
        si = store_info or {"area": "강남", "type": "오피스"}
        inv = inventory.get(sn, {})
        items = inv.get("inventory", {})
        low = inv.get("low_stock", [])
        avg = sales.get(sn, {}).get("daily_average", {})

        tool_calls = [
            {"tool": "get_inventory_status", "input": f'store: "{sn}"', "output": f"부족 {len(low)}건" if low else "전체 정상", "time": "0.3s"},
            {"tool": "get_sales_data", "input": f'store: "{sn}"', "output": "일평균 판매량 참조", "time": "0.2s"},
        ]

        rows = []
        for cat, label in CAT_NAMES.items():
            emoji = CAT_EMOJI[cat]
            stock = items.get(cat, 0)
            daily = avg.get(cat, 50)
            days_left = round(stock / daily, 1) if daily > 0 else 99
            if days_left < 1:
                status = "🔴 긴급"
            elif days_left < 3:
                status = "🟡 부족"
            else:
                status = "🟢 충분"
            rows.append(f"| {emoji} {label} | {stock}개 | {daily}개 | {days_left}일 | {status} |")

        text = f"""📦 **{sn}** 재고 현황 리포트

> 📍 {sn} ({si.get('area', '')}) · 기준: 3일분 미만 시 부족 경고

| 카테고리 | 현재고 | 일평균 | 소진예상 | 상태 |
|---------|--------|--------|---------|------|
{chr(10).join(rows)}"""

        if low:
            low_labels = ", ".join(f"**{CAT_NAMES.get(c, c)}**" for c in low)
            text += f"\n\n🔴 **재고 부족**: {low_labels} — 3일분 미만으로 긴급 발주가 필요합니다."

        if low:
            actions = [{"label": "📦 긴급 발주 실행", "query": f"{sn} 재고 부족 카테고리 긴급 발주 해줘"}]
            suggestions = [f"🗑️ {sn} 폐기율 어때?"]
        else:
            actions = []
            suggestions = []

    # ═══════════════════════════════════════════
    # 이상 감지 / 모니터링
    # ═══════════════════════════════════════════
    elif "이상" in msg or "감지" in msg or "알림" in msg or "스캔" in msg:
        # 실제 데이터에서 이상 점포 추출
        anomalies = []
        store_list = stores if isinstance(stores, list) else []
        for s in store_list:
            sn_ = s.get("name", "")
            w = waste.get(sn_, {}).get("warnings", [])
            low = inventory.get(sn_, {}).get("low_stock", [])
            if w:
                for cat in w:
                    rate = waste.get(sn_, {}).get("waste_rate", {}).get(cat, 0)
                    anomalies.append({"store": sn_, "type": "폐기율 초과", "detail": f"{CAT_NAMES.get(cat, cat)} {rate}% (기준 5%)", "severity": "🟡"})
            if low:
                for cat in low:
                    stock = inventory.get(sn_, {}).get("inventory", {}).get(cat, 0)
                    anomalies.append({"store": sn_, "type": "재고 부족", "detail": f"{CAT_NAMES.get(cat, cat)} {stock}개 남음", "severity": "🔴"})

        tool_calls = [
            {"tool": "scan_all_stores", "input": f'stores: {len(store_list)}개 점포', "output": f"스캔 완료", "time": "0.6s"},
            {"tool": "detect_anomaly", "input": 'threshold: 5.0%', "output": f"이상 {len(anomalies)}건 감지", "time": "0.4s"},
        ]

        rows = []
        for a in anomalies[:8]:
            rows.append(f"| {a['severity']} {a['store']} | {a['type']} | {a['detail']} |")

        text = f"""🚨 **전 점포 이상 징후 스캔 결과**

> 📊 {len(store_list)}개 점포 스캔 · 이상 징후 **{len(anomalies)}건** 감지

| 점포 | 유형 | 상세 |
|------|------|------|
{chr(10).join(rows) if rows else "| — | — | 이상 징후 없음 |"}

{"⚠️ 총 **" + str(len(anomalies)) + "건**의 이상 징후가 감지되었습니다." if anomalies else "✅ 전 점포 정상 범위입니다!"}"""

        if anomalies:
            top_store = anomalies[0]["store"]
            actions = [
                {"label": "📋 상세 리포트", "query": f"{top_store} 상세 분석해줘"},
                {"label": "📦 긴급 발주", "query": f"재고 부족 점포 일괄 발주 해줘"},
            ]
            suggestions = []
        else:
            actions = []
            suggestions = []

    # ═══════════════════════════════════════════
    # 매출 / 추세
    # ═══════════════════════════════════════════
    elif "매출" in msg or "추세" in msg or "판매" in msg:
        sn = store_name or "역삼역점"
        si = store_info or {"area": "강남", "type": "오피스"}
        s_data = sales.get(sn, {})
        avg = s_data.get("daily_average", {})
        weekly = s_data.get("weekly_sales", [])

        tool_calls = [
            {"tool": "get_sales_data", "input": f'store: "{sn}", weeks: 4', "output": f"4주 데이터 조회 완료", "time": "0.4s"},
        ]

        rows = []
        for w in weekly:
            week_total = sum(v for k, v in w.items() if k != "week")
            rows.append(f"| {w.get('week','')}주차 | {w.get('dosirak',0)} | {w.get('beverage',0)} | {w.get('snack',0)} | {w.get('household',0)} | **{week_total:,}** |")

        total_daily = sum(avg.values())
        text = f"""📊 **{sn}** 매출 분석 리포트

> 📍 {sn} ({si.get('area', '')}, {si.get('type', '')}) · 최근 4주 데이터

| 주차 | 🍱 도시락 | 🥤 음료 | 🍪 스낵 | 🧴 생활 | 합계 |
|------|---------|--------|--------|--------|------|
{chr(10).join(rows)}

**📈 일평균 판매량:** 도시락 {avg.get('dosirak',0)}개 · 음료 {avg.get('beverage',0)}개 · 스낵 {avg.get('snack',0)}개 · 생활 {avg.get('household',0)}개 (총 **{total_daily}개/일**)"""

        actions = []
        suggestions = [f"📦 {sn} 이 데이터 기반으로 발주 해줘"]

    # ═══════════════════════════════════════════
    # 날씨
    # ═══════════════════════════════════════════
    elif "날씨" in msg:
        area = store_info.get("area", "강남") if store_info else "강남"
        wx = weather_data.get(area, {})

        tool_calls = [
            {"tool": "get_weather_forecast", "input": f'location: "{area}"', "output": f"{wx.get('weather','맑음')}, {wx.get('temp_high',18)}°C", "time": "0.3s"},
        ]

        cond = wx.get("weather", "맑음")
        impact = []
        if cond == "맑음":
            impact.append("☀️ 맑은 날씨 → **음료류 수요 +18%** 예상")
            impact.append("🍦 아이스크림/빙과류 판매 증가 예상")
        elif cond in ["비", "눈"]:
            impact.append("☔ 비/눈 예보 → **도시락류 수요 +12%** 예상 (외출 감소)")
            impact.append("☂️ 우산/우비 비치 확인 권장")
        else:
            impact.append("☁️ 흐림 → 특별한 수요 변동 없음")

        text = f"""🌤️ **내일 날씨 & 매출 영향 분석**

> 📍 {wx.get('location', area)} · {wx.get('date', '내일')}

| 항목 | 내용 |
|------|------|
| 날씨 | {cond} |
| 최고기온 | {wx.get('temp_high', 18)}°C |
| 최저기온 | {wx.get('temp_low', 7)}°C |
| 강수확률 | {wx.get('precipitation_prob', 10)}% |

**📈 예상 매출 영향:**
{chr(10).join(impact)}"""

        sn = store_name or "역삼역점"
        actions = []
        suggestions = [f"📦 {sn} 내일 날씨 반영해서 발주 해줘"]

    # ═══════════════════════════════════════════
    # 기본 / Bedrock fallback
    # ═══════════════════════════════════════════
    else:
        bedrock_answer = _invoke_bedrock(message)
        if bedrock_answer:
            tool_calls = [
                {"tool": "bedrock_claude", "input": f'model: "{BEDROCK_MODEL_ID}"', "output": "응답 생성 완료", "time": "1.2s"},
            ]
            text = bedrock_answer
            suggestions = []
        else:
            store_count = len(stores) if isinstance(stores, list) else 0
            text = f"""안녕하세요! **GS25 발주 자동화 Agent**입니다 📦

현재 **{store_count}개 점포** 데이터가 준비되어 있어요.
아래 버튼을 눌러보거나, 자유롭게 질문해주세요!"""

            suggestions = [
                "📦 강남역점 내일 발주 해줘",
                "📊 역삼역점 폐기율 어때?",
                "🚨 이번주 이상 점포 있어?",
                "🌤️ 내일 날씨가 매출에 영향 줄까?",
            ]

    return {
        "text": text,
        "tool_calls": tool_calls,
        "actions": actions,
        "suggestions": suggestions,
    }
