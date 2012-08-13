@author : chenchiyuan
@email : chenchiyuan03@gmail.com
@company: tukeq.com
需求： 将单机负荷重的同步任务，例如训练和爬虫能够迅速的分发到其他机器，实现分布式。 主要利用了gearman的任务分发机制。

设计： 将任务抽象。通过回调完成任务。 Task模型（任务的handle)：

map: 将数据分发，规定。数据比较符合以下形式[dict, dict]。#数据采用json传递
callback: worker回调，由于gearman queue的数据只能采用str传递。自带的encode的函数不灵活。 因而callback主要处理数据的格式转换。从queue中取出消息，将起转化为json，交由on_callback处理， 最后将数据转化为string,丢回reactor循环。
on_callback: dict数据处理，主要的业务逻辑。需要定制。
sync_run: 同步运行代码。
reduce: 将计算结果汇总，研究机制中。

Manager模型(任务的管理者)： clear_workers(task_name): 清理workers get_admin(): 取得admin实例，可以于服务器打交到，得到他的一些数据，能清理task中的queue/ get_worker(): 可以取得一个workder手动测试代码 get_client(): 得到一个gearman客户端，可以分发任务。

注意事项：

业务逻辑(on_callback)中，最好不要有阻塞式的操作。比如time.sleep(1).gearman采用twisted实现 异步模型，在reactor中不能忍受阻塞操作。
任务建立之后，必须使用测试script来测试脚本。（还没写清理函数，如有记录之类的操作，数据将被记录） 测试成功后，manager的tested属性激活，才能分发。

待处理的问题:
1. gearman worker干净退出。
2. scrapy等内部依赖问题。如何得到django环境，从settings中读数据。
3. template如何写得更方便。
4. 任务成功回调的研究。