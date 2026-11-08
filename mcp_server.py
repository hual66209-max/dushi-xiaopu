"""MCP stdio entry; reads and writes the same save as web.py."""
from mcp.server.fastmcp import FastMCP
import game

mcp=FastMCP('赌石小铺')

@mcp.tool()
def jade_shop(text: str) -> str:
    """与玩家共用赌石小铺。text 输入“帮助”“打开”“去 垃圾铺”“买 1”“打灯”“切”“磨”“卖”“收藏”或破产时“领取800”。按游戏返回的提示继续操作。"""
    return game.tool_result(text)

if __name__=='__main__':
    mcp.run(transport='stdio')
