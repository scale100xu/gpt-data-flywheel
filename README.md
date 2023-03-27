# gpt-data-flywheel

这是用gpt api生成无限数据的数据飞轮工具，用它可以无限的生成你的数据，
总体的工作原理为 【种子prompt】生成 答案 ，然后对 答案 用 prompting提示 生成 问题，然后 解析问题 再生成 答案；
问题到答案，答案到问题，无限循环，生成无限数据。
但是要注意你的tokens数量是有限的，钱是有限的

# 工作原理如下图

![image](gpt-data-flywheel-working-principle.png)


# 使用

### 1. 配置config.yaml

```yaml
api-urls: # api urls
  - https://api.openai.com/v1/chat/completions
openai-tokens: # openai tokens
  - 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
proxys: # proxy address
  -  # example as socks5://127.0.0.1:7890
thread-count: 5 # thread count
retry-count: 3 # request failure, try again count
save-file: ./flywheel.md # save data file name
seed-prompts-type: 0 # 0 is question as seed; 1 is answer as seed;
seed-prompts: # seed prompts
  - Java语言的设计哲学
  - Java语言的常用库或框架，有哪些，各个的实现原理是什么
  - 正则表达式的算法核心是什么
  - 正则表达式的语法规则是什么
  - 正则表达式可以做什么
output-prompting-answer: 0 # 0 is not output prompting; 1 is output prompting;
prompting-answers: # guide to ask questions
  - 对下面的内容提出一些问题:\n\n
  - 对下面的内容步步深入的提出一些问题:\n\n

```

### 2. 安装和运行 gpt-data-flywheel，生成数据
```shell
git clone https://github.com/scale100xu/gpt-data-flywheel
cd gpt-data-flywheel
pip install -r requirements.txt
python gpt-data-flywheel.py --config=./config.yaml
```


### 3. 查看结果数据，例子中的结果文件为flywheel.md

### 关闭此程序

#### 方法 1. Ctrl + C
#### 方法 2. kill -15 进程ID
#### 方法 3. kill -9 进程ID

### 说明

openai tokens 是测试账号，随时都有可能不能用，请用你自己的API token测试！

### 后续

虽说这是用gpt模型生成数据的工具，后续可以添加其它的模型，作为生成数据的底座！！！
欢迎提出你的想法或善意的建议！！！

### telegram testing group
https://t.me/+BalrnUYBE4o3NTI1

### discord testing group
https://discord.gg/EknWWntCRE
