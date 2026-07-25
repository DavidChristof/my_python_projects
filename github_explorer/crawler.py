"""
GitHub Explorer - 阶段①：数据爬虫
调用 GitHub REST API，获取 Top 100 Python 热门项目
"""
import requests
import json
import time
import os

# ==================== 配置 ====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "repos.json")

# GitHub API 搜索端点（无需认证，每小时 60 次）
API_URL = "https://api.github.com/search/repositories"
HEADERS = {
    "User-Agent": "GitHub-Explorer-Learning-Project",
    "Accept": "application/vnd.github.v3+json",
}


def fetch_trending_python(language="python", sort="stars", per_page=100):
    """
    从 GitHub API 获取热门项目列表
    
    返回示例：
    {
        "name": "public-apis",
        "stars": 280000,
        "forks": 31000,
        "language": "Python",
        "description": "A collective list of free APIs",
        "url": "https://github.com/public-apis/public-apis",
        "created_at": "2016-03-21",
        "topics": ["api", "list", "free"],
        "open_issues": 150,
        "watchers": 280000
    }
    """
    all_repos = []
    pages_needed = (per_page + 99) // 100  # 向上取整，每页最多100条

    for page in range(1, pages_needed + 1):
        params = {
            "q": f"language:{language}",
            "sort": sort,
            "order": "desc",
            "per_page": min(100, per_page),
            "page": page,
        }

        print(f"📡 正在请求第 {page} 页...")
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)

        if resp.status_code == 403:
            print("⚠️  API 限流！等待 30 秒后重试...")
            time.sleep(30)
            resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)

        if resp.status_code != 200:
            print(f"❌ 请求失败: {resp.status_code} - {resp.text[:200]}")
            break

        data = resp.json()
        items = data.get("items", [])

        for item in items:
            repo = {
                "name": item["full_name"],
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "language": item.get("language", "N/A"),
                "description": (item.get("description") or "")[:200],
                "url": item["html_url"],
                "created_at": item["created_at"][:10],  # 只取日期
                "updated_at": item["updated_at"][:10],
                "topics": item.get("topics", []),
                "open_issues": item["open_issues_count"],
                "license": (item.get("license") or {}).get("spdx_id", "None"),
            }
            all_repos.append(repo)

        print(f"   ✓ 已获取 {len(all_repos)} 条")

        # 遵守 API 规范：请求间留间隔
        if page < pages_needed:
            time.sleep(2)

    return all_repos[:per_page]


def save_data(repos):
    """保存为 JSON 文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存到 {OUTPUT_FILE} ({len(repos)} 条)")


def print_summary(repos):
    """打印数据概览"""
    print("\n" + "=" * 50)
    print("📊 数据概览")
    print("=" * 50)
    print(f"  总项目数: {len(repos)}")
    print(f"  总 Stars: {sum(r['stars'] for r in repos):,}")
    print(f"  平均 Stars: {sum(r['stars'] for r in repos) // len(repos):,}")
    print(f"  最早项目: {min(r['created_at'] for r in repos)}")
    print(f"  最新项目: {max(r['created_at'] for r in repos)}")
    print()
    print("🏆 Top 5 热门项目:")
    for i, r in enumerate(repos[:5], 1):
        print(f"  {i}. {r['name']} — ⭐ {r['stars']:,}")


if __name__ == "__main__":
    print("🚀 开始爬取 GitHub Python 热门项目...")
    print(f"   目标: Top 100 (按 Stars 排序)\n")

    repos = fetch_trending_python(per_page=100)
    save_data(repos)
    print_summary(repos)
