"""
GitHub Explorer - 阶段②：Flask 后端
提供 API 接口 + 渲染前端页面
"""
from flask import Flask, jsonify, render_template
import json
import os

app = Flask(__name__)

# ==================== 加载数据 ====================
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "repos.json")

def load_data():
    """加载爬虫获取的 JSON 数据"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== 路由 ====================

@app.route("/")
def index():
    """首页：渲染 HTML 模板"""
    return render_template("index.html")


@app.route("/api/repos")
def api_repos():
    """API：返回所有项目数据（JSON）"""
    repos = load_data()
    return jsonify(repos)


@app.route("/api/stats")
def api_stats():
    """API：返回聚合统计数据"""
    repos = load_data()

    # Top 20 项目（用于排行榜）
    top20 = sorted(repos, key=lambda r: r["stars"], reverse=True)[:20]

    # 项目类型分类（根据 topics 关键字）
    categories = {
        "AI/ML": 0, "Web框架": 0, "工具/脚本": 0,
        "学习资源": 0, "爬虫/数据": 0, "DevOps": 0, "其他": 0
    }
    for r in repos:
        desc = (r["description"] + " " + " ".join(r["topics"])).lower()
        if any(k in desc for k in ["machine learning", "deep learning", "ai", "neural", "nlp", "llm", "gpt"]):
            categories["AI/ML"] += 1
        elif any(k in desc for k in ["web", "framework", "flask", "django", "api", "fastapi"]):
            categories["Web框架"] += 1
        elif any(k in desc for k in ["tool", "cli", "utility", "automation", "script"]):
            categories["工具/脚本"] += 1
        elif any(k in desc for k in ["learn", "tutorial", "awesome", "book", "course", "guide", "interview"]):
            categories["学习资源"] += 1
        elif any(k in desc for k in ["scrap", "crawl", "data", "spider", "visualization"]):
            categories["爬虫/数据"] += 1
        elif any(k in desc for k in ["docker", "kubernetes", "deploy", "ci", "devops"]):
            categories["DevOps"] += 1
        else:
            categories["其他"] += 1

    # Stars vs Issues 数据（散点图）
    scatter = [{"name": r["name"], "stars": r["stars"], "issues": r["open_issues"]}
               for r in repos]

    # 年份趋势（按创建年份统计项目数）
    year_count = {}
    for r in repos:
        year = r["created_at"][:4]
        year_count[year] = year_count.get(year, 0) + 1
    years = sorted(year_count.keys())
    year_data = [{"year": y, "count": year_count[y]} for y in years]

    # 许可证分布
    license_count = {}
    for r in repos:
        lic = r.get("license", "None")
        license_count[lic] = license_count.get(lic, 0) + 1
    license_data = [{"name": k, "value": v} for k, v in
                    sorted(license_count.items(), key=lambda x: -x[1])[:8]]

    return jsonify({
        "top20": top20,
        "categories": categories,
        "scatter": scatter,
        "yearTrend": year_data,
        "licenses": license_data,
        "totalStars": sum(r["stars"] for r in repos),
        "totalRepos": len(repos),
    })


# ==================== 启动 ====================
if __name__ == "__main__":
    print("🌐 GitHub Explorer 启动！访问 http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
