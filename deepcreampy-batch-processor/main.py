#!/usr/bin/env python3
"""
DeepCreamPy 批量图片处理工具 - 主入口文件
"""

import sys
import argparse
import logging
from src.processor import DeepCreamPyBatchProcessor
from src.config import MODE_DESCRIPTIONS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_mode_info():
    """打印模式信息"""
    print("可用处理模式:")
    for mode, description in MODE_DESCRIPTIONS.items():
        print(f"  {mode}: {description}")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="DeepCreamPy 批量图片处理工具")
    
    parser.add_argument(
        "-f", "--folder",
        required=True,
        help="输入文件夹路径，例如: C:\\BDown"
    )
    
    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8001",
        help="API服务器地址，例如: http://localhost:8001 (默认: http://localhost:8001)"
    )
    
    parser.add_argument(
        "-m", "--mode",
        type=int,
        choices=list(MODE_DESCRIPTIONS.keys()),
        default=2,
        help="处理模式: 0=色条自动识别, 1=马赛克自动识别, 2=马赛克自动识别并放大, 3=色条手动涂抹, 4=马赛克手动涂抹 (默认: 2)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="自定义输出文件夹路径 (默认: 自动在输入文件夹同级创建new_前缀文件夹)"
    )
    
    parser.add_argument(
        "-t", "--transparent",
        action="store_true",
        help="启用智能透明背景恢复功能，通过与原始图片对比精确恢复透明区域"
    )
    
    parser.add_argument(
        "-w", "--overwrite",
        action="store_true",
        help="覆盖已存在的输出文件（默认行为是跳过已存在的文件，实现断点续传）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 显示模式信息
    if args.mode not in MODE_DESCRIPTIONS:
        print("错误: 无效的模式选择")
        print_mode_info()
        sys.exit(1)
    
    # 创建处理器实例
    processor = DeepCreamPyBatchProcessor(
        base_url=args.url, 
        mode=args.mode, 
        transparent_bg=args.transparent,
        overwrite_existing=args.overwrite
    )
    
    try:
        # 测试API连接
        logger.info("测试API连接...")
        if processor.test_connection():
            logger.info("API连接正常")
        else:
            logger.warning("API可能未正常运行")
        
        # 处理文件夹
        result = processor.process_folder(args.folder, args.output)
        
        if result:
            logger.info(f"批量处理完成！成功率: {result['success']}/{result['total']}")
            if args.transparent:
                logger.info("智能透明背景恢复功能已应用于所有检测到透明背景的图片")
            if not args.overwrite:
                logger.info("断点续传模式: 已跳过已存在的文件")
            
            # 如果有失败的文件，在控制台额外显示
            if result['failed_files']:
                print("\n" + "="*60)
                print("处理失败的文件列表 (已复制原始文件到输出目录):")
                print("="*60)
                for i, failed_file in enumerate(result['failed_files'], 1):
                    print(f"  {i}. {failed_file}")
                print("="*60)
                print(f"总计 {len(result['failed_files'])} 个文件处理失败")
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 如果没有提供参数，显示帮助信息
    if len(sys.argv) == 1:
        print("DeepCreamPy 批量图片处理工具")
        print("使用方法: python main.py -f <文件夹路径> [选项]")
        print("\n示例:")
        print('  python main.py -f "C:\\BDown"')
        print('  python main.py -f "C:\\BDown" -u "http://localhost:8001" -m 2')
        print('  python main.py -f "C:\\BDown" -t  # 启用智能透明背景恢复')
        print('  python main.py -f "C:\\BDown" -w  # 覆盖已存在的文件')
        print("\n选项:")
        print("  -f, --folder  输入文件夹路径 (必需)")
        print("  -u, --url     API服务器地址 (默认: http://localhost:8001)")
        print("  -m, --mode    处理模式 0-4 (默认: 2)")
        print("  -o, --output  自定义输出文件夹路径")
        print("  -t, --transparent  启用智能透明背景恢复功能")
        print("  -w, --overwrite  覆盖已存在的输出文件（默认跳过，用于断点续传）")
        print("  -v, --verbose  启用详细日志输出")
        print_mode_info()
        sys.exit(1)
    
    main()