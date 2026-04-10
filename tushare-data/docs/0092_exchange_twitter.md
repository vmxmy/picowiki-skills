交易所Twitter数据
------

接口：exchange_twitter

描述：获取Twitter上数字货币交易所发布的消息（5分钟更新一次，未来根据服务器压力再做调整）

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
start_date | datetime | Y | 开始时间 格式：YYYY-MM-DD HH:MM:SS
end_date | datetime | Y | 结束时间 格式：YYYY-MM-DD HH:MM:SS

**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
id | int | 记录ID（采集站点中的）
account_id | int | 交易所账号ID（采集站点中的）
account | str | 交易所账号
nickname | str | 交易所昵称
avatar | str | 头像
content_id | int | 类容ID（采集站点中的）
content | str | 原始内容
is_retweet | int | 是否转发：0-否；1-是
retweet_content | json | 转发内容，json格式，包含了另一个Twitter结构
media | json | 附件，json格式，包含了资源类型、资源链接等
posted_at | int | 发布时间戳
content_translation | str | 内容翻译
str_posted_at | str | 发布时间，根据posted_at转换而来
create_at | str | 采集时间

注：内容中包含HTML标签怎么办？

答：请见[PYTHON过滤HTML标签](https://tushare.pro/document/1?doc_id=91)

**接口用法**

由于数据量可能比较大，我们限定了必须设定起止时间来获取数据，并且每次最多只能取200条数据。

```python
pro = ts.pro_api()

pro.exchange_twitter(start_date='2018-09-02 03:20:03', end_date='2018-09-02 03:35:03', fields="id,account,nickname,content,retweet_content,media,str_posted_at,create_at")
```

或者

```python
pro.query('exchange_twitter', start_date='2018-09-02 03:20:03', end_date='2018-09-02 03:35:03', fields="id,account,nickname,content,retweet_content,media,str_posted_at,create_at")
```

**数据样例**

id | account | nickname | content | retweet_content | media | str_posted_at | create_at
--- | --- | --- | --- | --- | --- | --- | ---
1067775 | OpenLedgerDC | OpenLedger ApS | RT @OpenLedgerDC: Meet #OpenLedger at #CoinsBa... | {'account': 'OpenLedgerDC', 'nickname': 'OpenL... | \[] | 2018-09-02 03:11:20 | 2018-09-02 03:35:03
1067758 | QuoineGlobal | QUOINE | Liquidity is vital for crypto to flourish.\nWe... | None | \[{'type': 'image', 'thumbnail': 'https://cdn.m... | 2018-09-02 03:08:03 | 2018-09-02 03:20:03
1067757 | CoinsBank | CoinsBank | @Crypto_poet_ Did you try? | None | \[] | 2018-09-02 02:51:05 | 2018-09-02 03:20:03