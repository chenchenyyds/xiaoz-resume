"""虎皮椒支付 - V1 唯一支付渠道"""
import hashlib
import time
import uuid
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BizException, BizCode


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _sign(params: Dict[str, Any], key: str) -> str:
    """虎皮椒签名:按 key 排序后拼接 key=val...&key=密钥,做 MD5"""
    items = sorted([(k, str(v)) for k, v in params.items() if v is not None and v != ""])
    sign_str = "&".join([f"{k}={v}" for k, v in items]) + f"&key={key}"
    return _md5(sign_str).lower()


def _api_url() -> str:
    base = "https://api.hupijiao.com" if settings.HUPIIJIAO_SANDBOX else settings.HUPIIJIAO_API_URL
    return base


def create_order(
    order_no: str,
    product_name: str,
    amount: float,  # 元
    notify_url: Optional[str] = None,
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """创建虎皮椒支付订单,返回 {pay_url, trade_no, raw}"""
    if not settings.HUPIIJIAO_MERCHANT_ID or not settings.HUPIIJIAO_MERCHANT_KEY:
        raise BizException(BizCode.PAY_ERROR, "支付未配置")

    params = {
        "merchant": settings.HUPIIJIAO_MERCHANT_ID,
        "order_no": order_no,
        "product_name": product_name,
        "amount": f"{amount:.2f}",
        "notify_url": notify_url or settings.HUPIIJIAO_NOTIFY_URL,
        "return_url": return_url or settings.HUPIIJIAO_RETURN_URL,
        "timestamp": str(int(time.time())),
        "nonce_str": uuid.uuid4().hex,
    }
    params["sign"] = _sign(params, settings.HUPIIJIAO_MERCHANT_KEY)

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{_api_url()}/pay", data=params)
        data = resp.json()
        logger.info(f"虎皮椒下单: order_no={order_no} resp={data}")

        if data.get("code") != 200 or not data.get("data", {}).get("pay_url"):
            raise BizException(BizCode.PAY_ERROR, f"下单失败: {data.get('msg', '未知')}")
        return data["data"]
    except BizException:
        raise
    except Exception as e:
        logger.exception("虎皮椒下单异常")
        raise BizException(BizCode.PAY_ERROR, f"支付服务异常: {str(e)[:100]}")


def verify_notify(params: Dict[str, Any]) -> bool:
    """验证虎皮椒回调签名"""
    sign = params.pop("sign", "")
    expected = _sign(params, settings.HUPIIJIAO_MERCHANT_KEY)
    return sign.lower() == expected
