import requests, csv, os, json, glob, time
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def wait_for_half_hour():
    now = datetime.utcnow()
    minutes = now.minute
    seconds = now.second
    if minutes < 30:
        wait_seconds = (30 - minutes) * 60 - seconds
    else:
        wait_seconds = (60 - minutes) * 60 - seconds
    if wait_seconds > 10:
        print(f"⏳ 等待 {wait_seconds} 秒，将在下一个整点/半点开始")
        time.sleep(wait_seconds)

def fetch_project(config):
    try:
        res = requests.get(config['url'], params=config['params'], timeout=30)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 转换为项目时区时间
        offset = config.get('timezone_offset', 0)
        tz = timezone(timedelta(hours=offset))
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
        tz_label = f"UTC+{offset}" if offset >= 0 else f"UTC{offset}"
        
        rows = []
        for tr in soup.select('table tr'):
            cells = [td.get_text(strip=True) for td in tr.select('td,th')]
            if len(cells) == 4 and not cells[0].startswith('渠') and cells[0] not in ['合计', '']:
                rows.append([now, tz_label, config['name']] + cells)
        return rows
    except Exception as e:
        print(f"❌ {config['name']} 抓取失败: {e}")
        return []

def save(project_name, rows):
    os.makedirs('data', exist_ok=True)
    filepath = f"data/{project_name}.csv"
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['时间', '时区', '项目', '渠道', '访问', '注册', '首充'])
        writer.writerows(rows)

if __name__ == '__main__':
    wait_for_half_hour()
    
    configs = sorted(glob.glob('config/*.json'))
    if not configs:
        print("❌ 没有找到配置文件")
        exit(1)
    
    for config_file in configs:
        with open(config_file, encoding='utf-8') as f:
            config = json.load(f)
        print(f"正在抓取 {config['name']}...")
        rows = fetch_project(config)
        if rows:
            save(config['name'], rows)
            print(f"✅ {config['name']} 已保存 {len(rows)} 条")
