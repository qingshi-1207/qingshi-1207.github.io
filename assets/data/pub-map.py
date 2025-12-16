import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

# --- 配置部分 ---
DBLP_URL = "https://dblp.org/pid/50/6579.html" # 请替换为你的 DBLP PID URL
OUTPUT_FILE = "assets/data/auto-publications.json"
VENUE_MAP_FILE = "assets/data/venue_map.json"

class VenueMapper:
    def __init__(self, map_file):
        self.map_file = map_file
        self.mapping = {}
        self.load_mapping()
        self.modified = False

    def load_mapping(self):
        if os.path.exists(self.map_file):
            try:
                with open(self.map_file, 'r', encoding='utf-8') as f:
                    self.mapping = json.load(f)
            except:
                self.mapping = {}

    def save_mapping(self):
        if self.modified:
            with open(self.map_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, indent=4, ensure_ascii=False)
            print("Venue mapping updated and saved.")

    def get_full_name(self, venue_abbr, venue_url):
        # 如果没有 URL，直接返回缩写
        if not venue_url:
            return venue_abbr
        
        # 尝试将具体年份的 URL 转换为系列主页 URL (Series URL)
        # 例如: db/conf/cvpr/cvpr2022.html -> db/conf/cvpr/index.html
        # 这样能获得更通用的全称
        try:
            base_path = venue_url.rsplit('/', 1)[0]
            series_url = f"{base_path}/index.html"
        except:
            series_url = venue_url

        # 检查缓存
        if series_url in self.mapping:
            return self.mapping[series_url]

        # 如果缓存没有，去爬取
        print(f"Fetching full name for: {venue_abbr} ({series_url})")
        full_name = self.fetch_remote_title(series_url)
        
        # 如果获取失败，回退到使用缩写，但也存入缓存避免重复请求
        final_name = full_name if full_name else venue_abbr
        
        self.mapping[series_url] = final_name
        self.modified = True
        
        # 礼貌性延时，防止触发 DBLP 频率限制
        time.sleep(1) 
        
        return final_name

    def fetch_remote_title(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                # DBLP Series 页面的全称通常在 <header> 下的 <h1> 中
                # 或者直接取网页 <title> 并清洗
                h1 = soup.find('h1')
                if h1:
                    text = h1.get_text()
                    return text.strip()
                
                # 备选：从 title 标签取 (格式通常是 "Full Name (Abbr) - dblp")
                title_tag = soup.title.string
                if title_tag:
                    clean_name = title_tag.replace(" - dblp", "").strip()
                    # 尝试去掉括号里的缩写，例如 "Computer Vision (ICCV)" -> "Computer Vision"
                    # 可选：如果你喜欢保留括号，可以注释掉下面这行
                    # clean_name = re.sub(r'\s*\(.*?\)$', '', clean_name)
                    return clean_name
        except Exception as e:
            print(f"Failed to fetch venue info: {e}")
        return None

def fetch_and_save():
    mapper = VenueMapper(VENUE_MAP_FILE)
    
    print(f"Fetching publication list from {DBLP_URL}...")
    try:
        response = requests.get(DBLP_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers_data = []
        entries = soup.find_all('li', class_='entry')
        
        for entry in entries:
            # # ... (其他字段提取逻辑与之前相同) ...
            # paper_id = entry['id']
            # title = entry.find('span', class_='title').get_text().strip(" .")
            # authors = [a.get_text() for a in entry.find_all('span', itemprop='author')]
            # year = entry.find('span', itemprop='datePublished').get_text().strip()
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
            
            # # 4. 提取会议/期刊名称
            # venue_span = entry.find('span', itemprop='isPartOf')
            # venue = venue_span.get_text().strip() if venue_span else ""
            
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


            # --- 关键修改部分 ---
            # 提取 Venue 缩写
            venue_span = entry.find('span', itemprop='isPartOf')
            venue_abbr = venue_span.get_text().strip() if venue_span else ""
            
            # 提取 Venue URL (用于查找全称)
            venue_url = None
            venue_link_tag = venue_span.find_parent('a') if venue_span else None
            # 有时候 link 不直接包在 span 外面，而是在 href 里
            if not venue_link_tag:
                # 尝试查找 db/conf/... 的链接
                for a in entry.find_all('a'):
                    href = a.get('href', '')
                    if 'db/conf/' in href or 'db/journals/' in href:
                        venue_url = href
                        break
            else:
                venue_url = venue_link_tag['href']

            # 获取全称！
            full_venue_name = mapper.get_full_name(venue_abbr, venue_url)

            # 构造数据
            papers_data.append({
                "id": paper_id,
                "title": title,
                "authors": authors,
                "venue": full_venue_name, # 这里存入全称
                "venue_abbr": venue_abbr, # 保留缩写以备不时之需
                "year": year,
                "link": link,
                "type": entry_type
            })

        # 保存结果
        output = {
            "last_updated": time.strftime("%Y-%m-%d"),
            "publications": papers_data
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
            
        # 保存映射表 (很重要！)
        mapper.save_mapping()
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_save()