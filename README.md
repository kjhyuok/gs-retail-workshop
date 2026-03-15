# GS Retail AI Agent Workshop

> **Zero to Builder with Kiro!** — GS Retail 편의점 발주 자동화 Agent 핸즈온 워크샵

## Overview

Kiro IDE + AWS Strands SDK + Amazon Bedrock + AgentCore를 활용하여,
**자연어만으로 AI Agent를 만들고 AWS에 배포하는** 핸즈온 워크샵입니다.

| 항목 | 내용 |
|------|------|
| 대상 | GS Retail AX팀 (비개발자 포함) |
| 시간 | 반일 (약 4시간) |
| 리전 | us-west-2 (Oregon) |
| 난이도 | 입문 (코딩 경험 불필요) |

## Repo 구조

```
gs-retail-workshop/
│
├── README.md                        # 이 문서 (SA 가이드)
├── cfn-workshop-participant.yaml    # CloudFormation 템플릿 (참가자 계정에 배포)
│
├── app.py                           # Streamlit UI 메인 앱
├── demo_mode.py                     # 데모 모드 (Agent 미연결 시)
├── agentcore_client.py              # AgentCore 클라이언트 (ARN 연결)
├── requirements.txt                 # Streamlit 의존성
├── .streamlit/config.toml           # Streamlit 설정 (다크 테마)
│
├── data/                            # 샘플 데이터 (10개 점포)
│   ├── sales.json                   #   매출 데이터 (4주간)
│   ├── weather.json                 #   날씨 예보
│   ├── inventory.json               #   재고 현황
│   ├── waste.json                   #   폐기율
│   ├── stores.json                  #   점포 마스터
│   └── events.json                  #   이벤트 정보
│
└── participant-project/             # 참가자 프로젝트 템플릿
    ├── data/                        #   로컬 테스트용 샘플 데이터
    │   ├── sales.json
    │   ├── weather.json
    │   ├── inventory.json
    │   └── waste.json
    ├── requirements.txt             #   Python 의존성
    └── .gitignore
```

## SA 사전 준비 체크리스트

### 1. 이 Repo 준비

```bash
# 이미 완료된 상태
git clone https://github.com/kjhyuok/gs-retail-workshop.git
```

### 2. 워크샵 당일 — 참가자 안내

참가자는 워크샵 가이드의 **사전 준비 사항** 페이지에서 아래 URL을 복사하여 CloudFormation을 직접 실행합니다:

```
https://raw.githubusercontent.com/kjhyuok/gs-retail-workshop/main/cfn-workshop-participant.yaml
```

### 3. CloudFormation이 생성하는 리소스

| 리소스 | 설명 |
|--------|------|
| **EC2** (t4g.medium) | Streamlit UI 호스팅 + SQLite 샘플 DB |
| **EIP** | 고정 IP (EC2 재시작해도 유지) |
| **S3 Bucket** | 샘플 데이터 (Agent Tool이 참조) |
| **IAM Role** (EC2) | Bedrock + AgentCore + S3 접근 |
| **IAM Role** (Agent Runtime) | AgentCore Agent 실행 권한 |

### 4. 참가자 프로젝트 폴더 준비

참가자 PC에 `participant-project/`를 `gs-retail-agent`로 복사하여 제공합니다:

```bash
# 참가자에게 배포할 프로젝트 폴더
cp -r participant-project gs-retail-agent
```

또는 워크샵 가이드에서 직접 다운로드 안내:

```bash
git clone https://github.com/kjhyuok/gs-retail-workshop.git
cp -r gs-retail-workshop/participant-project gs-retail-agent
cd gs-retail-agent
```

## 워크샵 흐름

```
참가자 PC (Kiro IDE)                     참가자 AWS 계정
┌──────────────────┐                ┌─────────────────────────────┐
│ Lab 1: Steering  │                │ prereq: CFN 배포            │
│ Lab 2: Spec      │                │  → EC2 + Streamlit + S3     │
│ Lab 3: 코드 생성 │                │                             │
│   └─ data/*.json │                │ Lab 4: agentcore launch     │
│      로컬 테스트 │                │  → Agent Runtime (ARN)      │
└──────────────────┘                │                             │
                                    │ Lab 5: Streamlit에 ARN 연결 │
                                    │  → 실제 Agent 대화          │
                                    └─────────────────────────────┘
```

## Streamlit UI 기능

### 3-Panel 레이아웃
- **좌측 사이드바**: Agent ARN 연결, 연결 상태, 카테고리별 빠른 질문
- **중앙 채팅**: 사용자 ↔ Agent 대화, 액션 버튼, 후속 질문 제안
- **우측 로그 패널**: Tool 호출 실시간 로그, Turns/Tool Calls 카운터

### 2가지 모드
| 모드 | 상태 | 동작 |
|------|------|------|
| **DEMO** | Agent 미연결 (노란색) | 샘플 데이터 기반 키워드 매칭 응답 |
| **LIVE** | ARN 연결됨 (초록색) | AgentCore → Bedrock Claude 실제 AI 응답 |

## 샘플 데이터

10개 점포, 4개 카테고리(도시락/음료/스낵/생활용품) 전체 커버:

| 파일 | 내용 | 비고 |
|------|------|------|
| sales.json | 점포별 4주 매출 + 일평균 | 점포 유형별 판매량 차이 |
| weather.json | 5개 지역 내일 날씨 | 강남 맑음, 마포 흐림 등 |
| inventory.json | 점포별 현재 재고 | 일부 재고 부족 설정 |
| waste.json | 점포별 폐기율 | 석촌점 12.3% 등 고폐기 |
| stores.json | 10개 점포 마스터 | 지역/유형 정보 |
| events.json | 야구/콘서트 등 이벤트 | 비즈니스 규칙 테스트용 |

## 문제 해결

| 문제 | 해결 |
|------|------|
| CFN 스택 생성 실패 | IAM 권한 체크 확인, 리전 us-west-2 확인 |
| Streamlit 접속 안 됨 | Security Group 8501 포트 확인, EIP 할당 확인 |
| Agent 배포 실패 | `bedrock-agentcore:*` IAM 권한 확인 |
| 데모 모드에서 점포 인식 안 됨 | 정확한 점포명 사용 (역삼역점, 강남역점 등) |

## License

This project is for GS Retail internal workshop use only.
