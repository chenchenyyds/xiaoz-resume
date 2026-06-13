"""DeepSeek LLM 封装 - V1 直接调,不上 LangChain"""
import time
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BizException, BizCode


def _get_client() -> OpenAI:
    """OpenAI SDK 兼容 DeepSeek"""
    return OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_URL,
        timeout=settings.LLM_TIMEOUT_SECONDS if hasattr(settings, "LLM_TIMEOUT_SECONDS") else 60,
    )


def chat(
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """单次 LLM 调用,返回 {content, input_tokens, output_tokens, duration_ms}

    抛出 BizException(LLM_ERROR) - 上层统一处理
    """
    client = _get_client()
    start = time.time()
    try:
        kwargs = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": messages,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format

        resp = client.chat.completions.create(**kwargs)
        duration = int((time.time() - start) * 1000)

        content = resp.choices[0].message.content
        usage = resp.usage
        logger.info(
            f"LLM 调用完成: model={settings.DEEPSEEK_MODEL} "
            f"in={usage.prompt_tokens} out={usage.completion_tokens} "
            f"duration={duration}ms"
        )
        return {
            "content": content,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "duration_ms": duration,
            "model_name": settings.DEEPSEEK_MODEL,
        }
    except BizException:
        raise
    except Exception as e:
        logger.exception("LLM 调用失败")
        raise BizException(BizCode.LLM_ERROR, f"AI 服务异常: {str(e)[:200]}")


def chat_json(
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """要求 LLM 返回 JSON,自动解析;解析失败抛出 LLM_ERROR。"""
    result = chat(
        messages,
        temperature=temperature or 0.3,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    try:
        parsed = json.loads(result["content"])
    except json.JSONDecodeError as e:
        logger.error(f"LLM 返回非 JSON: {result['content'][:200]}")
        raise BizException(BizCode.LLM_ERROR, "AI 返回格式异常")
    result["parsed"] = parsed
    return result
