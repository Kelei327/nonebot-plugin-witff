

<div align="center">

# nonebot-plugin-witff
When Is The FurryFusion? | 兽聚是什么时候? | 兽聚时间查询插件

<a href="https://github.com/TheChenXI/nonebot-plugin-witff/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Ekac00/nonebot-plugin-furryfusion.svg" alt="license">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

<a href="https://pypi.python.org/pypi/nonebot-plugin-furryfusion">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-furryfusion.svg" alt="pypi">
</a>

</div>

### <del>第一次使用Github/Pypi，如果有错误,还请谅解,请多多包容,非常感谢</del>

***

# 前文

### 感谢 <a href="https://github.com/Ekac00/nonebot-plugin-furryfusion/">✨ 兽聚动态 ✨</a>的启发

### 感谢 <a href="https://console-docs.apipost.cn/preview/fcba96ab381efa80/fdb51b00b68a9bbf?target_id=3a8b741e-9648-4469-8f47-98484378fdcf">兽云祭</a>所提供的API


***

# 安装 & 使用

### [推荐] 使用nb命令安装

`nb plugin install nonebot_plugin_witff`

### Pip安装

 `pip install nonebot-plugin-witff`

### 手动安装

找到机器人的项目的插件目录下, 上传项目zip/tar.gz并解压
找到项目根目录下的 `pyproject.toml` 文件, 在Plugins部分追加写入
plugins = ["nonebot_plugin_witff"]


## 支持的命令
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| /兽聚 | 无 | 否 | 群聊/私聊 | 查询兽聚  |
| /兽聚 {Page} | 无 | 否 | 群聊/私聊 | 通过页面查询兽聚  |
| /兽聚 搜索 {Keyword}| 群员 | 否 | 群聊/私聊 | 关键词查询  <del>多个关键词查询似乎有BUG</del> |
| /兽聚 图片发送 | 无 | 否 | 群聊/私聊 | 切换发送模式为"图片发送"  |
| /兽聚 文字发送 | 无 | 否 | 群聊/私聊 | 切换发送模式为"文字发送"  |
| /兽聚 帮助 | 无 | 否 | 群聊/私聊 | 获取插件帮助  |


<img width="1800" height="990" alt="cc825e6da5476affe136c7153c733367" src="https://github.com/user-attachments/assets/84a61bec-60db-45c6-9e22-32812f9487dd" />



***

# 功能
 - [x] 分条发送
 - [x] 文字转图片发送
 - [ ] 兽聚详细信息


