import requests, csv, os, json, glob
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def fetch_project(config):
    try:
        res = requests.get(config['url'], params=config['params'], timeout=30)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        offset = config.get('timezone_offset', 0)
        tz = timezone(timedelta(hours=offset))
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
        tz_label = f"UTC+{offset}" if offset >= 0 else f"UTC{offset}"
        
        rows = []
        for tr in soup.select('table tr'):
            cells = [td.get_text(strip=True) for td in tr.select('td,th')]
            if len(cells) == 4 and not cells[0].startswith('渠') and cells[0] not in ['合计', '']:
                rows.append([now, tz_label, config['name']] + cells)
        
        print(f"抓到 {len(rows)} 条数据")
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
    print(f"已保存到 {filepath}")

if __name__ == '__main__':
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
        else:
            print(f"⚠️ {config['name']} 没有数据")
