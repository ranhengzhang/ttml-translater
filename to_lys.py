import os
from typing import Match
from xml.dom.minidom import parseString, Document

from loguru import logger
import requests
import re

from github import Github
from github.Issue import Issue
from github.Repository import Repository
from requests import Response
from ttml.ttml import TTML


def process_content(content: str) -> tuple[str, str|None]:
    """示例目标处理函数"""
    dom: Document = parseString(content)
    ttml: TTML = TTML(dom)
    # 在这里添加您的自定义处理逻辑
    comment: str = ''
    orig, ts = ttml.to_lys()
    logger.info(f"orig: \n{orig}")
    comment += f'### ORIG\n\n```\n{orig}\n```\n\n'
    if ts:
        logger.info(f"ts: \n{ts}")
        comment += f'### TS\n\n```\n{ts}\n```\n\n'

    return comment, ttml.get_full_title()


if __name__ == '__main__':
    """处理GitHub Issue"""
    issue: Issue|None = None
    try:
        # 获取环境变量
        github_token: str = os.environ['GITHUB_TOKEN']
        repo_name: str = os.environ['GITHUB_REPOSITORY']
        issue_number: str = os.environ['ISSUE_NUMBER']

        # 初始化GitHub客户端
        g: Github = Github(github_token)
        repo: Repository = g.get_repo(repo_name)
        issue = repo.get_issue(int(issue_number))

        # 获取Issue内容
        issue_body: str = issue.body

        # 提取URL
        url_pattern: str = r"https?://[^\s]+"
        url_match: Match[str] = re.search(url_pattern, issue_body)

        if not url_match:
            logger.error('未找到有效 URL')
            exit(0)

        file_url: str = url_match.group(0)
        file_response: Response = requests.get(file_url)
        file_response.raise_for_status()
        file_content: str = file_response.text

        comment, title = process_content(file_content)
        issue.create_comment(comment)
        if title is not None:
            issue.edit(title=f'[LYS] {title}')

    except Exception as e:
        logger.exception(e)
        if 'issue' in locals():
            issue.create_comment(str(e))

    finally:
        issue.edit(state='closed')