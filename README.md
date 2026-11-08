# 赌石小铺：网页与 AI 共用存档

网页上看石、打灯、买石和切石；支持 MCP 的 AI 助手可以用 `jade_shop` 工具操作同一份存档。初始本金 ¥10,000，五档铺子、NPC、三种切法和珍藏柜沿用小铺玩法。

本分享版没有商城积分兑换。买不起所有已解锁货架上的石头、手里也没有待切石头时，网页可以点击「领 ¥800 重新开始」，AI 可以调用 `jade_shop(text="领取800")`。所有货架为空时，本金低于 ¥200 才可领取。领取不计入切石花费和盈亏。

## 本机运行

当前版本面向 Linux / macOS，需要 Python 3.11 及以上、Node.js（`node` 在 PATH 中）、支持 WebGL 的浏览器。Windows 目前未适配。网页和 AI 工具必须运行在**能访问同一份存档文件的同一台机器上**。

在本目录执行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python web.py
```

打开 `http://127.0.0.1:8088/`。也可运行 `.venv/bin/python web.py 8089` 指定本地端口。首次使用会自动建立新档；网页和 AI 工具的默认存档都在本项目 `data/save.json`。不要把 `data/` 上传或发给别人。

`web.py` 仅监听本机，没有远程登录与多用户隔离；不要直接把它开放到互联网。网页和 AI 各自修改了存档时，旧网页会提示重新打开，以防覆盖对方的操作。

## 接入支持 MCP 的 AI 客户端

把项目目录中的虚拟环境 Python 和 MCP 脚本加入客户端的 MCP 服务器配置，以下仅是路径示例，请改成自己的绝对路径：

```json
{
  "mcpServers": {
    "jade-shop": {
      "command": "/path/to/jade-shop-share/.venv/bin/python",
      "args": ["/path/to/jade-shop-share/mcp_server.py"]
    }
  }
}
```

客户端连接后可调用 `jade_shop(text="帮助")` 查看完整命令，例如 `打开`、`去 垃圾铺`、`打灯`、`买 1`、`切`、`磨`、`卖` 和 `领取800`。需要确保客户端启动 MCP 子进程时的 `PATH` 能找到 Node.js。

如需把存档放到其他位置，可在启动网页和 MCP 服务时都设置相同的 `JADE_DATA_DIR` 环境变量。不同值会形成不同存档；环境变量应指向绝对目录。

## 许可与状态

保留原项目的 [PolyForm Noncommercial 1.0.0](LICENSE)：允许的范围是非商业用途，并非 OSI 定义的开源许可证。网页内嵌的 Three.js 许可见 [第三方说明](THIRD_PARTY_NOTICES.md)。正式对外发布前请原作者确认署名和分享范围。
