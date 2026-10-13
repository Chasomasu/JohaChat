"""
图片工具函数
提供图片格式转换等实用功能
适配 RqhBot SDK 的消息段格式
"""


def image_to_data_url(seg_data: dict) -> str:
    """
    将 SDK 消息段中的图片数据转换为 base64 data URL（供多模态模型使用）
    
    Args:
        seg_data: SDK 消息段 data 字段，如 {"file": "...", "file_base64": "base64://...", "url": "..."}
        
    Returns:
        base64 data URL 字符串，失败返回空字符串
    """
    try:
        # 优先使用 file_base64（内嵌 base64）
        raw = seg_data.get("file_base64", "")
        if raw and raw.startswith("base64://"):
            return "data:image/jpeg;base64," + raw[len("base64://"):]
        # 其次使用 url（可公开访问的 URL）
        url = seg_data.get("url", "")
        if url:
            return url
        return ""
    except Exception:
        return ""


def extract_images_from_sdk_event(event) -> list:
    """
    从 SDK 群消息事件中提取并转换所有图片
    
    Args:
        event: SDK GroupMessageEvent 对象
        
    Returns:
        转换后的图片 URL 列表（过滤掉失败的）
    """
    image_urls = []
    for seg in event.message.segments:
        if seg.get("type") == "image":
            seg_data = seg.get("data", {})
            url = image_to_data_url(seg_data)
            if url:
                image_urls.append(url)
    return image_urls
