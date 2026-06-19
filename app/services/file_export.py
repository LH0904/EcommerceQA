"""
文件导出服务 - HTML/PDF 生成与文件管理
"""
import os
import time
import logging

from playwright.async_api import async_playwright

from app.config import settings

logger = logging.getLogger(__name__)

# Chrome 路径（Windows）
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def get_output_dir() -> str:
    """获取输出目录的绝对路径，确保目录存在"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, settings.OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def save_html(content: str, prefix: str = "board") -> str:
    """
    保存 HTML 文件到输出目录
    返回文件绝对路径
    """
    output_dir = get_output_dir()
    timestamp = int(time.time() * 1000)
    html_path = os.path.join(output_dir, f"{prefix}_{timestamp}.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"HTML 已保存: {html_path}")
    return html_path


async def generate_pdf(html_path: str) -> str | None:
    """
    使用 Playwright 将 HTML 转换为 PDF
    返回 PDF 文件路径，失败返回 None
    """
    pdf_path = html_path.replace(".html", ".pdf")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
            )
            page = await browser.new_page()
            await page.goto(f"file:///{os.path.abspath(html_path)}")
            await page.wait_for_timeout(3000)
            await page.pdf(path=pdf_path, format="A4")
            await browser.close()
            logger.info(f"PDF 已生成: {pdf_path}")
            return pdf_path
    except Exception as e:
        logger.error(f"PDF 生成失败: {e}")
        return None


def file_exists(path: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(path)


def get_filename(path: str) -> str:
    """获取文件名"""
    return os.path.basename(path)
