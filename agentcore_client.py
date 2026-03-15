"""AgentCore 클라이언트 — Runtime 조회 및 Agent 호출"""
import json
import os
import boto3
from botocore.exceptions import ClientError

DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")  # Workshop 기본 리전


def _control_client(region=None):
    return boto3.client("bedrock-agentcore-control", region_name=region or DEFAULT_REGION)


def _data_client(region=None):
    return boto3.client("bedrock-agentcore", region_name=region or DEFAULT_REGION)


def validate_runtime(runtime_arn, region=None):
    """Runtime ARN이 유효하고 READY 상태인지 검증"""
    try:
        # ARN에서 ID 추출: arn:aws:bedrock-agentcore:region:account:agent/ID:version
        runtime_id = runtime_arn.split("/")[-1].split(":")[0]
        client = _control_client(region)
        resp = client.get_agent_runtime(agentRuntimeId=runtime_id)
        status = resp.get("status", "UNKNOWN")
        name = resp.get("agentRuntimeName", "Unknown")
        return {"valid": True, "status": status, "name": name, "ready": status == "READY"}
    except ClientError as e:
        return {"valid": False, "error": f"{e.response['Error']['Code']}: {e.response['Error']['Message']}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def list_agent_runtimes(region=None):
    """배포된 AgentCore Runtime 목록 조회"""
    try:
        client = _control_client(region)
        resp = client.list_agent_runtimes()
        return [
            {
                "arn": rt.get("agentRuntimeArn", ""),
                "name": rt.get("agentRuntimeName", "Unknown"),
                "status": rt.get("status", "UNKNOWN"),
            }
            for rt in resp.get("agentRuntimeSummaries", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


def invoke_agent(runtime_arn, message, session_id, region=None):
    """AgentCore Runtime에 메시지 전송 및 응답 수신"""
    try:
        client = _data_client(region)
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            payload=json.dumps({"query": message, "session_id": session_id}).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )
        body = resp.get("body", b"")
        if hasattr(body, "read"):
            body = body.read()
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return parse_agent_response(body)
    except ClientError as e:
        return {"text": f"❌ AWS 오류: {e.response['Error']['Code']} — {e.response['Error']['Message']}", "tool_calls": []}
    except Exception as e:
        return {"text": f"❌ Agent 호출 실패: {str(e)}", "tool_calls": []}


def parse_agent_response(raw):
    """Agent 응답에서 텍스트와 tool call 정보 추출"""
    tool_calls = []
    text_parts = []
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            text_parts.append(data.get("response", data.get("output", raw)))
            for tc in data.get("tool_calls", data.get("toolUse", [])):
                tool_calls.append({
                    "tool": tc.get("name", tc.get("tool", "unknown")),
                    "input": json.dumps(tc.get("input", {}), ensure_ascii=False)[:80],
                    "output": tc.get("output", tc.get("result", ""))[:100],
                    "time": tc.get("duration", "0.3s"),
                })
    except (json.JSONDecodeError, TypeError):
        text_parts.append(str(raw))
    return {"text": "\n".join(text_parts) or raw, "tool_calls": tool_calls}
