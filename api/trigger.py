# api/trigger.py
#
# 这个 Serverless Function 用于接收外部 POST 请求，
# 并通过 GitHub API 触发本仓库 (AIPEUSTracker) 的数据更新工作流。

import os
import requests
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理 POST 请求，触发 GitHub Actions 工作流。"""
        
        # --- 从 Vercel 环境变量中安全地获取配置 ---
        # 重要：请确保已在 Vercel 项目设置中配置了以下环境变量。
        token = os.environ.get('GITHUB_TOKEN')
        repo_owner = os.environ.get('GITHUB_REPO_OWNER') # 例如: 'digital-era'
        repo_name = os.environ.get('GITHUB_REPO_NAME')   # 例如: 'AIPEUSTracker'
        
        # 检查必要的环境变量是否存在，如果缺失则返回服务器错误
        if not all([token, repo_owner, repo_name]):
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "error": "Server configuration is incomplete. Required environment variables (GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME) are missing."
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        # --- 准备并调用 GitHub API ---
        
        # 你的工作流文件名，例如 main.yml, ci.yml 等。
        # 这个文件必须包含 `on: workflow_dispatch:` 才能被触发。
        workflow_file_name = "main.yml"  # 请根据你的实际文件名修改
        
        # 你希望在哪一个分支上运行这个工作流
        branch_to_run_on = "main"

        # 构造用于触发 workflow_dispatch 事件的 GitHub API URL
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_file_name}/dispatches"

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # 构造请求体 (payload)
        data = {
            "ref": branch_to_run_on,
            "inputs": {
                # 你可以传递自定义参数，方便在工作流中区分触发来源
                "trigger_source": "vercel_api_call" 
            }
        }
        
        try:
            # 向 GitHub API 发送 POST 请求
            res = requests.post(url, headers=headers, json=data)

            # 检查 GitHub API 的响应
            # 成功接收请求后，GitHub 会返回 204 No Content
            if res.status_code == 204:
                self.send_response(202) # 202 Accepted: 请求已被接受，正在异步处理
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "message": "Workflow triggered successfully.",
                    "details": f"Check the 'Actions' tab in your GitHub repository '{repo_owner}/{repo_name}' for progress."
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                # 如果 GitHub API 返回错误，则将错误信息透传给调用方
                self.send_response(res.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "error": "Failed to trigger GitHub workflow.",
                    "github_status_code": res.status_code,
                    "github_response": res.json()
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))

        except requests.exceptions.RequestException as e:
            # 处理网络请求本身的异常
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": f"An internal error occurred while contacting GitHub API: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        return

    def do_GET(self):
        """处理 GET 请求，返回提示信息，防止误用。"""
        self.send_response(405) # 405 Method Not Allowed
        self.send_header('Content-type', 'application/json')
        self.send_header('Allow', 'POST')
        self.end_headers()
        response = {
            "message": "This endpoint is for triggering a data refresh.",
            "error": "Method not allowed. Please use a POST request to trigger the workflow."
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return
