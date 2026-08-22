# SafeW 音乐搜索机器人

基于 SafeW API + go-music-api 的极简音乐搜索机器人。

## 功能
- 用户发送歌名，返回全网最多歌曲
- 每条歌曲是蓝色文本链接，点击跳转领取文件
- 顶部招商广告（蓝色字体链接）
- 底部内联按钮（广告商动态管理）

## 用户命令
- `/start` - 开始使用
- `/hlpl` - 使用帮助
- `/kefu` - 商务合作

## 管理员命令
- `/set_ad` - 修改顶部招商广告
- `/ad_add` - 添加广告商（名称|链接）
- `/ad_del` - 删除广告商（编号）
- `/ad_list` - 查看广告商列表
- `/ad_clear` - 清空所有广告商

## 部署步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 修改 `config.json` 填入你的 Token 和广告链接
3. 运行 `python main.py`

## 注意
`config.json` 和 `ad_config.json` 含敏感信息，已加入 `.gitignore`。
