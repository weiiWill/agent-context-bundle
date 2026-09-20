# Local Scratchpad & Lightweight TODOs

> 本文件是极轻量随手记草稿纸，不纳入 `manifest.jsonl` 检索索引，不消耗上下文 Token。
> - 供开发者记录天级、分钟级零碎待办与临时灵感；
> - 供 Agent 在执行主线任务时记录发现的旁路次要问题（Out-of-Scope Items），严禁私自扩大改动范围，统一在此追加留痕。
>
> **条目归属规范**：`- [ ] [<scope>] <代码位置或模块>: <问题描述>`
> - `[global]`：全局工程级待办（与特定任务无关）；
> - `[task:<task-slug>]`：执行特定任务时顺带发现的旁路待办（便于任务结项时回溯核对）。

- [ ] [global] Makefile: 补充本地压测 docker-compose 启动命令
- [ ] [task:example-task] src/auth/jwt.go#L42: 顺手修复 CheckToken 边界异常未捕获
