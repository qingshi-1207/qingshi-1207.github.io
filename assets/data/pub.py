'''
Description: 
Author: Qing Shi
Date: 2025-12-16 22:52:24
LastEditors: Qing Shi
LastEditTime: 2025-12-16 23:21:21
'''
import requests
from bs4 import BeautifulSoup
import json
import datetime

# --- 配置部分 ---
DBLP_URL = "https://dblp.org/pid/50/6579.html" # 请替换为你的 DBLP PID URL
OUTPUT_FILE = "assets/data/auto-pub-list.json"

def fetch_dblp_data(url):
    print(f"Fetching data from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers_data = []
        
        # 获取所有条目
        entries = soup.find_all('li', class_='entry')
        
        for entry in entries:
            # print(entry)
            # 1. 提取 ID (用于去重或做 key)
            paper_id = entry['id']
            
            # 2. 提取标题
            title_span = entry.find('span', class_='title')
            title = title_span.get_text().strip() if title_span else "Unknown Title"
            # 去掉标题最后的点号（如果需要）
            if title.endswith('.'):
                title = title[:-1]

            # 3. 提取作者 (存为列表)
            authors = [a.get_text() for a in entry.find_all('span', itemprop='author')]
            
            # 4. 提取会议/期刊名称
            venue_span = entry.find('span', itemprop='isPartOf')
            venue = venue_span.get_text().strip() if venue_span else ""
            
            # 5. 提取年份
            year_span = entry.find('span', itemprop='datePublished')
            year = year_span.get_text().strip() if year_span else ""
            
            # 6. 提取链接 (DOI 优先，没有则取 DBLP 页)
            link = ""
            link_tag = entry.find('nav', class_='publ').find('li', class_='drop-down').find('div', class_='head').find('a')
            if link_tag:
                link = link_tag['href']

            # 7. 提取类型 (Conference, Journal, ArXiv 等)
            # DBLP 的 class 通常包含 'article', 'inproceedings' 等
            entry_type = "unknown"
            if "article" in entry.get("class", []):
                entry_type = "Journal"
            elif "inproceedings" in entry.get("class", []):
                entry_type = "Conference"
            elif "informal" in entry.get("class", []):
                entry_type = "Preprint/Workshop"

            # 构造字典对象
            paper_obj = {
                "id": paper_id,
                "title": title,
                "authors": authors,
                "venue": venue,
                "year": year,
                "link": link,
                "type": entry_type
            }
            papers_data.append(paper_obj)
            
        return papers_data

    except Exception as e:
        print(f"Error fetching DBLP: {e}")
        return []

def save_to_json(data):
    if not data:
        print("No data found, skipping save.")
        return

    # 包装一下，加个元数据（更新时间）
    output_data = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(data),
        "publications": data
    }

    try:
        # ensure_ascii=False 保证中文名（如果有）不会变成 \uXXXX 乱码
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(data)} items to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    data = fetch_dblp_data(DBLP_URL)
    save_to_json(data)