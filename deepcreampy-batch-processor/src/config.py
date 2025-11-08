# API端点映射
API_ENDPOINTS = {
    0: "/deepcreampy-bar-rcnn",
    1: "/deepcreampy-mosaic-rcnn", 
    2: "/deepcreampy-mosaic-rcnn-esrgan",
    3: "/deepcreampy-bar",
    4: "/deepcreampy-mosaic"
}

# 模式描述
MODE_DESCRIPTIONS = {
    0: "修复一个带有色条的图片(自动识别涂抹)",
    1: "修复一个带有马赛克的图片(自动识别涂抹)",
    2: "修复一个带有马赛克的图片(自动识别涂抹并放大)",
    3: "修复一个带有色条的图片(已手动涂抹)",
    4: "修复一个带有马赛克的图片(已手动涂抹)"
}

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

# 默认配置
DEFAULT_CONFIG = {
    'base_url': 'http://localhost:8001',
    'mode': 2,
    'timeout': 120,
    'delay': 0.5
}