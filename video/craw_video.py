import base64
import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

def download_blob_video(page_url, output_path='videos'):
    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # 配置Chrome无头模式
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = ChromeService(executable_path="./chromedriver")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 访问目标网页
        driver.get(page_url)
        time.sleep(5)  # 等待页面加载完成

        # 查找所有video标签
        videos = driver.find_elements(By.TAG_NAME,'video')

        for i, video in enumerate(videos):
            # 获取video标签的src属性
            src = video.get_attribute('src')

            if src and src.startswith('blob:'):
                print(f"发现Blob视频: {src}")

                # 通过JavaScript获取视频数据
                script = """return arguments[0].currentSrc;"""

                video_url = driver.execute_script(script, video)
                response = requests.get(video_url, stream=True)
                with open('video.mp4', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"视频成功保存到: {output_path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    download_blob_video("", "videos")
